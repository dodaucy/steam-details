import json
import logging
from typing import Iterator, Union
from urllib.parse import quote

from bs4 import BeautifulSoup
from httpx import Response
from pydantic import BaseModel

from services.steam import SteamDetails
from utils import ANSICodes, http_client


class HowLongToBeatDetails(BaseModel):
    main: Union[int, None]
    plus: Union[int, None]
    completionist: Union[int, None]
    external_url: str


class HowLongToBeat:
    def __init__(self):
        self.logger = logging.getLogger(f"{ANSICodes.RED}howlongtobeat{ANSICodes.RESET}")

        # Cache
        self._search_endpoint: Union[str, None] = None
        self._build_id: Union[str, None] = None

    async def load(self) -> None:
        await self._update_search_endpoint_and_build_id()

    async def _update_search_endpoint_and_build_id(self) -> None:
        self.logger.info("Try fetching new howlongtobeat search endpoint")

        # Get index page
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
        self.logger.info(f"Response (100 chars): {repr(index_response.text[:100])}")
        self.logger.debug(f"Response: (all): {index_response.text}")
        index_response.raise_for_status()

        # Parse index page
        soup = BeautifulSoup(index_response.text, "html.parser")

        # Get build ID
        metadata_tag = soup.find("script", {"id": "__NEXT_DATA__", "type": "application/json"})
        assert metadata_tag is not None
        metadata = json.loads(metadata_tag.text)
        assert isinstance(metadata["buildId"], str)
        self._build_id = metadata["buildId"]
        self.logger.info(f"Found howlongtobeat build ID: {repr(self._build_id)}")

        # Get search endpoint
        new_search_endpoint = None
        for script_tag in soup.find_all("script"):
            if script_tag.has_attr("src"):
                src: str = script_tag["src"]
                if src.startswith("/_next/static/chunks/pages/_app-") and src.endswith(".js"):
                    js_url = "https://howlongtobeat.com" + src
                    self.logger.debug(f"Found howlongtobeat JS URL: {repr(js_url)}")

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
                    self.logger.info(f"Response (100 chars): {repr(js_response.text[:100])}")
                    self.logger.debug(f"Response: (all): {js_response.text}")
                    js_response.raise_for_status()

                    for url in self._parse_fetch_urls_from_js(js_response.text):
                        if url.startswith("/api/search") or url.startswith("/api/find"):
                            url = "https://howlongtobeat.com" + url
                            self.logger.info(f"Found howlongtobeat search endpoint: {repr(url)}")
                            new_search_endpoint = url
                            break
                    if new_search_endpoint is not None:
                        break

                else:
                    self.logger.debug(f"Skipping {repr(script_tag['src'])}")

        assert new_search_endpoint is not None
        self._search_endpoint = new_search_endpoint

    async def _search(self, steam: SteamDetails) -> Response:
        assert self._search_endpoint is not None

        # Search
        r = await http_client.post(
            self._search_endpoint,
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
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {r.text}")

        return r

    def _parse_fetch_urls_from_js(self, java_script: str) -> Iterator[str]:
        """
        Extract all fetch urls from the given java script
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
                    self.logger.debug(f"Found raw fetch url: {repr(raw_url)}")

                    splitted_url = raw_url.split('"')
                    self.logger.debug(f"Splitted fetch url: {repr(splitted_url)}")
                    real_url: Union[str, None] = None

                    if len(splitted_url) == 3 and splitted_url[0] == "" and splitted_url[2] == "":  # "..."
                        real_url = splitted_url[1]
                    elif len(splitted_url) == 5 and splitted_url[0] == "" and splitted_url[2] == ".concat(" and splitted_url[4] == ")":  # "...".concat("...")
                        real_url = splitted_url = splitted_url[1] + splitted_url[3]

                    if real_url is None:
                        self.logger.debug(f"Could not parse fetch url: {repr(raw_url)}")
                    else:
                        self.logger.debug(f"Parsed fetch url: {repr(real_url)}")
                        yield real_url

                    break

    async def _parse_search_results(self, steam: SteamDetails, search_results: dict) -> Union[HowLongToBeatDetails, None]:
        for game_data in search_results["data"]:

            if "profile_steam" in game_data:  # Was available in the past (might be removed in the future, it's still here for stability)
                current_appid = int(game_data["profile_steam"])

            else:
                assert isinstance(game_data["game_id"], int)
                props = await self._get_game_props(game_data["game_id"], steam)
                current_appid = int(props["pageProps"]["game"]["data"]["game"][0]["profile_steam"])

            if current_appid == steam.appid:
                return HowLongToBeatDetails(
                    main=game_data["comp_main"] if game_data["comp_main"] != 0 else None,
                    plus=game_data["comp_plus"] if game_data["comp_plus"] != 0 else None,
                    completionist=game_data["comp_100"] if game_data["comp_100"] != 0 else None,
                    external_url=f"https://howlongtobeat.com/game/{game_data['game_id']}"
                )

    async def _get_game_props(self, internal_game_id: int, steam: SteamDetails, *, allow_wrong_build_id: bool = True) -> dict:
        r = await http_client.get(
            f"https://howlongtobeat.com/_next/data/{self._build_id}/game/{internal_game_id}.json",
            params={
                "gameId": internal_game_id
            },
            headers={
                "Priority": "u=0",
                "Referer": quote(f"https://howlongtobeat.com/?q={quote(steam.name)}"),
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "Sec-GPC": "1"
            }
        )
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {r.text}")

        # Allow updating the build id if it's wrong
        if allow_wrong_build_id and r.status_code == 404:
            self.logger.info(f"The howlongtobeat build id ({repr(self._build_id)}) is deprecated")
            self._update_search_endpoint_and_build_id()
            return await self._get_game_props(internal_game_id, steam, allow_wrong_build_id=False)

        r.raise_for_status()
        return r.json()

    async def get_game_details(self, steam: SteamDetails) -> Union[HowLongToBeatDetails, None]:
        self.logger.info(f"Getting how long to beat for {repr(steam.name)} ({steam.appid})")

        # Search
        r = await self._search(steam)
        if r.status_code == 404:
            self.logger.info(f"The howlongtobeat search endpoint ({repr(self._search_endpoint)}) is not available")
            self._update_search_endpoint_and_build_id()
            r = await self._search(steam)

        r.raise_for_status()

        return await self._parse_search_results(steam, r.json())
