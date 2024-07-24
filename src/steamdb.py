import time
from datetime import datetime
from tempfile import TemporaryDirectory
from typing import Union

from bs4 import BeautifulSoup, Tag
from playwright.async_api import async_playwright

from utils import price_string_to_float


async def _captcha(appid: str, timeout: int) -> None:
    print("Displaying captcha or bot protection message")
    play = await async_playwright().start()
    with TemporaryDirectory() as td:
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
        print(f"Captcha response status: {response.status}")

        # Wait for captcha to be solved
        start_time = time.time()
        while remaining_time := timeout - (time.time() - start_time) > 0:
            # Wait for page reload
            print(f"Waiting for captcha to be solved (remaining time: {remaining_time:.0f}s)")
            await page.wait_for_url(f"https://steamdb.info/app/{appid}/", timeout=remaining_time)

    # Close
    if browser._loop.is_running():
        await browser.close()
    if play._loop.is_running():
        await play.stop()


async def _parse_page_content(content: str) -> Union[Tag, None]:
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
                        td = tds[4]
                        if td.has_attr("class") and "muted" in td["class"]:
                            print(f"Found element: {td}")
                            return td
                        else:
                            print("Muted class not found")
                    else:
                        print(f"tbody columns count didn't match: {tds}")
            else:
                print(f"thead columns didn't match: {thead_columns}")
        else:
            print("thead or tbody not found")


async def get_steam_historical_low(appid: str, steam_price: float, allow_captcha: bool = True) -> Union[dict, None]:
    print(f"Getting historical low for {appid}")
    play = await async_playwright().start()
    with TemporaryDirectory() as td:
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
        response = await page.goto(f"https://steamdb.info/app/{appid}/")
        print(f"Response status: {response.status}")
        if response.status == 404:
            return
        elif response.status == 403 and allow_captcha:  # Try to bypass bot protection
            await _captcha(appid, timeout=20)
            return get_steam_historical_low(appid, steam_price, allow_captcha=False)
        assert response.status == 200, f"Unexpected status: {response.status}"

        # Get response
        page_content = await page.content()
        print(f"Page content: {page_content}")

        # Parse response
        element = await _parse_page_content(page_content)
        assert element is not None, "Element not found"
        historical_low = {
            "price": min(price_string_to_float(element.text.split("at")[0]), steam_price),  # float
            "iso_date": datetime.strptime(element["title"].strip(), "%d %B %Y").date().isoformat()  # str
        }
        print(f"Historical low: {historical_low}")

        # Close
        await browser.close()
        await play.stop()

        return historical_low
