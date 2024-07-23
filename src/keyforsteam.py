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
    r = await http_client.get(f"https://www.keyforsteam.de/wp-admin/admin-ajax.php?action=get_offers&product={internal_id}&currency=eur&locale=de-DE")
    print(f"Response: {r.text}")
    r.raise_for_status()
    data = r.json()

    cheapest_offer = None
    for offer in data["offers"]:
        if all((
            cheapest_offer is None or offer["price"]["eur"]["priceCard"] < cheapest_offer["price"]["eur"]["priceCard"],
            offer["isActive"],
            offer["stock"] == "InStock",
            "ACCOUNT" not in data["regions"][offer["region"]]["name"],
            "GLOBAL" not in data["regions"][offer["region"]]["name"]
        )):
            cheapest_offer = offer
    assert cheapest_offer is not None

    print(f"Getting price history for {internal_id}")
    r = await http_client.get(f"https://www.allkeyshop.com/api/price_history_api.php?normalised_name={internal_id}&currency=EUR&database=keyforsteam.de&v2=1")
    print(f"Response: {r.text}")
    r.raise_for_status()
    data = r.json()

    return {
        "cheapest_offer": {
            "price": round(cheapest_offer["price"]["eur"]["priceCard"], 2),
            "form": data["regions"][cheapest_offer["region"]]["name"],
            "seller": data["merchants"][str(cheapest_offer["merchant"])]["name"],
            "edition": data["editions"][cheapest_offer["edition"]]["name"]
        },
        "historical_low": {
            "price": price_string_to_float(data["lower_keyshops_price"]["price"]),
            "seller": data["merchants"][data["lower_keyshops_price"]["merchant_id"]]["name"]
        },
        "external_url": f"https://www.keyforsteam.de/{'-'.join(name.lower().split(' '))}-key-kaufen-preisvergleich/"
    }
