import asyncio
import logging
import time
from typing import Union

from services.how_long_to_beat import HowLongToBeat, HowLongToBeatDetails
from services.keyforsteam import KeyForSteam, KeyForSteamDetails
from services.protondb import ProtonDB, ProtonDBDetails
from services.steam import Steam, SteamDetails
from services.steamdb import SteamDB, SteamDBDetails


class ServiceManager:
    def __init__(self):
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
        for service in self._services:
            if hasattr(service, "load"):
                logging.debug(f"Loading {service.__class__.__name__}")
                start_time = time.time()
                await service.load()
                logging.debug(f"Loaded {service.__class__.__name__} in {time.time() - start_time:.2f}s")

        logging.debug("All services loaded")

    async def get_service_details(self, task: asyncio.Task) -> object:
        logging.debug(f"Starting task {task.__class__.__name__}")
        start_time = time.time()
        response = await task
        logging.debug(f"Got response from {task.__class__.__name__} in {time.time() - start_time:.2f}s")
        return response

    def create_task(self, service: object, *args, **kwargs) -> asyncio.Task:
        return asyncio.create_task(self.get_service_details(
            asyncio.create_task(service.get_game_details(*args, **kwargs))
        ))

    def get_steam_details(self, appid: int) -> asyncio.Task[Union[SteamDetails, None]]:
        return self.create_task(self._steam, appid)

    def get_steam_historical_low(self, steam: SteamDetails) -> asyncio.Task[Union[SteamDBDetails, None]]:
        return self.create_task(self._steamdb, steam)

    def get_linux_support(self, steam: SteamDetails) -> asyncio.Task[Union[ProtonDBDetails, None]]:
        return self.create_task(self._protondb, steam)

    def get_key_and_gift_sellers_data(self, steam: SteamDetails) -> asyncio.Task[Union[KeyForSteamDetails, None]]:
        return self.create_task(self._keyforsteam, steam)

    def get_game_length(self, steam: SteamDetails) -> asyncio.Task[Union[HowLongToBeatDetails, None]]:
        return self.create_task(self._how_long_to_beat, steam)
