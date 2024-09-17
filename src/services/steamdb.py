import logging
import time
from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Union

from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright
from pydantic import BaseModel

from services.steam import SteamDetails
from utils import price_string_to_float


class SteamDBDetails(BaseModel):
    price: float
    discount: Union[int, None]
    iso_date: Union[str, None]
    external_url: str


class SteamDB:
    async def _captcha(self, appid: str, timeout: int) -> None:
        logging.warning("Displaying captcha or bot protection message")
        play = await async_playwright().start()
        with TemporaryDirectory() as td:
            logging.debug(f"Temporary directory: {td}")

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
            logging.info(f"Captcha response status: {response.status}")

            # Wait for captcha to be solved
            start_time = time.time()
            while remaining_time := timeout - (time.time() - start_time) > 0:
                # Wait for page reload
                logging.info(f"Waiting for captcha to be solved (remaining time: {remaining_time:.0f}s)")
                await page.wait_for_url(f"https://steamdb.info/app/{appid}/", timeout=remaining_time)

        # Close
        if browser._loop.is_running():
            await browser.close()
        if play._loop.is_running():
            await play.stop()

    async def _parse_page_content(self, content: str) -> Union[Tag, None]:
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
                                    logging.info(f"Found element: {td}")
                                    return td
                                else:
                                    logging.debug("Muted class not found")
                            else:
                                logging.debug(f"Currency column didn't match: {tds[0].text.strip()}")
                        else:
                            logging.debug(f"tbody columns count didn't match: {tds}")
                else:
                    logging.debug(f"thead columns didn't match: {thead_columns}")
            else:
                logging.debug("thead or tbody not found")

    async def get_game_details(self, steam: SteamDetails, allow_captcha: bool = True) -> Union[SteamDBDetails, None]:
        logging.info(f"Getting historical low for {steam.appid}")
        play = await async_playwright().start()
        with TemporaryDirectory() as td:
            logging.debug(f"Temporary directory: {td}")

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
            logging.info(f"Response status: {response.status}")
            if response.status == 404:
                return
            elif response.status == 403 and allow_captcha:  # Try to bypass bot protection
                await self._captcha(steam.appid, timeout=20)
                return self.get_game_details(steam.appid, steam.price, allow_captcha=False)
            assert response.status == 200, f"Unexpected status: {response.status}"

            # Get response
            page_content = await page.content()
            logging.info(f"Page content (100 chars): {repr(page_content[:100])}")
            logging.debug(f"Page content (all): {page_content}")

            # Parse response
            element = await self._parse_page_content(page_content)
            assert element is not None, "Element not found"
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
            logging.info(f"Historical low: {historical_low}")

            # Close
            await browser.close()
            await play.stop()

            return historical_low
