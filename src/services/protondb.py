import logging
from typing import Union

from pydantic import BaseModel

from services.steam import SteamDetails
from utils import http_client


class ProtonDBDetails(BaseModel):
    tier: str
    confidence: str
    report_count: int
    external_url: str


class ProtonDB:
    async def get_game_details(self, steam: SteamDetails) -> Union[ProtonDBDetails, None]:
        logging.info(f"Getting linux support state for {repr(steam.name)} ({steam.appid})")
        r = await http_client.get(f"https://www.protondb.com/api/v1/reports/summaries/{steam.appid}.json")
        logging.info(f"Response (100 chars): {repr(r.text[:100])}")
        logging.debug(f"Response: (all): {r.text}")
        if r.status_code == 404:
            return
        r.raise_for_status()
        data = r.json()
        return ProtonDBDetails(
            tier=data["tier"].upper(),
            confidence=data["confidence"],
            report_count=data["total"],
            external_url=f"https://www.protondb.com/app/{steam.appid}"
        )
