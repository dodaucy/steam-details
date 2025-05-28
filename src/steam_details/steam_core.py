import json
import logging
from datetime import datetime
from typing import cast

from bs4 import BeautifulSoup
from pydantic import BaseModel

from .network_module import NetworkFunction, NetworkModule
from .utils import (ANSICodes, get_colored_logger, http_client,
                    read_js_variables)


class _WishlistItem(BaseModel):
    appid: int
    priority: int


class ReleaseDate(BaseModel):
    display_string: str
    iso_date: str | None


class SteamCoreDetails(BaseModel):
    appid: int
    name: str
    images: list[str]
    external_url: str

    released: bool
    price: float | None
    discount: int | None

    release_date: ReleaseDate | None
    achievement_count: int
    native_linux_support: bool


class SteamCore(NetworkModule):
    def __init__(self) -> None:
        super().__init__("Steam Core", get_colored_logger("steam_core", ANSICodes.CYAN))

        # Cache
        self.app_list: dict[str, int] | None = None

        # Network functions
        self.net_get_core_details = NetworkFunction(self._get_core_details, self.logger)
        self.net_get_wishlist_data = NetworkFunction(self._get_wishlist_data, self.logger)

    async def load(self) -> None:
        """Get the steam app list."""
        self.logger.info("Downloading app list")
        r = await http_client.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", timeout=30)
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {repr(r.text)}")
        r.raise_for_status()

        self.logger.info("Processing app list")
        j = r.json()
        self.app_list = {}
        for app in j["applist"]["apps"]:
            self.app_list[app["name"].lower()] = app["appid"]

        self.logger.info(f"App list ready with {len(self.app_list)} games")

    async def get_app_id_by_name(self, name: str) -> int | None:
        """Get the app id for the given name using the steam app list."""
        await self.load_module()  # Ensure the module is loaded
        self.logger.debug(f"Getting app id for {repr(name)}")
        return cast(dict[str, int], self.app_list).get(name.lower())

    async def _get_core_details(self, appid: int) -> SteamCoreDetails | None:
        """Get steam core details for the given app id."""
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
        self.logger.debug(f"Response: (all): {repr(r.text)}")
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
        if steam_data["release_date"]["date"] == "":
            release_date = None
        else:
            if released:
                iso_date = datetime.strptime(steam_data["release_date"]["date"], "%d %b, %Y").date().isoformat()
            else:
                iso_date = None
            release_date = ReleaseDate(
                display_string=steam_data["release_date"]["date"],
                iso_date=iso_date
            )

        # Achievement count
        if "achievements" in steam_data:
            achievement_count = steam_data["achievements"]["total"]
        else:
            achievement_count = 0

        return SteamCoreDetails(
            appid=appid,
            name=steam_data["name"],
            images=images,
            external_url=f"https://store.steampowered.com/app/{appid}/",

            released=released,
            price=price,
            discount=discount,

            release_date=release_date,
            achievement_count=achievement_count,
            native_linux_support=steam_data["platforms"]["linux"]
        )

    async def _get_wishlist_data(self, profile_name_or_id: str) -> list[int] | None:
        """Get the wishlist data for the given profile name or id."""
        self.logger.info(f"Getting wishlist data for {repr(profile_name_or_id)}")
        if profile_name_or_id.isdigit() and len(bin(int(profile_name_or_id))[2:]) <= 64:
            self.logger.info(f"It seems like {repr(profile_name_or_id)} is a valid steamID64, trying with it")
            wishlist = await self._scrape_wishlist_url(f"https://store.steampowered.com/wishlist/profiles/{profile_name_or_id}/")
            if wishlist is not None:
                return wishlist
            self.logger.info(f"Seems {repr(profile_name_or_id)} is not a user per id, trying with profile name anyway")
        else:
            self.logger.info(f"Seems like {repr(profile_name_or_id)} is not a valid id, trying with profile name")
        return await self._scrape_wishlist_url(f"https://store.steampowered.com/wishlist/id/{profile_name_or_id}/")

    async def _scrape_wishlist_url(self, wishlist_url: str) -> list[int] | None:
        # Get page
        r = await http_client.get(
            wishlist_url,
            params={
                "l": "english"
            },
            headers={
                "Referer": "https://store.steampowered.com/",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "same-origin"
            }
        )
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {repr(r.text)}")
        r.raise_for_status()

        # Parse page
        soup = BeautifulSoup(r.text, "html.parser")
        for script_tag in soup.find_all("script"):
            self.logger.debug(f"Found script tag: {repr(script_tag.text)}")
            variables = read_js_variables(script_tag.text)
            self.logger.debug(f"Variables: {repr(variables)}")

            if "window.SSR.loaderData" in variables:
                self.logger.debug(f"Found window.SSR.loaderData: {repr(variables['window.SSR.loaderData'])}")
                for data_item in variables["window.SSR.loaderData"]:
                    data = json.loads(data_item)
                    if "error" in data:
                        if data["error"] == "ProfileNotFound":
                            return None
                        raise Exception(f"Steam error: {repr(data['error'])}")

            if "window.SSR.renderContext" in variables:
                self.logger.debug(f"Found window.SSR.renderContext: {repr(variables['window.SSR.renderContext'])}")
                for query in json.loads(variables["window.SSR.renderContext"]["queryData"])["queries"]:
                    if "WishlistSortedFiltered" in query["queryKey"]:
                        # Check for errors
                        if query["state"]["error"] is not None:
                            raise Exception(f"Steam error: {repr(query['state']['error'])}")

                        # Sort wishlist
                        sorted_items: list[_WishlistItem] = []
                        unsorted_items: list[int] = []
                        for item in query["state"]["data"]["items"]:
                            if item["priority"] == 0:
                                unsorted_items.append(item["appid"])
                            else:
                                sorted_items.append(
                                    _WishlistItem(
                                        appid=item["appid"],
                                        priority=item["priority"]
                                    )
                                )

                        return [item.appid for item in sorted(sorted_items, key=lambda x: x.priority)] + unsorted_items
                else:
                    self.logger.warning("Could not find WishlistSortedFiltered query")
        else:
            raise Exception("Could not find (all) needed script tag/s")


steam_core = SteamCore()
