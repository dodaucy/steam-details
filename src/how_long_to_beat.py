import logging
from typing import Iterator, Union

from bs4 import BeautifulSoup
from httpx import Response

from steam import SteamDetails
from utils import http_client


_last_url: Union[str, None] = None


async def _get_game_length(url: str, steam: SteamDetails) -> Response:
    r = await http_client.post(
        url,
        headers={
            "Origin": "https://howlongtobeat.com",
            "Priority": "u=4",
            "Referer": "https://howlongtobeat.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1"
        },
        json={
            "searchType": "games",
            "searchTerms": [steam.name],
            "searchPage": 1,
            "size": 10,
            "searchOptions": {
                "games": {
                    "userId": 0,
                    "platform": "PC",
                    "sortCategory": "name",
                    "rangeCategory": "main",
                    "rangeTime": {"min": None, "max": None},
                    "gameplay": {"perspective": "", "flow": "", "genre": ""},
                    "rangeYear": {"min": "", "max": ""},
                    "modifier": ""
                },
                "users": {"sortCategory": "postcount"},
                "lists": {"sortCategory": "follows"},
                "filter": "",
                "sort": 0,
                "randomizer": 0
            },
            "useCache": True
        }
    )

    logging.info(f"Response (100 chars): {repr(r.text[:100])}")
    logging.debug(f"Response: (all): {r.text}")

    return r


def _get_fetch_urls(java_script: str) -> Iterator[str]:
    """
    Extract all fetch urls from the java script
    """
    for fetch_split in java_script.split("fetch(")[1:]:
        depth = 1
        char_counter = 0
        for char in fetch_split:
            char_counter += 1

            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1

            if depth == 0 or (depth == 1 and char == ","):  # Outside of fetch or end of first argument
                raw_url = fetch_split[:char_counter - 1]
                logging.debug(f"Found raw fetch url: {repr(raw_url)}")

                splitted_url = raw_url.split('"')
                logging.debug(f"Splitted fetch url: {repr(splitted_url)}")
                real_url: Union[str, None] = None

                if len(splitted_url) == 3 and splitted_url[0] == "" and splitted_url[2] == "":  # "..."
                    real_url = splitted_url[1]
                elif len(splitted_url) == 5 and splitted_url[0] == "" and splitted_url[2] == ".concat(" and splitted_url[4] == ")":  # "...".concat("...")
                    real_url = splitted_url = splitted_url[1] + splitted_url[3]

                if real_url is None:
                    logging.debug(f"Could not parse fetch url: {repr(raw_url)}")
                else:
                    logging.debug(f"Parsed fetch url: {repr(real_url)}")
                    yield real_url

                break


async def get_game_length(steam: SteamDetails) -> Union[dict, None]:
    global _last_url
    logging.info(f"Getting how long to beat for {repr(steam.name)} ({steam.appid})")

    r: Union[Response, None] = None
    if _last_url is None:
        logging.info("No old howlongtobeat API URL was found")
    else:
        response = await _get_game_length(_last_url, steam)
        if response.status_code == 404:
            logging.info(f"The old howlongtobeat API URL ({repr(_last_url)}) is not available")
        else:
            r = response

    if r is None:
        logging.info("Try fetching new howlongtobeat API URL")

        index_response = await http_client.get(
            "https://howlongtobeat.com/",
            headers={
                "Priority": "u=0, i",
                "Referer": "https://duckduckgo.com/",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "cross-site",
                "Sec-GPC": "1"
            }
        )
        logging.info(f"Response (100 chars): {repr(index_response.text[:100])}")
        logging.debug(f"Response: (all): {index_response.text}")
        index_response.raise_for_status()

        soup = BeautifulSoup(index_response.text, "html.parser")
        for script_tag in soup.find_all("script"):
            if script_tag.has_attr("src"):
                src: str = script_tag["src"]
                if src.startswith("/_next/static/chunks/pages/_app-") and src.endswith(".js"):
                    js_url = "https://howlongtobeat.com" + src
                    logging.debug(f"Found howlongtobeat JS URL: {repr(js_url)}")

                    js_response = await http_client.get(
                        js_url,
                        headers={
                            "Referer": "https://howlongtobeat.com/",
                            "Sec-Fetch-Dest": "script",
                            "Sec-Fetch-Mode": "no-cors",
                            "Sec-Fetch-Site": "same-origin",
                            "Sec-GPC": "1"
                        }
                    )
                    logging.info(f"Response (100 chars): {repr(js_response.text[:100])}")
                    logging.debug(f"Response: (all): {js_response.text}")
                    js_response.raise_for_status()

                    for url in _get_fetch_urls(js_response.text):
                        if url.startswith("/api/search") or url.startswith("/api/find"):
                            url = "https://howlongtobeat.com" + url
                            logging.info(f"Found howlongtobeat API URL: {repr(url)}")
                            _last_url = url
                            r = await _get_game_length(url, steam)
                            break
                    if r is not None:
                        break

                else:
                    logging.debug(f"Skipping {repr(script_tag['src'])}")

    if r is None:
        logging.warning("No howlongtobeat API URL found")
    else:
        r.raise_for_status()
        j = r.json()
        for game_data in j["data"]:
            if steam.appid == str(game_data["profile_steam"]):
                return {
                    "main": game_data["comp_main"] if game_data["comp_main"] != 0 else None,  # Union[int, None]
                    "plus": game_data["comp_plus"] if game_data["comp_plus"] != 0 else None,  # Union[int, None]
                    "completionist": game_data["comp_100"] if game_data["comp_100"] != 0 else None,  # Union[int, None]
                    "external_url": f"https://howlongtobeat.com/game/{game_data['game_id']}"  # str
                }
