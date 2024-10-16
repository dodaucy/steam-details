from datetime import datetime, timezone

from pydantic import BaseModel

from ..service import Service
from ..services.steam import SteamDetails
from ..utils import http_client, price_string_to_float


class SteamDBDetails(BaseModel):
    price: float
    discount: int
    iso_date: str | None  # None -> Today
    external_url: str


class SteamDB(Service):
    def __init__(self, name: str, log_name: str):
        super().__init__(name, log_name, "https://steamdb.info/app/{steam.appid}/")

    async def get_game_details(self, steam: SteamDetails) -> SteamDBDetails | None:
        """Get steam historical low price from SteamDB."""
        self.logger.info(f"Getting historical low for {steam.appid}")

        if steam.price is None or steam.discount is None:
            raise Exception("Steam price or discount not found")

        r = await http_client.get(
            "https://steamdb.info/api/ExtensionAppPrice/",
            params={
                "appid": steam.appid,
                "currency": "EUR",
            },
            headers={
                "Accept": "application/json",
                "Accept-Language": "en-US,en;q=0.5",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
                "X-Requested-With": "SteamDB"
            }
        )
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {r.text}")

        if r.status_code == 404:
            return
        r.raise_for_status()

        j = r.json()

        if j["success"] is not True:
            raise Exception("SteamDB API error")

        historical_low_price = price_string_to_float(j["data"]["p"])
        if historical_low_price < steam.price:
            historical_low = SteamDBDetails(
                price=historical_low_price,
                discount=j["data"]["d"],
                iso_date=datetime.fromtimestamp(j["data"]["t"], tz=timezone.utc).isoformat(),
                external_url=f"https://steamdb.info/app/{steam.appid}/"
            )
        else:
            historical_low = SteamDBDetails(
                price=steam.price,
                discount=steam.discount,
                iso_date=None,
                external_url=f"https://steamdb.info/app/{steam.appid}/"
            )

        self.logger.info(f"Historical low: {historical_low}")
        return historical_low
