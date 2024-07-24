import json
import asyncio
from tempfile import TemporaryDirectory
from typing import Union

from playwright.async_api import async_playwright

from utils import price_string_to_float


async def get_steam_historical_low(appid: str, steam_price: float) -> Union[float, None]:
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
            page = browser.new_page()

        # Open page
        await page.goto(f"https://steamdb.info/app/{appid}/")

        # Wait for page to load
        print("Waiting for page to load")
        counter = 0
        while await page.evaluate("document.getElementById('pricehistory') === null"):
            counter += 1
            if counter > 50:  # 10 seconds timeout
                print("Timed out waiting for page to load")
                return
            await asyncio.sleep(0.2)

        # Scroll to price history
        print("Scrolling to price history")
        await page.evaluate("document.getElementById('pricehistory').scrollIntoView();")

        # Wait for price history to load
        print("Waiting for price history to load")
        counter = 0
        while await page.evaluate("document.getElementById('pricehistory').textContent.trim() === 'Price history'"):
            counter += 1
            if counter > 50:  # 10 seconds timeout
                print("Timed out waiting for price history")
                return
            await asyncio.sleep(0.2)

        # Get price history
        print("Getting price history")
        await page.evaluate(f"""
            const xhr = new XMLHttpRequest();
            xhr.open('GET', 'https://steamdb.info/api/GetPriceHistory/?appid={appid}&cc=eu');
            xhr.onload = () => {{
                var response_div = document.createElement('DIV');
                response_div.id = 'response_div';
                response_div.innerText = xhr.responseText;
                document.body.appendChild(response_div);
            }};
            xhr.send();
        """)

        # Wait for response
        print("Waiting for response")
        counter = 0
        while True:
            counter += 1
            selected_divs = await page.query_selector("div#response_div")
            if selected_divs is not None:
                break
            if counter > 50:  # 10 seconds timeout
                print("Timed out waiting for response")
                return
            await asyncio.sleep(0.2)

        # Parse response
        response = await selected_divs.inner_text()
        print(f"Got response: {response}")
        data = json.loads(response)["data"]

        # Get lowest price
        lowest_price: float = steam_price
        for entry in data["history"]:
            entry_price = price_string_to_float(entry["f"])
            if entry_price < lowest_price:
                lowest_price = entry_price

        return lowest_price
