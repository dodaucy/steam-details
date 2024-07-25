import asyncio
import logging
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from how_long_to_beat import get_game_length
from keyforsteam import get_key_and_gift_sellers_data
from protondb import get_linux_support
from steam import download_app_list, get_app, get_steam_details, wishlist_data
from steamdb import get_steam_historical_low


app = FastAPI(openapi_url=None, on_startup=[download_app_list])

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s"
)


details_lock = asyncio.Lock()


@app.get("/")
async def index(request: Request):
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request
        }
    )


@app.get("/wishlist")
async def wishlist(profile_name_or_id: str):
    game_appids = await wishlist_data(profile_name_or_id)
    if game_appids is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Steam ID / Profile not found")
    return game_appids


@app.get("/details")
async def details(appid_or_name: str):
    if details_lock.locked():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is busy")

    async with details_lock:

        if appid_or_name.strip() == "":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Empty search")

        # Get steam details
        steam = await get_steam_details(appid_or_name)
        if steam is None:
            appid = await get_app(appid_or_name)
            if appid is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
            steam = await get_steam_details(appid)
            if steam is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get steam details")

        if steam.released:

            details: Dict[str, Any] = {
                "steam": steam.model_dump()
            }

            tasks: Dict[str, asyncio.Task] = {}

            # Steam historical low
            if steam.price is None:
                details["steam_historical_low"] = None
            elif steam.price > 0:
                tasks["steam_historical_low"] = asyncio.create_task(get_steam_historical_low(steam))
            else:
                details["steam_historical_low"] = {
                    "price": 0.0,
                    "iso_date": None
                }

            # Key and gift sellers
            if steam.price is not None and steam.price > 0:
                tasks["key_and_gift_sellers"] = asyncio.create_task(get_key_and_gift_sellers_data(steam))
            else:
                details["key_and_gift_sellers"] = None

            # Game length
            tasks["game_length"] = asyncio.create_task(get_game_length(steam))

            # Linux support
            if steam.native_linux_support:
                details["linux_support"] = None
            else:
                tasks["linux_support"] = asyncio.create_task(get_linux_support(steam))

            # Run tasks
            results = await asyncio.gather(*tasks.values())
            for task, result in zip(tasks.keys(), results):
                details[task] = result

            logging.debug(f"Details from released app: {details}")

            return details

        else:

            return {
                "steam": steam.model_dump(),
                "steam_historical_low": None,
                "key_and_gift_sellers": None,
                "game_length": None,
                "linux_support": None
            }
