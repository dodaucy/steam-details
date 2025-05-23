import asyncio
import logging
import traceback
from types import CoroutineType
from typing import Any, Literal, cast

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing_extensions import TypedDict

from ..manager import manager
from ..network_module import ModuleResponse
from ..service import Service
from ..steam_core import SteamCoreDetails, steam_core
from ..utils import ANSICodes


class ServiceDetails(TypedDict):
    success: Literal[True]
    from_cache: bool
    data: Any


class ServiceError(TypedDict):
    success: Literal[False]
    from_cache: Literal[False]
    error: str
    url: str


class Details(BaseModel):
    modules: dict[str, ServiceDetails | ServiceError]


def steam_error(error: Exception) -> HTTPException:
    """Return an HTTPException with the Steam error message."""
    traceback.print_exc()
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Steam error: {error.__class__.__name__}: {error}"
    )


async def get_dict_from_task(task: asyncio.Task[ModuleResponse], service: Service) -> ServiceDetails | ServiceError:
    """Run the service task and return the result as a dictionary with success status."""
    try:
        response = await task
        if response.data is None:
            return {
                "success": True,
                "from_cache": response.from_cache,
                "data": None
            }
        else:
            return {
                "success": True,
                "from_cache": response.from_cache,
                "data": cast(BaseModel, response.data).model_dump()
            }
    except Exception as e:  # noqa: BLE001
        if service.error_url is None:
            raise Exception("Service error URL not set")  # noqa: B904
        else:
            traceback.print_exc()
        return {
            "success": False,
            "from_cache": False,
            "error": f"{e.__class__.__name__}: {e}",
            "url": service.error_url
        }


app = FastAPI(openapi_url=None)

details_lock = asyncio.Lock()

logger = logging.getLogger(f"{ANSICodes.MAGENTA}api{ANSICodes.RESET}")


@app.get("/wishlist")
async def wishlist(profile_name_or_id: str):
    """Get the wishlist data for the given profile name or id."""
    try:
        game_appids: list[int] | None = (await steam_core.net_get_wishlist_data(
            profile_name_or_id,
            _network_cache_key=profile_name_or_id.strip()
        )).data
    except Exception as e:  # noqa: BLE001
        raise steam_error(e)
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

        # Get steam core details
        steam: ModuleResponse | None = None
        if appid_or_name.strip().isdigit():
            try:
                steam = await steam_core.net_get_core_details(
                    int(appid_or_name),
                    _network_cache_key=int(appid_or_name)
                )
            except Exception as e:  # noqa: BLE001
                raise steam_error(e)
        if steam is None or cast(SteamCoreDetails | None, steam.data) is None:
            try:
                appid = steam_core.get_app_id_by_name(appid_or_name)
            except Exception as e:  # noqa: BLE001
                raise steam_error(e)
            if appid is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="App not found")
            try:
                steam = await steam_core.net_get_core_details(
                    appid,
                    _network_cache_key=appid
                )
                if cast(SteamCoreDetails | None, steam.data) is None:
                    raise Exception("Failed to get steam details")
            except Exception as e:  # noqa: BLE001
                raise steam_error(e)
        steam_data: SteamCoreDetails = steam.data

        if steam_data.released:

            modules: dict[str, ServiceDetails | ServiceError] = {
                "steam_core": {
                    "success": True,
                    "from_cache": steam.from_cache,
                    "data": steam_data.model_dump()
                }
            }
            task_services: dict[str, Service] = {
                "steam_extension": manager.steam_extension
            }

            # Steam historical low
            if steam_data.price is None:
                modules["steam_historical_low"] = {
                    "success": True,
                    "from_cache": True,
                    "data": None
                }
            elif steam_data.price > 0:
                task_services["steam_historical_low"] = manager.steamdb
            else:
                modules["steam_historical_low"] = {
                    "success": True,
                    "from_cache": True,
                    "data": {
                        "price": 0.0,
                        "discount": 0,
                        "iso_date": None,
                        "external_url": None
                    }
                }

            # Key and gift sellers
            if steam_data.price is not None and steam_data.price > 0:
                task_services["key_and_gift_sellers"] = manager.keyforsteam
            else:
                modules["key_and_gift_sellers"] = {
                    "success": True,
                    "from_cache": True,
                    "data": None
                }

            # Game length
            task_services["game_length"] = manager.how_long_to_beat

            # Linux support
            if steam_data.native_linux_support:
                modules["linux_support"] = {
                    "success": True,
                    "from_cache": True,
                    "data": None
                }
            else:
                task_services["linux_support"] = manager.protondb

            # Create JSON tasks
            json_tasks: dict[str, CoroutineType[Any, Any, ServiceDetails | ServiceError]] = {}
            for name, service in task_services.items():
                json_tasks[name] = get_dict_from_task(
                    asyncio.create_task(service.net_get_game_details(steam_data, _network_cache_key=steam_data.appid)),
                    service
                )

            # Run tasks
            results = await asyncio.gather(*json_tasks.values())
            for task, result in zip(json_tasks.keys(), results, strict=True):
                modules[task] = result

            details = Details(
                modules=modules
            )

        else:

            details = Details(
                modules={
                    "steam_core": {
                        "success": True,
                        "from_cache": steam.from_cache,
                        "data": steam_data.model_dump()
                    },
                    "steam_extension": {
                        "success": True,
                        "from_cache": True,
                        "data": None
                    },
                    "steam_historical_low": {
                        "success": True,
                        "from_cache": True,
                        "data": None
                    },
                    "key_and_gift_sellers": {
                        "success": True,
                        "from_cache": True,
                        "data": None
                    },
                    "game_length": {
                        "success": True,
                        "from_cache": True,
                        "data": None
                    },
                    "linux_support": {
                        "success": True,
                        "from_cache": True,
                        "data": None
                    }
                }
            )

        logger.info(f"Details: {details}")
        return details.model_dump()


@app.get("/analyze")
async def analyze():
    """Analyze all services and return their data."""
    data = await manager.analyze_modules()
    if data is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No data available")
    return data.model_dump()
