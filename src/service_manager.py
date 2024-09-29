import logging

from service import Service
from services.how_long_to_beat import HowLongToBeat
from services.keyforsteam import KeyForSteam
from services.protondb import ProtonDB
from services.steam import Steam
from services.steamdb import SteamDB
from utils import ANSICodes


class ServiceManager:
    def __init__(self):
        self._logger = logging.getLogger(f"{ANSICodes.MAGENTA}service_manager{ANSICodes.RESET}")

        self.steam = Steam()
        self.steamdb = SteamDB()
        self.protondb = ProtonDB()
        self.keyforsteam = KeyForSteam()
        self.how_long_to_beat = HowLongToBeat()

        self._services: list[Service] = [
            self.steam,
            self.steamdb,
            self.protondb,
            self.keyforsteam,
            self.how_long_to_beat
        ]

    async def load_services(self) -> None:
        """Load all services by calling their load method."""
        self._logger.info("Loading all services")
        for service in self._services:
            self._logger.debug(f"Loading {service.__class__.__name__}")
            await service.load_service()
            self._logger.debug(f"Loaded {service.__class__.__name__}")
        self._logger.info("All services loaded")

    def get_appid_from_name(self, name: str) -> int | None:
        """Get the app id for the given name using the steam app list."""
        return self.steam.get_app(name)

    async def get_wishlist(self, profile_name_or_id: str) -> list[int] | None:
        """Get the wishlist data for the given profile name or id."""
        return await self.steam.get_wishlist_data(profile_name_or_id)

    async def analyze_services(self) -> ...:  # TODO
        raise NotImplementedError
