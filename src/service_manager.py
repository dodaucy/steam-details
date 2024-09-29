import base64
import logging

from analytics import Analytics, AnalyticsService, render_speed_box_plot
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

    async def analyze_services(self) -> Analytics:
        """Analyze all services and return their data."""
        # Collect data
        services: dict[str, AnalyticsService] = {}
        speed_histories: dict[str, list[float]] = {}
        for service in self._services:
            name = service.__class__.__name__.lower()
            services[name] = AnalyticsService(
                load_time=service.load_time,
                timeout_count=service.timeout_count,
                error_count=service.error_count
            )
            speed_histories[name] = service.speed_history

        # Render box plot
        speed_box_plot = await render_speed_box_plot(speed_histories)

        # Return data
        return Analytics(
            services=services,
            speed_box_plot=base64.b64encode(speed_box_plot).decode()
        )
