import asyncio
import logging
import time
from typing import Any

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

from .service_manager import service_manager
from .utils import ANSICodes

app = FastAPI(docs_url="/")

details_lock = asyncio.Lock()

details_cache: dict[float, dict] = {}

logger = logging.getLogger(f"{ANSICodes.MAGENTA}api{ANSICodes.RESET}")


@app.get("/wishlist")
async def wishlist(profile_name_or_id: str):
    """Get the wishlist data for the given profile name or id."""
    game_appids: list[int] | None = await service_manager.get_wishlist(profile_name_or_id)
    if game_appids is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Steam ID / Profile not found (your wishlist must be public)")
    return game_appids


@app.get("/details")
async def details(appid_or_name: str):
    """Get the details for the given appid or name."""
    if details_lock.locked():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is busy")

    async with details_lock:

        if appid_or_name.strip() == "":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty search")

        # Get steam details
        steam = None
        if appid_or_name.strip().isdigit():
            steam = await service_manager.steam.create_task(int(appid_or_name))
        if steam is None:
            appid = service_manager.get_appid_from_name(appid_or_name)
            if appid is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
            steam = await service_manager.steam.create_task(appid)
            if steam is None:
                raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get steam details")

        # Remove old cache entries
        for cache_time in list(details_cache.keys()):
            if time.time() - cache_time > 60 * 15:
                logger.debug(f"Removing old cache entry: {cache_time}")
                del details_cache[cache_time]

        # Check if already in cache
        for details in details_cache.values():
            if details["steam"]["appid"] == steam.appid:
                logger.debug(f"App {steam.appid} already in cache")
                details["from_cache"] = True
                return details

        if steam.released:

            details: dict[str, Any] = {
                "steam": steam.model_dump()
            }

            tasks: dict[str, asyncio.Task[BaseModel]] = {}

            # Steam historical low
            if steam.price is None:
                details["steam_historical_low"] = None
            elif steam.price > 0:
                tasks["steam_historical_low"] = service_manager.steamdb.create_task(steam)
            else:
                details["steam_historical_low"] = {
                    "price": 0.0,
                    "iso_date": None
                }

            # Key and gift sellers
            if steam.price is not None and steam.price > 0:
                tasks["key_and_gift_sellers"] = service_manager.keyforsteam.create_task(steam)
            else:
                details["key_and_gift_sellers"] = None

            # Game length
            tasks["game_length"] = service_manager.how_long_to_beat.create_task(steam)

            # Linux support
            if steam.native_linux_support:
                details["linux_support"] = None
            else:
                tasks["linux_support"] = service_manager.protondb.create_task(steam)

            # Run tasks
            results = await asyncio.gather(*tasks.values())
            for task, result in zip(tasks.keys(), results, strict=True):
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

        logger.info(f"Details: {details}")

        # Add to cache
        details_cache[time.time()] = details

        details["from_cache"] = False
        return details


@app.get("/analyze")
async def analyze():
    """Analyze all services and return their data."""
    data = await service_manager.analyze_services()
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data available")
    return data.model_dump()
