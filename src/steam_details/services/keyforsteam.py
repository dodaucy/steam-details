import json
import logging
import re
import unicodedata
from typing import AsyncGenerator

from bs4 import BeautifulSoup
from pydantic import BaseModel
from typing_extensions import TypedDict

from ..cache import Cache
from ..service import Service
from ..steam_core import SteamCoreDetails
from ..utils import http_client, roman_string_to_int_string

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
    historical_low: HistoricalLow
    steam_id: int | None
    keyforsteam_game_url: str


class KeyForSteamDetails(BaseModel):
    cheapest_offer: CheapestOffer
    historical_low: HistoricalLow
    id_verified: bool
    external_url: str


class KeyForSteam(Service):
    def __init__(self, name: str, logger: logging.Logger) -> None:
        super().__init__(name, logger, "https://www.keyforsteam.de")

        # Get full ignored word list
        self._ignored_word_list = IGNORED_WORDS + PLATFORMS
        for platform in PLATFORMS:
            for adjective in ADJECTIVES:
                self._ignored_word_list.append(f"{adjective} {platform}")

        # Product cache
        self._product_cache = Cache("products", self.logger, 60 * 60)

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

        This function is inspired by the allkeyshop add-on:

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

    async def _get_product(
        self,
        internal_id: int,
        keyforsteam_game_url: str,
        historical_low: HistoricalLow
    ) -> Product:
        """Return product details for the given internal ID."""

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
        self.logger.debug(f"Response: (all): {repr(r.text)}")
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
                "KONTO" not in offer.form,
                "ONLY" not in offer.form,
                "AUF" not in offer.form,
                cheapest_offer is None or offer.price < cheapest_offer.price
            )):
                self.logger.debug(f"Found cheaper offer: {offer}")
                cheapest_offer = offer

        # Check if steam offer is available
        steam_id: int | None = None
        if steam_offer is not None:

            # Request redirection
            r = await http_client.get(f"https://www.allkeyshop.com/redirection/offer/eur/{steam_offer.id}")
            self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
            self.logger.debug(f"Response: (all): {repr(r.text)}")
            r.raise_for_status()

            # Get potential steam id
            soup = BeautifulSoup(r.text, "html.parser")
            redirect_data_tag = soup.find("script", {"id": "appData"})
            if redirect_data_tag is None:
                raise Exception("Could not find appData tag")
            redirect_data = json.loads(redirect_data_tag.text)
            redirection_url = redirect_data["redirectionUrl"]
            if not isinstance(redirection_url, str) or not redirection_url.startswith("https://store.steampowered.com/"):
                raise Exception("Invalid redirection URL")
            if redirection_url.startswith("https://store.steampowered.com/app/"):  # Exclude bundles and stuff
                steam_id = int(redirection_url.split("https://store.steampowered.com/app/", 1)[1].split("/", 1)[0].split("?", 1)[0])

        if cheapest_offer is None:
            return Product(
                internal_id=internal_id,
                cheapest_offer=None,
                historical_low=historical_low,
                steam_id=steam_id,
                keyforsteam_game_url=keyforsteam_game_url
            )

        # Overwrite historical low if outdated
        if cheapest_offer.price < historical_low["price"]:
            historical_low = HistoricalLow(
                price=cheapest_offer.price,
                seller=cheapest_offer.seller,
                iso_date=None
            )

        return Product(
            internal_id=internal_id,
            cheapest_offer=CheapestOffer(
                price=cheapest_offer.price,
                form=cheapest_offer.form,
                seller=cheapest_offer.seller,
                edition=cheapest_offer.edition
            ),
            historical_low=historical_low,
            steam_id=steam_id,
            keyforsteam_game_url=keyforsteam_game_url
        )

    async def _search(self, steam: SteamCoreDetails) -> AsyncGenerator[Product, None]:
        """Get internal ID and link via search"""

        purged_name = self._purge_name(steam.name)
        self.logger.info(f"Searching for {repr(purged_name)}")

        # Search for game
        r = await http_client.get(
            "https://www.allkeyshop.com/api/latest/vaks.php",
            params={
                "action": "CatalogV2",
                "sort_field": "relevance",
                "sort_order": "desc",
                "pagenum": 1,
                "per_page": 10,  # Original: 1
                "type": "game",
                "locale": "de_DE",
                "price_mode": "price_card",
                "currency": "eur",
                "apiKey": "vaks_extension",
                "operating_systems": "pc",
                "search_name": purged_name
            }
        )
        self.logger.info(f"Response (100 chars): {repr(r.text[:100])}")
        self.logger.debug(f"Response: (all): {repr(r.text)}")

        # Validate and parse response
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

        # Check status
        if search_result["status"] != "success":
            raise Exception(f"KeyForSteam status: {repr(search_result['status'])}")

        # Filter products
        for product_data in search_result["products"]:
            self.logger.debug(f"Product: {repr(product_data)}")

            # Validate link
            if not product_data["link"].startswith("https://www.keyforsteam.de/") or not product_data["link"].endswith("-key-kaufen-preisvergleich/"):
                self.logger.debug(f"Invalid link: {repr(product_data['link'])}")
                continue

            if product_data["id"] not in self._product_cache:
                # Skip if no historical low
                if product_data["best_historical_offer"] is None:
                    self.logger.debug(f"No historical low for internal id {repr(product_data['id'])}")
                    continue

                # Get historical low
                historical_low = HistoricalLow(
                    price=product_data["best_historical_offer"]["price"],
                    seller=product_data["best_historical_offer"]["merchant"]["name"],
                    iso_date=product_data["best_historical_offer"]["date"]
                )

                # Get product
                product = await self._get_product(
                    internal_id=product_data["id"],
                    keyforsteam_game_url=product_data["link"],
                    historical_low=historical_low
                )

                # Update cache
                self._product_cache[product_data["id"]] = product

            yield self._product_cache[product_data["id"]]

    async def get_game_details(self, steam: SteamCoreDetails) -> KeyForSteamDetails | None:
        """Get cheapest offer and historical low price from KeyForSteam."""
        self.logger.info(f"Getting KeyForSteam data for {repr(steam.name)} ({steam.appid})")

        # Search and filter products
        products: list[Product] = []
        async for product in self._search(steam):
            if product.steam_id is not None:
                # Verify Steam ID
                if product.steam_id != steam.appid:
                    self.logger.info(f"Wrong Steam ID: Seems like {repr(product.internal_id)} ({product.steam_id}) is not the same as {repr(steam.name)} ({steam.appid})")
                    continue

                # Found verified product
                self.logger.info("Found verified product")
                products = [product]
                break

            # Found unverified product
            self.logger.info(f"Valid product: {product}")
            products.append(product)

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

        # Return data
        return KeyForSteamDetails(
            cheapest_offer=product.cheapest_offer,
            historical_low=product.historical_low,
            id_verified=product.steam_id is not None,
            external_url=product.keyforsteam_game_url
        )
