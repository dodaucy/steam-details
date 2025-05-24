import logging

from pydantic import BaseModel

from ..service import Service
from ..steam_core import SteamCoreDetails
from ..utils import http_client


class OverallReviews(BaseModel):
    desc: str
    score: int
    total_reviews: int


class SteamExtensionDetails(BaseModel):
    overall_reviews: OverallReviews


class SteamExtension(Service):
    def __init__(self, name: str, logger: logging.Logger) -> None:
        super().__init__(name, logger, "https://store.steampowered.com/app/{steam.appid}")

    async def get_game_details(self, steam: SteamCoreDetails) -> SteamExtensionDetails:
        """Get extented details from steam."""
        self.logger.info(f"Getting steam extension details for {repr(steam.name)} ({steam.appid})")

        # Get reviews
        self.logger.info(f"Getting reviews for {steam.appid}")
        r = await http_client.get(
            f"https://store.steampowered.com/appreviews/{steam.appid}",
            params={
                "json": 1,
                "num_per_page": 0,
                "l": "english",
                "language": "all",
                "review_type": "all",
                "purchase_type": "all"
            }
        )
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {repr(r.text)}")
        r.raise_for_status()

        review_data = r.json()["query_summary"]
        if review_data["total_reviews"] > 0:
            score = round(review_data["total_positive"] / review_data["total_reviews"] * 100)
        else:
            score = 0
        overall_reviews = OverallReviews(
            desc=review_data["review_score_desc"],
            score=score,
            total_reviews=review_data["total_reviews"]
        )

        return SteamExtensionDetails(
            overall_reviews=overall_reviews
        )
