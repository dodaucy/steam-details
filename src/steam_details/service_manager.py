import base64
import logging

from .analytics import Analytics, AnalyticsService, render_speed_box_plot
from .service import Service
from .services.how_long_to_beat import HowLongToBeat
from .services.keyforsteam import KeyForSteam
from .services.protondb import ProtonDB
from .services.steam import Steam
from .services.steamdb import SteamDB
from .utils import ANSICodes


class ServiceManager:
    def __init__(self):
        self._logger = logging.getLogger(f"{ANSICodes.MAGENTA}service_manager{ANSICodes.RESET}")

        self.steam = Steam("Steam", f"{ANSICodes.CYAN}steam{ANSICodes.RESET}")
        self.steamdb = SteamDB("SteamDB", f"{ANSICodes.BLUE}steamdb{ANSICodes.RESET}")
        self.protondb = ProtonDB("ProtonDB", f"{ANSICodes.GREEN}protondb{ANSICodes.RESET}")
        self.keyforsteam = KeyForSteam("KeyForSteam", f"{ANSICodes.YELLOW}keyforsteam{ANSICodes.RESET}")
        self.how_long_to_beat = HowLongToBeat("HowLongToBeat", f"{ANSICodes.RED}howlongtobeat{ANSICodes.RESET}")

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
            self._logger.debug(f"Loading {service.name}")
            await service.load_service()
            self._logger.debug(f"Loaded {service.name}")
        self._logger.info("All services loaded")

    async def get_appid_from_name(self, name: str) -> int | None:
        """Get the app id for the given name using the steam app list."""
        return await self.steam.get_app(name)

    async def get_wishlist(self, profile_name_or_id: str) -> list[int] | None:
        """Get the wishlist data for the given profile name or id."""
        return await self.steam.get_wishlist_data(profile_name_or_id)

    async def analyze_services(self) -> Analytics | None:
        """
        Analyze all services and return their data.

        Return None if no data is available.
        """
        # Collect data
        services: list[AnalyticsService] = []
        speed_histories: dict[str, list[float]] = {}
        for service in self._services:
            if service.load_time is None:
                load_time = None
            else:
                load_time = round(service.load_time, 3)
            services.append(AnalyticsService(
                name=service.name,
                load_time=load_time,
                timeout_count=service.timeout_count,
                error_count=service.error_count
            ))
            speed_histories[service.name] = service.speed_history

        # Return if no data
        if not services:
            return

        # Render box plot
        speed_box_plot = await render_speed_box_plot(speed_histories)
        if speed_box_plot is None:
            speed_box_plot_base64 = None
        else:
            speed_box_plot_base64 = base64.b64encode(speed_box_plot).decode()

        # Return data
        return Analytics(
            services=services,
            speed_box_plot=speed_box_plot_base64
        )


service_manager = ServiceManager()
