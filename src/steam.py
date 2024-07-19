from typing import Any, List

from pydantic import BaseModel

from utils import http_client


class WishlistItem(BaseModel):
    appid: str
    name: str
    images: List[str]
    review_score: float
    review_count: str
    release_date_string: str


async def wishlist_data(profile_id: str) -> List[WishlistItem]:
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
    r.raise_for_status()
    j = r.json()
    items: List[WishlistItem] = []
    for appid, data in j.items():
        screenshots = [data["capsule"]]
        for screenshot in data["screenshots"]:
            screenshots.append(f"https://shared.akamai.steamstatic.com/store_item_assets/steam/apps/{appid}/{screenshot}")
        items.append(
            WishlistItem(
                appid=appid,
                name=data["name"],
                images=[data["capsule"]] + screenshots,
                review_score=data["reviews_percent"],
                review_count=data["reviews_total"],
                release_date_string=data["release_string"]
            )
        )
    return items


class SteamDetails(BaseModel):
    name: str
    description: str
    price: float


async def get_steam_details(appid: int) -> SteamDetails:
    print(f"Getting steam details for {appid}")
    r = await http_client.get(f"https://store.steampowered.com/api/appdetails?appids={appid}&cc=de")
    print(f"Response: {r.text}")
    r.raise_for_status()
    j = r.json()
    steam_data = j[str(appid)]["data"]
    if steam_data['is_free'] is True:
        price = 0.0
    else:
        assert steam_data["price_overview"]['currency'] == "EUR"
        price = float(steam_data["price_overview"]["final"] / 100)
    return SteamDetails(
        name=steam_data["name"],
        description=steam_data["short_description"],
        price=price,
    )
