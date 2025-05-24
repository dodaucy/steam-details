import asyncio
import base64
import logging
import time
from typing import Sequence

from .analytics import Analytics, AnalyticsModule, render_speed_box_plot
from .cache import Cache
from .service import NetworkModule, Service
from .services.how_long_to_beat import HowLongToBeat
from .services.keyforsteam import KeyForSteam
from .services.protondb import ProtonDB
from .services.steam_extension import SteamExtension
from .services.steamdb import SteamDB
from .steam_core import SteamCore, steam_core
from .utils import ANSICodes


class Manager:
    def __init__(self):
        self._logger = logging.getLogger(f"{ANSICodes.MAGENTA}service_manager{ANSICodes.RESET}")

        self.steam_extension = SteamExtension("Steam Extension", logging.getLogger(f"{ANSICodes.CYAN}steam_extension{ANSICodes.RESET}"))
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

        self._network_modules: Sequence[NetworkModule] = [steam_core] + self._services

    def clear_cache(self) -> None:
        """Clear the cache."""
        self._logger.info("Clearing cache")
        for cache in Cache.instances:
            cache.clear()
        self._logger.info("Cache cleared")

    async def start(self) -> None:
        """Load all network modules by calling their load method."""
        self._logger.info("Loading all network modules")
        start = time.time()
        tasks: list[asyncio.Task] = []
        for network_module in self._network_modules:
            self._logger.debug(f"Loading {network_module.name}")
            tasks.append(asyncio.create_task(network_module.load_module(raise_error=False)))
        await asyncio.gather(*tasks)
        self._logger.info(f"All network modules loaded in {time.time() - start:.2f}s")

    async def analyze_modules(self) -> Analytics | None:
        """
        Analyze all modules and return their data.

        Return None if no data is available.
        """
        # Collect data
        modules: list[AnalyticsModule] = []
        speed_histories: dict[str, list[float]] = {}
        for module in self._network_modules:
            if module.load_time is None:
                load_time = None
            else:
                load_time = round(module.load_time, 3)
            if isinstance(module, Service):
                modules.append(AnalyticsModule(
                    name=module.name,
                    load_time=load_time,
                    timeout_count=module.net_get_game_details.timeout_count,
                    error_count=module.net_get_game_details.error_count
                ))
                speed_histories[module.name] = module.net_get_game_details.speed_history
            elif isinstance(module, SteamCore):
                modules.append(AnalyticsModule(
                    name=f"{module.name} (Game)",
                    load_time=load_time,
                    timeout_count=module.net_get_core_details.timeout_count,
                    error_count=module.net_get_core_details.error_count
                ))
                modules.append(AnalyticsModule(
                    name=f"{module.name} (Wishlist)",
                    load_time=0,
                    timeout_count=module.net_get_wishlist_data.timeout_count,
                    error_count=module.net_get_wishlist_data.error_count
                ))
                speed_histories.update({
                    f"{module.name} (Game)": module.net_get_core_details.speed_history,
                    f"{module.name} (Wishlist)": module.net_get_wishlist_data.speed_history
                })

        # Return if no data
        if not modules:
            return

        # Render box plot
        speed_box_plot = await render_speed_box_plot(speed_histories)
        if speed_box_plot is None:
            speed_box_plot_base64 = None
        else:
            speed_box_plot_base64 = base64.b64encode(speed_box_plot).decode()

        # Get cache size
        cache_entries = 0
        for cache in Cache.instances:
            cache_entries += len(cache)

        # Return data
        return Analytics(
            modules=modules,
            speed_box_plot=speed_box_plot_base64,
            cache_entries=cache_entries
        )


manager = Manager()
