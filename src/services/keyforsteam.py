import logging
import re
import unicodedata
from datetime import datetime
from typing import Union
from urllib.parse import quote

from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing_extensions import TypedDict

from services.steam import SteamDetails
from utils import http_client, price_string_to_float, roman_to_int


# This add-on helped to improve the search:
# https://addons.mozilla.org/en-US/firefox/addon/allkeyshop-compare-game-prices/ - version 3.0.10413


PLATFORMS = [
    "PlayStation 4",
    "PlayStation4",
    "PlayStation5",
    "PlayStation 5",
    "pc",
    "win/mac",
    "mac",
    "psn",
    "ps vita",
    "ps4 e ps5",
    "ps4 et Ps5",
    "ps4 and ps5",
    "ps3",
    "ps4",
    "ps5",
    "Xbox one/series",
    "series x|s",
    "xbox series x",
    "xbox live",
    "xbox one",
    "xbox 360",
    "xbox",
    "nintendo switch",
    "nintendo",
    "switch",
    "windows 7",
    "windows 10",
    "windows 11",
]

ADJECTIVES = ["pour", "for", "por", "per", "für", "voor"]

IGNORED_WORDS = [
    "buy online",
    "buy",
    "compra",
    "kup",
    "kaufen",
    "cd key",
    "bind retail",
    "retail key",
    "oem key",
    "retail – download link",
    " – online activation",
    "digital code",
    "digital key",
    "key",
    "clé ",
    " / windows 10",
    "green gift",
    "gift",
    "/ V",
    "bethesda",
    "rocksta",
    "ubisoft connect",
    "pc/xbox live",
    "(pc)",
    "(eu)",
    "activision ng",
    "activision",
    "precommande de",
    "précommande",
    "pre-order",
    "preorder",
    "pre order",
    "édition complète",
    "complete pack",
    "enhanced edition",
    "special edition",
    "ultimate bundle",
    "crossgen bundle",
    "complete edition",
    "definitive edition",
    "ultimate edition",
    "digital deluxe",
    "deluxe",
    "edição completa",
    "édition standard",
    "standard edition",
    "gold edition",
    "game of the Year",
    "anniversary edition",
    "edition",
    "edizione",
    "add-on",
    "importación",
    "rockstar games launcher",
    "rockstar games",
    "gog.com",
    "gog",
    "steam row",
    "steam account",
    "row",
    "dlc",
    "steamcd",
    "steam ww",
    "steam",
    "ea play",
    "electronic arts",
    "epic games",
    "microsoft",
    "battle.net",
    "uplay",
    "origin",
    "/ biohazard 4",
    "global",
    "africa",
    "albania",
    "algeria",
    "angola",
    "argentina",
    "armenia",
    "asia",
    "austria",
    "australia",
    "bahrain",
    "bangladesh",
    "barbados",
    "belgium",
    "bolivia",
    "brazil",
    "brunei",
    "bulgaria",
    "cambodia",
    "cameroon",
    "canada",
    "chile",
    "china",
    "colombia",
    "congo",
    "costa rica",
    "croatia",
    "cuba",
    "cyprus",
    "czechia",
    "denmark",
    "djibouti",
    "germany",
    "ecuador",
    "egypt",
    "emea",
    "eritrea",
    "estonia",
    "eswatini",
    "ethiopia",
    "eng",
    "europe",
    "eu",
    "fiji",
    "finland",
    "france",
    "francia",
    "francesa",
    "gabon",
    "gambia",
    "georgia",
    "ghana",
    "greece",
    "grenada",
    "guatemala",
    "guinea",
    "haiti",
    "honduras",
    "hungary",
    "italy",
    "iceland",
    "india",
    "indonesia",
    "ireland",
    "japan",
    "kenya",
    "latam",
    "latvia",
    "lebanon",
    "lesotho",
    "liberia",
    "liechtenstein",
    "mexico",
    "malaysia",
    "nigeria",
    "north america",
    "south america",
    "philippines",
    "ru/cis",
    "spain",
    "turkey",
    "uk",
    "united states",
    "united kingdom",
    "us/ca",
    "us",
    "numérique de luxe",
]

IGNORED_CHARS = [":", "™", "-", "(", ")", "[", "]", "{", "}", "/", ",", "©", "®"]


class CheapestOffer(TypedDict):
    price: float
    form: str
    seller: str
    edition: str


class HistoricalLow(TypedDict):
    price: float
    seller: str
    iso_date: str


class KeyForSteamDetails(BaseModel):
    cheapest_offer: CheapestOffer
    historical_low: HistoricalLow
    external_url: str


class KeyForSteam:
    def _normalize_string(self, input_str: str) -> str:
        return (
            unicodedata.normalize("NFD", input_str)
            .encode("ascii", "ignore")
            .decode("utf-8")
        )

    def _purge_words(self, name: str, words: list[str]) -> str:
        for word in words:
            name = re.sub(
                r"\b" + re.escape(self._normalize_string(word).replace("’", "'")) + r"\b",
                "",
                name,
            )
        return name

    def _purge_chars(self, name: str, chars: list[str]) -> str:
        for char in chars:
            name = re.sub(re.escape(char.lower()), " ", name)
        return name

    async def _get_internal_id(self, game_url: str) -> Union[int, None]:
        # Get game page
        r = await http_client.get(game_url)
        logging.info(f"Response (100 chars): {repr(r.text[:100])}")
        logging.debug(f"Response: (all): {r.text}")
        if r.status_code == 404:
            return
        r.raise_for_status()

        # Get internal ID
        soup = BeautifulSoup(r.text, "html.parser")
        internal_id = None
        for script_tag in soup.find_all("script"):
            if script_tag.text.startswith("var game_id=\"") and script_tag.text.endswith("\""):
                internal_id = int(script_tag.text.split("var game_id=\"")[-1].split("\"")[0])
                logging.info(f"Internal KeyForSteam ID: {internal_id}")
                break
        assert internal_id is not None

        return internal_id

    async def get_game_details(self, steam: SteamDetails) -> Union[KeyForSteamDetails, None]:
        logging.info(f"Getting KeyForSteam data for {repr(steam.name)} ({steam.appid})")

        # Convert roman numbers to integers
        int_name_list = []
        for word in steam.name.split(" "):
            int_word = roman_to_int(word)
            if int_word is None:
                int_name_list.append(word)
            else:
                int_name_list.append(str(int_word))
        int_name = " ".join(int_name_list)

        # Get internal ID and link directly
        game_url = f"https://www.keyforsteam.de/{'-'.join(int_name.lower().split(' '))}-key-kaufen-preisvergleich/"
        internal_id = await self._get_internal_id(game_url)

        # Get internal ID and link via search
        if internal_id is None:
            logging.info("Couldn't get internal ID, trying search")

            # Get full ignored word list
            ignored_word_list = IGNORED_WORDS + PLATFORMS
            for platform in PLATFORMS:
                for adjective in ADJECTIVES:
                    ignored_word_list.append(f"{adjective} {platform}")

            # Purge name
            purged_name = re.sub(r"\s\s+", " ", self._purge_words(
                self._purge_chars(self._purge_words(
                    self._normalize_string(int_name.lower()).replace("&#39;", "'"),
                    ignored_word_list
                ), IGNORED_CHARS),
                ignored_word_list
            )).strip()
            logging.info(f"Purged name: {purged_name}")

            # Search for game
            r = await http_client.get(
                "https://www.allkeyshop.com/api/latest/vaks.php",
                params={
                    "action": "products",
                    "showOffers": "1",
                    "showVouchers": "false",
                    "locale": "de_DE",
                    "currency": "eur",
                    "apiKey": "vaks_extension",
                    "search": quote(purged_name)
                }
            )
            logging.info(f"Response (100 chars): {repr(r.text[:100])}")
            logging.debug(f"Response: (all): {r.text}")
            r.raise_for_status()
            search_result = r.json()

            # Display warnings
            if "warnings" in search_result and isinstance(search_result["warnings"], list):
                for warning in search_result["warnings"]:
                    logging.warning(f"KeyForSteam warning: {repr(warning)}")

            # Check for errors
            if "errors" in search_result and isinstance(search_result["errors"], list) and len(search_result["errors"]) > 0:
                for error in search_result["errors"]:
                    logging.error(f"KeyForSteam error: {repr(error)}")
                raise Exception(f"KeyForSteam errors: {repr(search_result['errors'])}")

            assert search_result["status"] == "success"

            # Filter products
            products = []
            for product in search_result["products"]:
                # Validate link
                if not product["link"].startswith("https://www.keyforsteam.de/") or not product["link"].endswith("-key-kaufen-preisvergleich/"):
                    logging.debug(f"Invalid link: {repr(product['link'])}")
                    continue
                # TODO: Validate publisher, developer and release date (ONLY IF NECESSARY DUE TO MANY PRODUCTS)
                logging.debug(f"Found product: {repr(product['name'])} ({repr(product['link'])})")
                products.append(product)

            # Check products
            if len(products) == 0:
                logging.info("No KeyForSteam products found")
                return
            elif len(products) > 1:
                raise Exception("Too many KeyForSteam products found")

            game_url = products[0]["link"]
            assert isinstance(game_url, str)
            internal_id = products[0]["id"]
            assert isinstance(internal_id, int)

        # Get price offers
        logging.info(f"Getting price offers for internal id {internal_id}")
        r = await http_client.get(
            "https://www.keyforsteam.de/wp-admin/admin-ajax.php",
            params={
                "action": "get_offers",
                "product": internal_id,
                "currency": "eur",
                "locale": "de-DE",
            }
        )
        logging.info(f"Response (100 chars): {repr(r.text[:100])}")
        logging.debug(f"Response: (all): {r.text}")
        r.raise_for_status()
        offers_data = r.json()

        # Display warnings
        if "warnings" in offers_data and isinstance(offers_data["warnings"], list):
            for warning in offers_data["warnings"]:
                logging.warning(f"KeyForSteam warning: {repr(warning)}")

        # Check for errors
        if "errors" in offers_data and isinstance(offers_data["errors"], list) and len(offers_data["errors"]) > 0:
            for error in offers_data["errors"]:
                logging.error(f"KeyForSteam error: {repr(error)}")
            raise Exception(f"KeyForSteam errors: {repr(offers_data['errors'])}")

        # Get cheapest offer
        cheapest_offer = None
        for offer in offers_data["offers"]:
            if all((
                cheapest_offer is None or offer["price"]["eur"]["priceCard"] < cheapest_offer["price"]["eur"]["priceCard"],
                offer["isActive"],
                offer["stock"] == "InStock",
                "ACCOUNT" not in offers_data["regions"][offer["region"]]["name"],
                "ONLY" not in offers_data["regions"][offer["region"]]["name"],
                "AUF" not in offers_data["regions"][offer["region"]]["name"],
                "Steam" != offers_data["merchants"][str(offer["merchant"])]["name"]
            )):
                cheapest_offer = offer
        if cheapest_offer is None:
            return

        # Get price history
        logging.info(f"Getting price history for internal id {internal_id}")
        r = await http_client.get(
            "https://www.allkeyshop.com/api/price_history_api.php",
            params={
                "normalised_name": internal_id,
                "currency": "EUR",
                "database": "keyforsteam.de",
                "v2": 1
            }
        )
        logging.info(f"Response (100 chars): {repr(r.text[:100])}")
        logging.debug(f"Response: (all): {r.text}")
        r.raise_for_status()
        price_history_data = r.json()

        # Format and bundle data
        cheapest_offer_price = round(cheapest_offer["price"]["eur"]["priceCard"], 2)
        cheapest_offer_seller = offers_data["merchants"][str(cheapest_offer["merchant"])]["name"]
        historical_low_price = price_string_to_float(price_history_data["lower_keyshops_price"]["price"])
        historical_low_seller = price_history_data["merchants"][price_history_data["lower_keyshops_price"]["merchant_id"]]["name"]
        historical_low_iso_date = datetime.strptime(price_history_data["lower_keyshops_price"]["last_update"], "%Y-%m-%d %H:%M:%S").isoformat()
        if cheapest_offer_price < historical_low_price:
            historical_low_price = cheapest_offer_price
            historical_low_seller = cheapest_offer_seller
            historical_low_iso_date = None

        # Return data
        return KeyForSteamDetails(
            cheapest_offer=CheapestOffer(
                price=cheapest_offer_price,
                form=offers_data["regions"][cheapest_offer["region"]]["name"],
                seller=cheapest_offer_seller,
                edition=offers_data["editions"][cheapest_offer["edition"]]["name"]
            ),
            historical_low=HistoricalLow(
                price=historical_low_price,
                seller=historical_low_seller,
                iso_date=historical_low_iso_date
            ),
            external_url=game_url
        )
