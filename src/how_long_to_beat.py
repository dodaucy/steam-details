import logging
from typing import Union

from steam import SteamDetails
from utils import http_client


async def get_game_length(steam: SteamDetails) -> Union[dict, None]:
    logging.info(f"Getting how long to beat for {repr(steam.name)} ({steam.appid})")
    r = await http_client.post(
        "https://howlongtobeat.com/api/find",
        headers={
            "Origin": "https://howlongtobeat.com",
            "Priority": "u=4",
            "Referer": "https://howlongtobeat.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "Sec-GPC": "1",
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
                    "modifier": "",
                },
                "users": {"sortCategory": "postcount"},
                "lists": {"sortCategory": "follows"},
                "filter": "",
                "sort": 0,
                "randomizer": 0,
            },
            "useCache": True,
        }
    )
    logging.info(f"Response (100 chars): {repr(r.text[:100])}")
    logging.debug(f"Response: (all): {r.text}")
    r.raise_for_status()
    j = r.json()
    for game_data in j["data"]:
        if steam.appid == str(game_data["profile_steam"]):
            return {
                "main": game_data["comp_main"] if game_data["comp_main"] != 0 else None,  # Union[int, None]
                "plus": game_data["comp_plus"] if game_data["comp_plus"] != 0 else None,  # Union[int, None]
                "completionist": game_data["comp_100"] if game_data["comp_100"] != 0 else None  # Union[int, None]
            }
