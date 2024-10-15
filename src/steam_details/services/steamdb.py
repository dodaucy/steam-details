import time
from datetime import datetime
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright
from pydantic import BaseModel

from ..service import Service
from ..services.steam import SteamDetails
from ..utils import price_string_to_float


class SteamDBDetails(BaseModel):
    price: float
    discount: int
    iso_date: str | None  # None -> Today
    external_url: str


class SteamDB(Service):
    def __init__(self, name: str, log_name: str):
        super().__init__(name, log_name, "https://steamdb.info/app/{steam.appid}/")

    async def _captcha(self, appid: int, timeout: int) -> None:  # noqa: ASYNC109
        self.logger.warning("Displaying captcha or bot protection message")
        play = await async_playwright().start()
        with TemporaryDirectory() as td:
            self.logger.debug(f"Temporary directory: {td}")

            # New browser
            browser = await play.firefox.launch_persistent_context(
                user_data_dir=td,
                headless=False
            )

            # New page
            if len(browser.pages) > 0:
                page = browser.pages[0]
            else:
                page = await browser.new_page()

            # Open page
            response = await page.goto(f"https://steamdb.info/app/{appid}/")
            self.logger.info(f"Captcha response status: {response.status}")

            # Wait for captcha to be solved
            start_time = time.time()
            while remaining_time := timeout - (time.time() - start_time) > 0:
                # Wait for page reload
                self.logger.info(f"Waiting for captcha to be solved (remaining time: {remaining_time:.0f}s)")
                await page.wait_for_url(f"https://steamdb.info/app/{appid}/", timeout=remaining_time)

        # Close
        if browser._loop.is_running():
            await browser.close()
        if play._loop.is_running():
            await play.stop()

    async def _parse_page_content(self, content: str) -> Tag | None:
        soup = BeautifulSoup(content, "html.parser")
        for table_tag in soup.find_all("table"):
            thead = table_tag.find("thead")
            tbody = table_tag.find("tbody")
            if thead is not None and tbody is not None:
                thead_columns = []
                for th in thead.find_all("th"):
                    thead_columns.append(th.text.strip())
                if thead_columns == ["Currency", "Current Price", "Converted Price", "Lowest Recorded Price"]:
                    for tr in tbody.find_all("tr"):
                        tds = tr.find_all("td")
                        if len(tds) == 5:
                            if tds[0].text.strip() == "Euro":
                                td = tds[4]
                                if td.has_attr("class") and "muted" in td["class"]:
                                    self.logger.info(f"Found element: {td}")
                                    return td
                                else:
                                    self.logger.debug("Muted class not found")
                            else:
                                self.logger.debug(f"Currency column didn't match: {tds[0].text.strip()}")
                        else:
                            self.logger.debug(f"tbody columns count didn't match: {tds}")
                else:
                    self.logger.debug(f"thead columns didn't match: {thead_columns}")
            else:
                self.logger.debug("thead or tbody not found")

    async def get_game_details(self, steam: SteamDetails, allow_captcha: bool = True) -> SteamDBDetails | None:
        """Get steam historical low price from SteamDB."""
        self.logger.info(f"Getting historical low for {steam.appid}")

        if steam.price is None or steam.discount is None:
            raise Exception("Steam price or discount not found")

        play = await async_playwright().start()
        with TemporaryDirectory() as td:
            self.logger.debug(f"Temporary directory: {td}")

            # New browser
            browser = await play.firefox.launch_persistent_context(
                user_data_dir=td,
                headless=True
            )

            # New page
            if len(browser.pages) > 0:
                page = browser.pages[0]
            else:
                page = await browser.new_page()

            # Open page
            response = await page.goto(f"https://steamdb.info/app/{steam.appid}/")
            self.logger.info(f"Response status: {response.status}")
            if response.status == 404:
                return
            elif response.status == 403 and allow_captcha:  # Try to bypass bot protection
                await self._captcha(steam.appid, timeout=20)
                return self.get_game_details(steam, allow_captcha=False)
            if response.status != 200:
                raise Exception(f"Unexpected status: {response.status}")

            # Get response
            page_content = await page.content()
            self.logger.info(f"Page content (100 chars): {repr(page_content[:100])}")
            self.logger.debug(f"Page content (all): {page_content}")

            # Parse response
            element = await self._parse_page_content(page_content)
            if element is None:
                raise Exception("Element not found")
            if "at" in element.text:
                price_string, discount_string = element.text.split("at", 1)
                discount = abs(int(discount_string.split("%", 1)[0]))
            else:
                price_string = element.text
                discount = 0
            historical_low_price = price_string_to_float(price_string)
            if historical_low_price < steam.price:
                historical_low = SteamDBDetails(
                    price=historical_low_price,
                    discount=discount,
                    iso_date=datetime.strptime(element["title"].strip(), "%d %B %Y").date().isoformat(),
                    external_url=f"https://steamdb.info/app/{steam.appid}/"
                )
            else:
                historical_low = SteamDBDetails(
                    price=steam.price,
                    discount=steam.discount,
                    iso_date=None,
                    external_url=f"https://steamdb.info/app/{steam.appid}/"
                )
            self.logger.info(f"Historical low: {historical_low}")

            # Close
            await browser.close()
            await play.stop()

            return historical_low
