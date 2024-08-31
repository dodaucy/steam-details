import logging
from typing import Union

from steam import SteamDetails
from utils import http_client


async def get_linux_support(steam: SteamDetails) -> Union[dict, None]:
    logging.info(f"Getting linux support state for {repr(steam.name)} ({steam.appid})")
    r = await http_client.get(f"https://www.protondb.com/api/v1/reports/summaries/{steam.appid}.json")
    logging.info(f"Response (100 chars): {repr(r.text[:100])}")
    logging.debug(f"Response: (all): {r.text}")
    if r.status_code == 404:
        return
    r.raise_for_status()
    data = r.json()
    return {
        "tier": data["tier"].upper(),  # str
        "confidence": data["confidence"],  # str
        "report_count": data["total"],  # int
        "external_url": f"https://www.protondb.com/app/{steam.appid}"  # str
    }
