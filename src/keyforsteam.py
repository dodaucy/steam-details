from datetime import datetime
from typing import Union

from bs4 import BeautifulSoup

from utils import http_client, price_string_to_float


async def get_key_and_gift_sellers_data(name: str) -> Union[dict, None]:
    print(f"Getting keyforsteam for {name}")
    r = await http_client.get(f"https://www.keyforsteam.de/{'-'.join(name.lower().split(' '))}-key-kaufen-preisvergleich/")
    print(f"Response: {r.text}")
    if r.status_code == 404:
        return
    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    internal_id = None
    for script_tag in soup.find_all("script"):
        if script_tag.text.startswith("var game_id=\"") and script_tag.text.endswith("\""):
            internal_id = int(script_tag.text.split("var game_id=\"")[-1].split("\"")[0])
            print(f"Internal KeyForSteam ID: {internal_id}")
            break
    assert internal_id is not None

    print(f"Getting price offers for {internal_id}")
    r = await http_client.get(
        "https://www.keyforsteam.de/wp-admin/admin-ajax.php",
        params={
            "action": "get_offers",
            "product": internal_id,
            "currency": "eur",
            "locale": "de-DE",
        }
    )
    print(f"Response: {r.text}")
    r.raise_for_status()
    offers_data = r.json()

    cheapest_offer = None
    for offer in offers_data["offers"]:
        if all((
            cheapest_offer is None or offer["price"]["eur"]["priceCard"] < cheapest_offer["price"]["eur"]["priceCard"],
            offer["isActive"],
            offer["stock"] == "InStock",
            "ACCOUNT" not in offers_data["regions"][offer["region"]]["name"],
            "GLOBAL" not in offers_data["regions"][offer["region"]]["name"]
        )):
            cheapest_offer = offer
    assert cheapest_offer is not None

    print(f"Getting price history for {internal_id}")
    r = await http_client.get(
        "https://www.allkeyshop.com/api/price_history_api.php",
        params={
            "normalised_name": internal_id,
            "currency": "EUR",
            "database": "keyforsteam.de",
            "v2": 1
        }
    )
    print(f"Response: {r.text}")
    r.raise_for_status()
    price_history_data = r.json()

    cheapest_offer_price = round(cheapest_offer["price"]["eur"]["priceCard"], 2)
    cheapest_offer_seller = offers_data["merchants"][str(cheapest_offer["merchant"])]["name"]
    historical_low_price = price_string_to_float(price_history_data["lower_keyshops_price"]["price"])
    historical_low_seller = price_history_data["merchants"][price_history_data["lower_keyshops_price"]["merchant_id"]]["name"]
    historical_low_iso_date = datetime.strptime(price_history_data["lower_keyshops_price"]["last_update"], "%Y-%m-%d %H:%M:%S").isoformat()
    if cheapest_offer_price < historical_low_price:
        historical_low_price = cheapest_offer_price
        historical_low_seller = cheapest_offer_seller
        historical_low_iso_date = None

    return {
        "cheapest_offer": {
            "price": cheapest_offer_price,  # float
            "form": offers_data["regions"][cheapest_offer["region"]]["name"],  # str
            "seller": cheapest_offer_seller,  # str
            "edition": offers_data["editions"][cheapest_offer["edition"]]["name"]  # str
        },
        "historical_low": {
            "price": historical_low_price,  # float
            "seller": historical_low_seller,  # str
            "iso_date": historical_low_iso_date
        },
        "external_url": f"https://www.keyforsteam.de/{'-'.join(name.lower().split(' '))}-key-kaufen-preisvergleich/"
    }
