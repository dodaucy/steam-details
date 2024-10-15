from datetime import datetime

from pydantic import BaseModel

from ..service import Service
from ..utils import http_client


class ReleaseDate(BaseModel):
    display_string: str
    iso_date: str | None


class OverallReviews(BaseModel):
    desc: str
    score: int
    total_reviews: int


class SteamDetails(BaseModel):
    appid: int
    name: str
    images: list[str]
    external_url: str

    released: bool
    price: float | None
    discount: int | None

    release_date: ReleaseDate
    overall_reviews: OverallReviews
    achievement_count: int
    native_linux_support: bool


class Steam(Service):
    def __init__(self, name: str, log_name: str) -> None:
        super().__init__(name, log_name, "https://store.steampowered.com/{appid}")

        self.app_list: dict[str, int] | None = None

    async def load(self) -> None:
        """Get the steam app list."""
        self.logger.info("Downloading app list")
        r = await http_client.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", timeout=30)
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {r.text}")
        r.raise_for_status()

        self.logger.info("Processing app list")
        j = r.json()
        self.app_list = {}
        for app in j["applist"]["apps"]:
            self.app_list[app["name"].lower()] = app["appid"]

        self.logger.info("App list ready")

    async def get_game_details(self, appid: int) -> SteamDetails | None:
        """Get details from steam for the given app id."""
        self.logger.info(f"Getting steam details for {appid}")

        r = await http_client.get(
            "https://store.steampowered.com/api/appdetails",
            params={
                "appids": appid,
                "cc": "de",
                "l": "english"
            }
        )
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {r.text}")
        if r.status_code == 404:
            return
        r.raise_for_status()
        j = r.json()
        if j[str(appid)]["success"] is False:
            return
        steam_data = j[str(appid)]["data"]

        # Get images
        images = [steam_data["header_image"]]
        for screenshot in steam_data["screenshots"]:
            images.append(screenshot["path_thumbnail"])

        # Check if released
        released = steam_data["release_date"]["coming_soon"] is False

        # Get price and discount
        if steam_data["is_free"] is True:
            price = 0.0
            discount = 0
        elif "price_overview" in steam_data:
            if steam_data["price_overview"]["currency"] != "EUR":
                raise Exception(f"Unexpected currency: {repr(steam_data['price_overview']['currency'])}")
            price = float(steam_data["price_overview"]["final"] / 100)
            discount = steam_data["price_overview"]["discount_percent"]
        else:
            price = None
            discount = None

        # Get release date
        if released:
            iso_date = datetime.strptime(steam_data["release_date"]["date"], "%d %b, %Y").date().isoformat()
        else:
            iso_date = None
        release_date = ReleaseDate(
            display_string=steam_data["release_date"]["date"],
            iso_date=iso_date
        )

        # Get reviews
        self.logger.info(f"Getting reviews for {appid}")
        r = await http_client.get(
            f"https://store.steampowered.com/appreviews/{appid}",
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
        self.logger.debug(f"Response: (all): {r.text}")
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

        # Achievement count
        if "achievements" in steam_data:
            achievement_count = steam_data["achievements"]["total"]
        else:
            achievement_count = 0

        return SteamDetails(
            appid=appid,
            name=steam_data["name"],
            images=images,
            external_url=f"https://store.steampowered.com/app/{appid}/",

            released=released,
            price=price,
            discount=discount,

            release_date=release_date,
            overall_reviews=overall_reviews,
            achievement_count=achievement_count,
            native_linux_support=steam_data["platforms"]["linux"]
        )

    async def get_app(self, name: str) -> int | None:
        """Get the app id for the given name using the steam app list."""
        self.logger.debug(f"Getting app id for {repr(name)}")
        await self.load_check()
        return self.app_list.get(name.lower())

    async def get_wishlist_data(self, profile_name_or_id: str) -> list[int] | None:
        """Get the wishlist data for the given profile id."""
        self.logger.info(f"Getting wishlist data for {repr(profile_name_or_id)}")
        await self.load_check()
        r = await http_client.get(
            f"https://store.steampowered.com/wishlist/profiles/{profile_name_or_id}/wishlistdata/",
            params={
                "l": "english"
            }
        )
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {r.text}")
        if r.status_code != 200:
            self.logger.info(f"It seems the profile id {repr(profile_name_or_id)} is not a valid id, trying with profile name")
            r = await http_client.get(
                f"https://store.steampowered.com/wishlist/id/{profile_name_or_id}/wishlistdata/",
                params={
                    "l": "english"
                }
            )
            self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
            self.logger.debug(f"Response: (all): {r.text}")
            if r.status_code != 200:
                return None
        r.raise_for_status()
        j = r.json()
        sorted_items: list[int] = []
        unsorted_items: list[int] = []
        for appid, data in j.items():
            if data["priority"] == 0:
                unsorted_items.append(int(appid))
            else:
                sorted_items.append(int(appid))
        sorted_items.sort(key=lambda x: j[str(x)]["priority"])
        return sorted_items + unsorted_items
