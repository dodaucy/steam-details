import logging

from pydantic import BaseModel

from .network_module import NetworkFunction, NetworkModule
from .steam_core import SteamCoreDetails


class Service(NetworkModule):
    """Base class for all services. You should overwrite .get_game_details()"""
    def __init__(self, name: str, logger: logging.Logger, default_error_url: str) -> None:
        super().__init__(name, logger)

        # Network functions
        self.net_get_game_details = NetworkFunction(self._wrapped_get_game_details, logger)

        # Error handling
        self.default_error_url: str = default_error_url
        self.error_url: str | None = None  # Only set in self._lock

    async def get_game_details(self, steam: SteamCoreDetails) -> BaseModel | None:
        """Get the details of the game. You should overwrite this."""
        raise NotImplementedError

    async def _wrapped_get_game_details(self, steam: SteamCoreDetails) -> BaseModel | None:
        """Get the details of the game."""
        self.error_url = self.default_error_url.format(steam=steam)
        await self.load_module()  # Ensure the module is loaded
        return await self.get_game_details(steam)
