from typing import List, Union

from pydantic import BaseModel

from utils import http_client


class WishlistItem(BaseModel):
    appid: str
    review_score: int
    review_count: str


async def wishlist_data(profile_id: str) -> Union[List[WishlistItem], None]:
    """
    Get the wishlist data for the given profile id
    """
    print(f"Getting wishlist data for {profile_id}")
    r = await http_client.get(f"https://store.steampowered.com/wishlist/profiles/{profile_id}/wishlistdata/")
    print(f"Response: {r.text}")
    if r.status_code != 200:
        print("It seems the profile id is not a valid id, trying with id name")
        r = await http_client.get(f"https://store.steampowered.com/wishlist/id/{profile_id}/wishlistdata/")
        print(f"Response: {r.text}")
        if r.status_code != 200:
            return None
    r.raise_for_status()
    j = r.json()
    items: List[WishlistItem] = []
    for appid, data in j.items():
        screenshots = []
        for screenshot in data["screenshots"]:
            screenshots.append(f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/{screenshot}")
        items.append(
            WishlistItem(
                appid=appid,
                review_score=data["reviews_percent"],
                review_count=data["reviews_total"]
            )
        )
    return items


class SteamDetails(BaseModel):
    appid: str
    name: str
    images: List[str]
    external_url: str

    released: bool
    price: Union[float, None]

    release_date: str
    achievement_count: int
    native_linux_support: bool


async def get_steam_details(appid: str) -> SteamDetails:
    print(f"Getting steam details for {appid}")
    r = await http_client.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=de")
    print(f"Response: {r.text}")
    r.raise_for_status()
    j = r.json()
    steam_data = j[appid]["data"]

    # Get images
    images = [steam_data["header_image"]]
    for screenshot in steam_data["screenshots"]:
        images.append(screenshot['path_thumbnail'])

    # Get price
    if steam_data['is_free'] is True:
        price = 0.0
    elif "price_overview" in steam_data:
        assert steam_data["price_overview"]['currency'] == "EUR"
        price = float(steam_data["price_overview"]["final"] / 100)
    else:
        price = None

    # Achievement count
    if "achievements" in steam_data:
        achievement_count = steam_data["achievements"]["total"]
    else:
        achievement_count = 0

    return SteamDetails(
        appid=appid,
        name=steam_data["name"],
        images=images,
        external_url=f"https://store.steampowered.com/app/{appid}/{'_'.join(steam_data['name'].split(' '))}/",

        released=steam_data["release_date"]["coming_soon"] is False,
        price=price,

        release_date=steam_data["release_date"]["date"],
        achievement_count=achievement_count,
        native_linux_support=steam_data["platforms"]["linux"]
    )
