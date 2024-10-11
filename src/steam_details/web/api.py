import asyncio
import logging
import time
import traceback
from typing import Any, Literal

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing_extensions import TypedDict

from ..service_manager import service_manager
from ..services.steam import SteamDetails
from ..utils import ANSICodes


class ServiceDetails(TypedDict):
    success: Literal[True]
    data: Any


class ServiceError(TypedDict):
    success: Literal[False]
    error: str


class Details(BaseModel):
    services: dict[str, ServiceDetails | ServiceError]
    from_cache: bool


async def get_json_from_task(task: asyncio.Task[BaseModel | None]) -> ServiceDetails | ServiceError:
    """Run the task and return the result as a JSON object with success status."""
    try:
        response = await task
        if response is None:
            return {
                "success": True,
                "data": None
            }
        else:
            return {
                "success": True,
                "data": response.model_dump()
            }
    except Exception as e:
        traceback.print_exc()
        return {
            "success": False,
            "error": f"{repr(e.__class__.__name__)}: {e}"
        }


app = FastAPI(docs_url="/")

details_lock = asyncio.Lock()

details_cache: dict[float, dict[str, ServiceDetails | ServiceError]] = {}

logger = logging.getLogger(f"{ANSICodes.MAGENTA}api{ANSICodes.RESET}")


@app.get("/wishlist")
async def wishlist(profile_name_or_id: str):
    """Get the wishlist data for the given profile name or id."""
    game_appids: list[int] | None = await service_manager.get_wishlist(profile_name_or_id)
    if game_appids is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Steam ID / Profile not found (your wishlist must be public)")
    return game_appids


@app.get("/details")
async def details(appid_or_name: str, use_cache: bool = True):
    """Get the details for the given appid or name."""
    if details_lock.locked():
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Server is busy")

    async with details_lock:

        if appid_or_name.strip() == "":
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty search")

        # Get steam details
        steam: SteamDetails | None = None
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
        if use_cache:
            for sevices in details_cache.values():
                if sevices["steam"]["data"]["appid"] == steam.appid:
                    logger.debug(f"App {steam.appid} already in cache")
                    return Details(
                        services=sevices,
                        from_cache=True
                    )
            logger.debug(f"App {steam.appid} not in cache")
        else:
            logger.debug("App cache skipped")

        if steam.released:

            services: dict[str, ServiceDetails | ServiceError] = {
                "steam": {
                    "success": True,
                    "data": steam.model_dump()
                }
            }
            tasks: dict[str, asyncio.Task[BaseModel | None]] = {}

            # Steam historical low
            if steam.price is None:
                services["steam_historical_low"] = {
                    "success": True,
                    "data": None
                }
            elif steam.price > 0:
                tasks["steam_historical_low"] = service_manager.steamdb.create_task(steam)
            else:
                services["steam_historical_low"] = {
                    "success": True,
                    "data": {
                        "price": 0.0,
                        "iso_date": None
                    }
                }

            # Key and gift sellers
            if steam.price is not None and steam.price > 0:
                tasks["key_and_gift_sellers"] = service_manager.keyforsteam.create_task(steam)
            else:
                services["key_and_gift_sellers"] = {
                    "success": True,
                    "data": None
                }

            # Game length
            tasks["game_length"] = service_manager.how_long_to_beat.create_task(steam)

            # Linux support
            if steam.native_linux_support:
                services["linux_support"] = {
                    "success": True,
                    "data": None
                }
            else:
                tasks["linux_support"] = service_manager.protondb.create_task(steam)

            # Create JSON tasks
            json_tasks: dict[str, asyncio.Task[ServiceDetails | ServiceError]] = {}
            for name, task in tasks.items():
                json_tasks[name] = get_json_from_task(task)

            # Run tasks
            results = await asyncio.gather(*json_tasks.values())
            for task, result in zip(json_tasks.keys(), results, strict=True):
                services[task] = result

            details = Details(
                services=services,
                from_cache=False
            )

        else:

            details = Details(
                services={
                    "steam": {
                        "success": True,
                        "data": steam.model_dump()
                    },
                    "steam_historical_low": {
                        "success": True,
                        "data": None
                    },
                    "key_and_gift_sellers": {
                        "success": True,
                        "data": None
                    },
                    "game_length": {
                        "success": True,
                        "data": None
                    },
                    "linux_support": {
                        "success": True,
                        "data": None
                    }
                },
                from_cache=False
            )

        logger.info(f"Details: {details}")

        # Add to cache
        details_cache[time.time()] = details.services

        return details.model_dump()


@app.get("/analyze")
async def analyze():
    """Analyze all services and return their data."""
    data = await service_manager.analyze_services()
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data available")
    return data.model_dump()
