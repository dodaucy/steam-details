import base64
import logging

from .analytics import Analytics, AnalyticsService, render_speed_box_plot
from .service import Service
from .services.how_long_to_beat import HowLongToBeat
from .services.keyforsteam import KeyForSteam
from .services.protondb import ProtonDB
from .services.steam_extension import SteamExtension
from .services.steamdb import SteamDB
from .steam_core import steam_core
from .utils import ANSICodes


class ServiceManager:
    def __init__(self):
        self._logger = logging.getLogger(f"{ANSICodes.MAGENTA}service_manager{ANSICodes.RESET}")

        self.steam_extension = SteamExtension("SteamExtension", logging.getLogger(f"{ANSICodes.CYAN}steam_extension{ANSICodes.RESET}"))
        self.steamdb = SteamDB("SteamDB", logging.getLogger(f"{ANSICodes.BLUE}steamdb{ANSICodes.RESET}"))
        self.protondb = ProtonDB("ProtonDB", logging.getLogger(f"{ANSICodes.GREEN}protondb{ANSICodes.RESET}"))
        self.keyforsteam = KeyForSteam("KeyForSteam", logging.getLogger(f"{ANSICodes.YELLOW}keyforsteam{ANSICodes.RESET}"))
        self.how_long_to_beat = HowLongToBeat("HowLongToBeat", logging.getLogger(f"{ANSICodes.RED}howlongtobeat{ANSICodes.RESET}"))

        self._services: list[Service] = [
            self.steam_extension,
            self.steamdb,
            self.protondb,
            self.keyforsteam,
            self.how_long_to_beat
        ]

    async def start(self) -> None:
        """Load the steam core and all services by calling their load method."""
        # TODO: https://github.com/dodaucy/steam-details/issues/25
        self._logger.info("Loading steam core")
        await steam_core.load()
        self._logger.info("Steam core loaded")
        self._logger.info("Loading all services")
        for service in self._services:
            self._logger.debug(f"Loading {service.name}")
            await service.load_service()
            self._logger.debug(f"Loaded {service.name}")
        self._logger.info("All services loaded")

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
