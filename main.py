import json
import time
from datetime import datetime
from tempfile import TemporaryDirectory

import httpx
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


client = httpx.Client()
client.headers["User-Agent"] = "Mozilla/5.0 (X11; Linux x86_64; rv:129.0) Gecko/20100101 Firefox/129.0"

play = sync_playwright().start()


STEAM_API = "https://store.steampowered.com/api/appdetails?appids={appid}&cc=de"
STEAM_EXTERNAL_URL = "https://store.steampowered.com/app/{appid}/{name}/"

PROTONDB_API = "https://www.protondb.com/api/v1/reports/summaries/{appid}.json"
PROTONDB_EXTERNAL_URL = "https://www.protondb.com/app/{appid}/"

HOW_LONG_TO_BEAT_SEARCH_API = "https://howlongtobeat.com/api/search"
HOW_LONG_TO_BEAT_SEARCH_REQUEST_DATA = {
    "searchType": "games",
    "searchTerms": [],  # [ game name ]
    "searchPage": 1,
    "size": 1,
    "searchOptions": {
        "games": {
            "userId": 0,
            "platform": "PC",
            "sortCategory": "name",
            "rangeCategory": "main",
            "rangeTime": {"min": None, "max": None},
            "gameplay": {"perspective": "", "flow": "", "genre": ""},
            "rangeYear": {"min": "", "max": ""},
            "modifier": "",
        },
        "users": {"sortCategory": "postcount"},
        "lists": {"sortCategory": "follows"},
        "filter": "",
        "sort": 0,
        "randomizer": 0,
    },
    "useCache": True,
}
HOW_LONG_TO_BEAT_SEARCH_ADDITIONAL_REQUEST_HEADERS = {
    "Origin": "https://howlongtobeat.com",
    "Priority": "u=4",
    "Referer": "https://howlongtobeat.com/",
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-origin",
    "Sec-GPC": "1",
}
HOW_LONG_TO_BEAT_EXTERNAL_URL = "https://howlongtobeat.com/game/{internal_id}/"

STEAMDB_INDEX = "https://steamdb.info/app/{appid}/"
STEAMDB_PRICE_HISTORY_API = "https://steamdb.info/api/GetPriceHistory/?appid={appid}&cc=eu"
STEAMDB_EXTERNAL_URL = "https://steamdb.info/app/{appid}/"

KEYFORSTEAM_INDEX = "https://www.keyforsteam.de/{formatted_name}-key-kaufen-preisvergleich/"
KEYFORSTEAM_PRICE_OFFERS_API = "https://www.keyforsteam.de/wp-admin/admin-ajax.php?action=get_offers&product={internal_id}&currency=eur&locale=de-DE"
KEYFORSTEAM_PRICE_HISTORY_API = "https://www.allkeyshop.com/api/price_history_api.php?normalised_name={internal_id}&currency=EUR&database=keyforsteam.de&v2=1"
KEYFORSTEAM_EXTERNAL_URL = "https://www.keyforsteam.de/{formatted_name}-key-kaufen-preisvergleich/"


def display_time(seconds: int) -> str:
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    return f"{hours:02}:{minutes:02}"


def price_string_to_float(price_string: str) -> float:
    return float(price_string.replace("€", "").replace(" ", "").replace(",", "."))


# Get App ID

appid = int(input("App ID or URL: ").split("https://store.steampowered.com/app/")[-1].split("/")[0])

print(f"! App ID: {appid}")


# Get App Details

r = client.get(STEAM_API.format(appid=appid))
r.raise_for_status()

steam_data = r.json()[str(appid)]["data"]
if steam_data['is_free'] is True:
    price = 0.0
else:
    price = steam_data['price_overview']['final_formatted']

print(f"! Name: {steam_data['name']}")
print(f"! Description: {steam_data['short_description']}")
print(f"! Header Image: {steam_data['header_image']}")
print(f"Price: {price}")
print(f"! URL: {STEAM_EXTERNAL_URL.format(appid=appid, name='_'.join(steam_data['name'].split(' ')))}")


# Get KeyForSteam Price History

formatted_name = '-'.join(steam_data['name'].lower().split(' '))

r = client.get(KEYFORSTEAM_INDEX.format(formatted_name=formatted_name))
if r.status_code == 404:
    print("Cannot find any keys for this game.")
else:
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")

    internal_id = None
    for script_tag in soup.find_all("script"):
        if script_tag.text.startswith("var game_id=\"") and script_tag.text.endswith("\""):
            internal_id = int(script_tag.text.split("var game_id=\"")[-1].split("\"")[0])
            print(f"!! Internal KeyForSteam ID: {internal_id}")
            break
    assert internal_id is not None

    r = client.get(KEYFORSTEAM_PRICE_OFFERS_API.format(internal_id=internal_id))
    r.raise_for_status()

    data = r.json()

    cheapest_offer = None
    for offer in data['offers']:
        if all((
            cheapest_offer is None or offer['price']['eur']['priceCard'] < cheapest_offer['price']['eur']['priceCard'],
            offer['isActive'],
            offer['stock'] == "InStock",
            "ACCOUNT" not in data['regions'][offer['region']]['name'],
            "GLOBAL" not in data['regions'][offer['region']]['name']
        )):
            cheapest_offer = offer
    assert cheapest_offer is not None

    print(f"Currently Lowest Key Seller Price: {round(cheapest_offer['price']['eur']['priceCard'], 2)}")
    print(f"! Currently Lowest Key Seller: {data['merchants'][str(cheapest_offer['merchant'])]['name']}")
    print(f"! Region: {data['regions'][cheapest_offer['region']]['name']}")
    print(f"! Edition: {data['editions'][cheapest_offer['edition']]['name']}")

    r = client.get(KEYFORSTEAM_PRICE_HISTORY_API.format(internal_id=internal_id))
    r.raise_for_status()

    data = r.json()

    print(f"All Time Lowest Key Seller Price: {data['lower_keyshops_price']['price']}")
    print(f"! Seller: {data['merchants'][data['lower_keyshops_price']['merchant_id']]['name']}")

    print(f"! URL: {KEYFORSTEAM_EXTERNAL_URL.format(formatted_name=formatted_name)}")


# Get SteamDB Price History

browser = play.firefox.launch_persistent_context(
    user_data_dir=TemporaryDirectory().name,
    headless=True
)

# New page
if len(browser.pages) > 0:
    page = browser.pages[0]
else:
    page = browser.new_page()

# Open SteamDB
print("!! Opening SteamDB...")
page.goto(STEAMDB_INDEX.format(appid=appid))
time.sleep(3)

# Check if price history exists
if page.evaluate("document.getElementById('pricehistory') == null"):
    print("No price history found.")

else:

    # Scroll to pricehistory
    print("!! Scrolling...")
    page.evaluate("document.getElementById('pricehistory').scrollIntoView();")
    time.sleep(3)

    page.evaluate(f"""
        const xhr = new XMLHttpRequest();
        xhr.open('GET', '{STEAMDB_PRICE_HISTORY_API.format(appid=appid)}');
        xhr.onload = () => {{
            var response_div = document.createElement('DIV');
            response_div.id = 'response_div';
            response_div.innerText = xhr.responseText;
            document.body.appendChild(response_div);
        }};
        xhr.send();
    """)

    # Wait for response
    while True:
        print("!! Waiting for response...")
        selected_divs = page.query_selector_all("div#response_div")
        if len(selected_divs) > 0:
            break
        time.sleep(0.2)

    # Parse response
    response = selected_divs[0].inner_text()
    print(f"!! Got response: {response}")
    data = json.loads(response)["data"]

    # Get lowest price
    lowest_price: float = steam_data["price_overview"]["final"]
    for entry in data["history"]:
        entry_price = price_string_to_float(entry["f"])
        if entry_price < lowest_price:
            lowest_price = entry_price

    print(f"Lowest Steam Price: {lowest_price}")
    print(f"! URL: {STEAMDB_EXTERNAL_URL.format(appid=appid)}")

# Close browser
if play._loop.is_running():
    browser.close()
    play.stop()


# Get ProtonDB State

r = client.get(PROTONDB_API.format(appid=appid))
r.raise_for_status()

data = r.json()

print(f"Linux Support: {data['tier'].upper()}")
print(f"! URL: {PROTONDB_EXTERNAL_URL.format(appid=appid)}")


# Get How Long To Beat Times

request_data = HOW_LONG_TO_BEAT_SEARCH_REQUEST_DATA.copy()
request_data["searchTerms"] = [steam_data["name"]]

r = client.post(
    HOW_LONG_TO_BEAT_SEARCH_API,
    headers=HOW_LONG_TO_BEAT_SEARCH_ADDITIONAL_REQUEST_HEADERS,
    json=request_data,
)
r.raise_for_status()

data = r.json()["data"][0]

assert data["profile_steam"] == appid

print(f"Main Story: {display_time(data['comp_main'])}")
print(f"Main + Extras: {display_time(data['comp_plus'])}")
print(f"Completionist: {display_time(data['comp_100'])}")
print(f"All Styles: {display_time(data['comp_all'])}")
print(f"! URL: {HOW_LONG_TO_BEAT_EXTERNAL_URL.format(internal_id=data['game_id'])}")
