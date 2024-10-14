import json
import re
import unicodedata
from datetime import datetime
from urllib.parse import quote

from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing_extensions import TypedDict

from ..service import Service
from ..services.steam import SteamDetails
from ..utils import http_client, price_string_to_float, roman_string_to_int_string

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


class Offer(BaseModel):
    id: int
    is_available: bool

    price: float
    form: str
    seller: str
    edition: str


class CheapestOffer(TypedDict):
    price: float
    form: str
    seller: str
    edition: str


class HistoricalLow(TypedDict):
    price: float
    seller: str
    iso_date: str | None


class Product(BaseModel):
    internal_id: int
    cheapest_offer: CheapestOffer | None
    id_verified: bool
    keyforsteam_game_url: str


class KeyForSteamDetails(BaseModel):
    cheapest_offer: CheapestOffer
    historical_low: HistoricalLow
    id_verified: bool
    external_url: str


class KeyForSteam(Service):
    def __init__(self, name: str, log_name: str) -> None:
        super().__init__(name, log_name)

        # Get full ignored word list
        self._ignored_word_list = IGNORED_WORDS + PLATFORMS
        for platform in PLATFORMS:
            for adjective in ADJECTIVES:
                self._ignored_word_list.append(f"{adjective} {platform}")

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

    def _purge_name(self, name: str) -> str:
        """
        Purges a game name.

        This function is based on the allkeyshop add-on:

        https://addons.mozilla.org/en-US/firefox/addon/allkeyshop-compare-game-prices/ - version 3.0.10413
        """
        purged_name = re.sub(r"\s\s+", " ", self._purge_words(
            self._purge_chars(self._purge_words(
                self._normalize_string(roman_string_to_int_string(name).lower()).replace("&#39;", "'"),
                self._ignored_word_list
            ), IGNORED_CHARS),
            self._ignored_word_list
        )).strip()
        self.logger.debug(f"Purged name {repr(name)} -> {repr(purged_name)}")
        return purged_name

    async def _get_internal_id_and_name(self, keyforsteam_game_url: str) -> tuple[int | None, str | None]:
        """Return a tuple of the internal ID and name of the game on KeyForSteam or (None, None) if the game page doesn't exist."""
        # Get game page
        r = await http_client.get(keyforsteam_game_url)
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {r.text}")
        if r.status_code == 404:
            return None, None
        r.raise_for_status()
        soup = BeautifulSoup(r.text, "html.parser")

        # Get internal ID
        internal_id = None
        for script_tag in soup.find_all("script"):
            if script_tag.text.startswith('var game_id="') and script_tag.text.endswith('"'):
                internal_id = int(script_tag.text.split('var game_id="')[-1].split('"')[0])
                self.logger.info(f"Internal KeyForSteam ID: {internal_id}")
                break
            else:
                self.logger.debug(f"Skipping script tag: {repr(script_tag)}")
        if internal_id is None:
            raise Exception(f"Could not find KeyForSteam ID in {repr(keyforsteam_game_url)}")

        # Get internal name
        span_tag = soup.find("span", {"data-itemprop": "name"})
        if span_tag is None:
            raise Exception(f"Could not find internal name in {repr(keyforsteam_game_url)}")
        internal_name = span_tag.text.strip()
        self.logger.info(f"Internal name: {repr(internal_name)}")

        return internal_id, internal_name

    async def _get_product(
        self,
        steam: SteamDetails,
        internal_id: int,
        internal_name: str,
        keyforsteam_game_url: str
    ) -> Product | None:
        """Return product details for the given internal ID, or None if the game isn't available."""
        # Verify name
        if self._purge_name(steam.name) != self._purge_name(internal_name):
            self.logger.debug(f"Skipping KeyForSteam ID {internal_id} due to name mismatch: {repr(steam.name)} != {repr(internal_name)}")
            return

        # Get offers
        self.logger.info(f"Getting offers for internal id {internal_id}")
        r = await http_client.get(
            "https://www.keyforsteam.de/wp-admin/admin-ajax.php",
            params={
                "action": "get_offers",
                "product": internal_id,
                "currency": "eur",
                "locale": "de-DE"
            }
        )
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {r.text}")
        r.raise_for_status()
        offers_data = r.json()

        # Display warnings
        if "warnings" in offers_data and isinstance(offers_data["warnings"], list):
            for warning in offers_data["warnings"]:
                self.logger.warning(f"KeyForSteam warning: {repr(warning)}")

        # Check for errors
        if "errors" in offers_data and isinstance(offers_data["errors"], list) and len(offers_data["errors"]) > 0:
            for error in offers_data["errors"]:
                self.logger.error(f"KeyForSteam error: {repr(error)}")
            raise Exception(f"KeyForSteam errors: {repr(offers_data['errors'])}")

        if offers_data["success"] is not True:
            raise Exception("KeyForSteam API error")

        # Evaluate offers
        steam_offer: Offer | None = None
        cheapest_offer: Offer | None = None
        for offer_data in offers_data["offers"]:
            offer = Offer(
                id=offer_data["id"],
                is_available=offer_data["isActive"] and offer_data["stock"] == "InStock",

                price=round(offer_data["price"]["eur"]["priceCard"], 2),
                form=offers_data["regions"][offer_data["region"]]["name"],
                seller=offers_data["merchants"][str(offer_data["merchant"])]["name"],
                edition=offers_data["editions"][offer_data["edition"]]["name"]
            )
            self.logger.debug(f"Offer: {offer}")

            if offer.seller == "Steam":  # Get steam offer
                self.logger.debug(f"Found steam offer: {offer}")
                steam_offer = offer

            elif all((  # Get cheapest offer
                offer.is_available,
                "ACCOUNT" not in offer.form,
                "ONLY" not in offer.form,
                "AUF" not in offer.form,
                cheapest_offer is None or offer.price < cheapest_offer.price
            )):
                self.logger.debug(f"Found cheaper offer: {offer}")
                cheapest_offer = offer

        # Check if steam offer is available
        if steam_offer is not None:

            # Request redirection
            r = await http_client.get(f"https://www.allkeyshop.com/redirection/offer/eur/{steam_offer.id}")
            self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
            self.logger.debug(f"Response: (all): {r.text}")
            r.raise_for_status()

            # Get potential steam id
            soup = BeautifulSoup(r.text, "html.parser")
            redirect_data_tag = soup.find("script", {"id": "appData"})
            if redirect_data_tag is None:
                raise Exception("Could not find appData tag")
            redirect_data = json.loads(redirect_data_tag.text)
            redirection_url = redirect_data["clickBody"]["redirectionUrl"]
            if not isinstance(redirection_url, str) or not redirection_url.startswith("https://store.steampowered.com/"):
                raise Exception("Invalid redirection URL")
            if redirection_url.startswith("https://store.steampowered.com/app/"):  # Exclude bundles and stuff
                potential_steam_id = int(redirection_url.split("https://store.steampowered.com/app/", 1)[1].split("/", 1)[0].split("?", 1)[0])

                # Verify steam id
                if potential_steam_id != steam.appid:
                    self.logger.info(f"Wrong Steam ID: Seems like {repr(internal_name)} ({potential_steam_id}) is not the same as {repr(steam.name)} ({steam.appid})")
                    return

        return Product(
            internal_id=internal_id,
            cheapest_offer=CheapestOffer(
                price=cheapest_offer.price,
                form=cheapest_offer.form,
                seller=cheapest_offer.seller,
                edition=cheapest_offer.edition
            ) if cheapest_offer is not None else None,
            id_verified=steam_offer is not None,
            keyforsteam_game_url=keyforsteam_game_url
        )

    async def get_game_details(self, steam: SteamDetails) -> KeyForSteamDetails | None:
        """Get cheapest offer and historical low price from KeyForSteam."""
        self.logger.info(f"Getting KeyForSteam data for {repr(steam.name)} ({steam.appid})")
        self.error_url = "https://www.keyforsteam.de"

        products: list[Product] = []

        # Get internal ID and link directly
        keyforsteam_game_url = f"https://www.keyforsteam.de/{'-'.join(self._purge_name(steam.name).split(' '))}-key-kaufen-preisvergleich/"
        direct_internal_id, internal_name = await self._get_internal_id_and_name(keyforsteam_game_url)

        if direct_internal_id is not None:
            product = await self._get_product(
                steam=steam,
                internal_id=direct_internal_id,
                internal_name=internal_name,
                keyforsteam_game_url=keyforsteam_game_url
            )
            if product is not None:
                self.logger.info(f"Valid product: {repr(product)}")
                products.append(product)

        if not products or not products[0].id_verified:
            # Get internal ID and link via search
            self.logger.info("Couldn't get internal ID, trying search")

            purged_name = self._purge_name(steam.name)

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
            self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
            self.logger.debug(f"Response: (all): {r.text}")
            r.raise_for_status()
            search_result = r.json()

            # Display warnings
            if "warnings" in search_result and isinstance(search_result["warnings"], list):
                for warning in search_result["warnings"]:
                    self.logger.warning(f"KeyForSteam warning: {repr(warning)}")

            # Check for errors
            if "errors" in search_result and isinstance(search_result["errors"], list) and len(search_result["errors"]) > 0:
                for error in search_result["errors"]:
                    self.logger.error(f"KeyForSteam error: {repr(error)}")
                raise Exception(f"KeyForSteam errors: {repr(search_result['errors'])}")

            if search_result["status"] != "success":
                raise Exception(f"KeyForSteam status: {repr(search_result['status'])}")

            # Filter products
            for product_data in search_result["products"]:
                self.logger.debug(f"Product: {repr(product_data)}")

                # Validate link
                if not product_data["link"].startswith("https://www.keyforsteam.de/") or not product_data["link"].endswith("-key-kaufen-preisvergleich/"):
                    self.logger.debug(f"Invalid link: {repr(product_data['link'])}")
                    continue

                # Skip invalid internal id if present to optimize search
                if direct_internal_id is not None and product_data["id"] == direct_internal_id:
                    self.logger.info(f"Skipping invalid internal id: {product_data['id']}")
                    continue

                # Get product
                product = await self._get_product(
                    steam=steam,
                    internal_id=product_data["id"],
                    internal_name=product_data["name"],
                    keyforsteam_game_url=product_data["link"]
                )
                if product is not None:
                    self.logger.info(f"Valid product: {product}")
                    products.append(product)
                    if product.id_verified:
                        self.logger.info("Cancel search because the correct product was found")
                        products = [product]
                        break

        # Check products
        if len(products) == 0:
            self.logger.info("No KeyForSteam products found")
            return
        elif len(products) > 1:
            raise Exception(f"Too many KeyForSteam products found: Found {len(products)}")

        product = products[0]
        self.error_url = product.keyforsteam_game_url
        self.logger.info(f"Found KeyForSteam product: {product}")

        if product.cheapest_offer is None:
            self.logger.info("No cheapest offer found")
            return

        # Get price history
        self.logger.info(f"Getting price history for internal id {product.internal_id}")
        r = await http_client.get(
            "https://www.allkeyshop.com/api/price_history_api.php",
            params={
                "normalised_name": product.internal_id,
                "currency": "EUR",
                "database": "keyforsteam.de",
                "v2": 1
            }
        )
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {r.text}")
        r.raise_for_status()
        price_history_data = r.json()
        historical_low = HistoricalLow(
            price=price_string_to_float(price_history_data["lower_keyshops_price"]["price"]),
            seller=price_history_data["merchants"][price_history_data["lower_keyshops_price"]["merchant_id"]]["name"],
            iso_date=datetime.strptime(price_history_data["lower_keyshops_price"]["last_update"], "%Y-%m-%d %H:%M:%S").isoformat()
        )

        # Overwrite historical low if outdated
        if product.cheapest_offer["price"] < historical_low["price"]:
            historical_low = HistoricalLow(
                price=product.cheapest_offer["price"],
                seller=product.cheapest_offer["seller"],
                iso_date=None
            )

        # Return data
        return KeyForSteamDetails(
            cheapest_offer=product.cheapest_offer,
            historical_low=historical_low,
            id_verified=product.id_verified,
            external_url=product.keyforsteam_game_url
        )
