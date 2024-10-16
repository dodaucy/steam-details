from pydantic import BaseModel

from ..service import Service
from ..services.steam import SteamDetails
from ..utils import http_client


class ProtonDBDetails(BaseModel):
    tier: str
    confidence: str
    report_count: int
    external_url: str


class ProtonDB(Service):
    def __init__(self, name: str, log_name: str) -> None:
        super().__init__(name, log_name, "https://www.protondb.com/app/{steam.appid}")

    async def get_game_details(self, steam: SteamDetails) -> ProtonDBDetails | None:
        """Get linux support state from ProtonDB."""
        self.logger.info(f"Getting linux support state for {repr(steam.name)} ({steam.appid})")

        r = await http_client.get(f"https://www.protondb.com/api/v1/reports/summaries/{steam.appid}.json")
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {r.text}")

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
