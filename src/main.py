import asyncio
import logging
import time
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from service_manager import ServiceManager


service_manager = ServiceManager()


app = FastAPI(openapi_url=None, on_startup=[service_manager.load_services])

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s"
)


details_lock = asyncio.Lock()

details_cache: Dict[float, dict] = {}


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
    game_appids = await service_manager._steam.get_wishlist_data(profile_name_or_id)
    if game_appids is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Steam ID / Profile not found (your wishlist must be public)")
    return game_appids


@app.get("/details")
async def details(appid_or_name: str):
    if details_lock.locked():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is busy")

    async with details_lock:

        if appid_or_name.strip() == "":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty search")

        # Get steam details
        steam = None
        if appid_or_name.strip().isdigit():
            steam = await service_manager.get_steam_details(int(appid_or_name))
        if steam is None:
            appid = await service_manager._steam.get_app(appid_or_name)
            if appid is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
            steam = await service_manager.get_steam_details(appid)
            if steam is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get steam details")

        # Remove old cache entries
        for cache_time in list(details_cache.keys()):
            if time.time() - cache_time > 60 * 15:
                logging.debug(f"Removing old cache entry: {cache_time}")
                del details_cache[cache_time]

        # Check if already in cache
        for details in details_cache.values():
            if details["steam"]["appid"] == steam.appid:
                logging.debug(f"App {steam.appid} already in cache")
                details["from_cache"] = True
                return details

        if steam.released:

            details: Dict[str, Any] = {
                "steam": steam.model_dump()
            }

            tasks: Dict[str, asyncio.Task[object]] = {}

            # Steam historical low
            if steam.price is None:
                details["steam_historical_low"] = None
            elif steam.price > 0:
                tasks["steam_historical_low"] = service_manager.get_steam_historical_low(steam)
            else:
                details["steam_historical_low"] = {
                    "price": 0.0,
                    "iso_date": None
                }

            # Key and gift sellers
            if steam.price is not None and steam.price > 0:
                tasks["key_and_gift_sellers"] = service_manager.get_key_and_gift_sellers_data(steam)
            else:
                details["key_and_gift_sellers"] = None

            # Game length
            tasks["game_length"] = service_manager.get_game_length(steam)

            # Linux support
            if steam.native_linux_support:
                details["linux_support"] = None
            else:
                tasks["linux_support"] = service_manager.get_linux_support(steam)

            # Run tasks
            results = await asyncio.gather(*tasks.values())
            for task, result in zip(tasks.keys(), results):
                if result is None:
                    details[task] = None
                else:
                    details[task] = result.model_dump()

        else:

            details = {
                "steam": steam.model_dump(),
                "steam_historical_low": None,
                "key_and_gift_sellers": None,
                "game_length": None,
                "linux_support": None
            }

        logging.info(f"Details: {details}")

        # Add to cache
        details_cache[time.time()] = details

        details["from_cache"] = False
        return details
