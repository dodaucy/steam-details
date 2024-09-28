import asyncio
import logging
import time
from collections.abc import Awaitable

from services.how_long_to_beat import HowLongToBeat, HowLongToBeatDetails
from services.keyforsteam import KeyForSteam, KeyForSteamDetails
from services.protondb import ProtonDB, ProtonDBDetails
from services.steam import Steam, SteamDetails
from services.steamdb import SteamDB, SteamDBDetails
from utils import ANSICodes


class ServiceManager:
    def __init__(self):
        self._logger = logging.getLogger(f"{ANSICodes.MAGENTA}service_manager{ANSICodes.RESET}")

        self._steam = Steam()
        self._steamdb = SteamDB()
        self._protondb = ProtonDB()
        self._keyforsteam = KeyForSteam()
        self._how_long_to_beat = HowLongToBeat()

        self._services = [
            self._steam,
            self._steamdb,
            self._protondb,
            self._keyforsteam,
            self._how_long_to_beat
        ]

    async def load_services(self) -> None:
        """Load all services by calling their load method."""
        for service in self._services:
            if hasattr(service, "load"):
                self._logger.debug(f"Loading {service.__class__.__name__}")
                start_time = time.time()
                await service.load()
                self._logger.debug(f"Loaded {service.__class__.__name__} in {time.time() - start_time:.2f}s")

        self._logger.debug("All services loaded")

    async def get_service_details(self, service: Awaitable, *args, **kwargs) -> object | None:
        """Get the details of the given service."""
        self._logger.debug(f"Starting task {service.__class__.__name__}")
        start_time = time.time()
        response = await service.get_game_details(*args, **kwargs)
        self._logger.debug(f"Got response from {service.__class__.__name__} in {time.time() - start_time:.2f}s")
        return response

    def create_task(self, service: object, *args, **kwargs) -> asyncio.Task:
        """Create a task for the given service."""
        return asyncio.create_task(self.get_service_details(service, *args, **kwargs))

    def get_steam_details(self, appid: int) -> asyncio.Task[SteamDetails | None]:  # noqa: D102
        return self.create_task(self._steam, appid)

    def get_steam_historical_low(self, steam: SteamDetails) -> asyncio.Task[SteamDBDetails | None]:  # noqa: D102
        return self.create_task(self._steamdb, steam)

    def get_linux_support(self, steam: SteamDetails) -> asyncio.Task[ProtonDBDetails | None]:  # noqa: D102
        return self.create_task(self._protondb, steam)

    def get_key_and_gift_sellers_data(self, steam: SteamDetails) -> asyncio.Task[KeyForSteamDetails | None]:  # noqa: D102
        return self.create_task(self._keyforsteam, steam)

    def get_game_length(self, steam: SteamDetails) -> asyncio.Task[HowLongToBeatDetails | None]:  # noqa: D102
        return self.create_task(self._how_long_to_beat, steam)
