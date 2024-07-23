from datetime import datetime
from typing import Dict, List, Union

from pydantic import BaseModel

from utils import http_client


app_list: Union[Dict[str, int], None] = None


async def download_app_list() -> None:
    global app_list
    print("Downloading app list")
    r = await http_client.get("https://api.steampowered.com/ISteamApps/GetAppList/v2/", timeout=300)
    print(f"Response status: {r.status_code}")
    r.raise_for_status()
    print("Processing app list")
    j = r.json()
    app_list = {}
    for app in j["applist"]["apps"]:
        app_list[app["name"].lower()] = app["appid"]
    print("App list ready")


async def get_app(name: str) -> Union[str, None]:
    appid = app_list.get(name.lower())
    if appid is not None:
        return str(appid)


async def wishlist_data(profile_id: str) -> Union[List[str], None]:
    """
    Get the wishlist data for the given profile id
    """
    print(f"Getting wishlist data for {profile_id}")
    r = await http_client.get(
        f"https://store.steampowered.com/wishlist/profiles/{profile_id}/wishlistdata/",
        params={
            "l": "english"
        }
    )
    print(f"Response: {r.text}")
    if r.status_code != 200:
        print("It seems the profile id is not a valid id, trying with id name")
        r = await http_client.get(
            f"https://store.steampowered.com/wishlist/id/{profile_id}/wishlistdata/",
            params={
                "l": "english"
            }
        )
        print(f"Response: {r.text}")
        if r.status_code != 200:
            return None
    r.raise_for_status()
    j = r.json()
    sorted_items: List[str] = []
    unsorted_items: List[str] = []
    for appid, data in j.items():
        if data["priority"] == 0:
            unsorted_items.append(appid)
        else:
            sorted_items.append(appid)
    sorted_items.sort(key=lambda x: j[x]["priority"])
    return sorted_items + unsorted_items


class ReleaseDate(BaseModel):
    display_string: str
    iso_date: Union[str, None]


class OverallReviews(BaseModel):
    desc: str
    score: int
    total_reviews: int


class SteamDetails(BaseModel):
    appid: str
    name: str
    images: List[str]
    external_url: str

    released: bool
    price: Union[float, None]

    release_date: ReleaseDate
    overall_reviews: OverallReviews
    achievement_count: int
    native_linux_support: bool


async def get_steam_details(appid: str) -> Union[SteamDetails, None]:
    if not appid.isdigit():
        print(f"Not a valid appid: {appid}")
        return
    print(f"Getting steam details for {appid}")
    r = await http_client.get(
        "https://store.steampowered.com/api/appdetails",
        params={
            "appids": appid,
            "cc": "de",
            "l": "english"
        }
    )
    print(f"Response: {r.text}")
    if r.status_code == 404:
        return
    r.raise_for_status()
    j = r.json()
    if j[appid]["success"] is False:
        return
    steam_data = j[appid]["data"]

    # Get images
    images = [steam_data["header_image"]]
    for screenshot in steam_data["screenshots"]:
        images.append(screenshot["path_thumbnail"])

    # Check if released
    released = steam_data["release_date"]["coming_soon"] is False

    # Get price
    if steam_data["is_free"] is True:
        price = 0.0
    elif "price_overview" in steam_data:
        assert steam_data["price_overview"]["currency"] == "EUR"
        price = float(steam_data["price_overview"]["final"] / 100)
    else:
        price = None

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
    print(f"Getting reviews for {appid}")
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
    print(f"Response: {r.text}")
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
        external_url=f"https://store.steampowered.com/app/{appid}/{'_'.join(steam_data['name'].split(' '))}/",

        released=released,
        price=price,

        release_date=release_date,
        overall_reviews=overall_reviews,
        achievement_count=achievement_count,
        native_linux_support=steam_data["platforms"]["linux"]
    )
