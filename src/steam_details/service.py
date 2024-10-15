import asyncio
import logging
import time
import traceback

from httpx import ReadTimeout
from pydantic import BaseModel


class Service:
    """Base class for all services."""

    def __init__(self, name: str, log_name: str, default_error_url: str) -> None:
        # Logging
        self.logger = logging.getLogger(log_name)
        self.name = name

        # Error handling
        self._lock = asyncio.Lock()
        self.default_error_url: str = default_error_url
        self.error_url: str | None = None  # Only set in self._lock

        # Stats
        self.load_time: float | None = None
        self.speed_history: list[float] = []
        self.timeout_count: int = 0
        self.error_count: int = 0

        self.logger.debug(f"Initialized {self.name}")

    async def load(self) -> None:
        """Load the service. You can override this."""
        self.logger.debug("Nothing to load")

    async def get_game_details(self, **kwargs) -> BaseModel | None:
        """Get the details of the game. You should override this."""
        raise NotImplementedError

    async def _get_game_details_task(self, **kwargs) -> BaseModel:
        """Get the details of the game."""
        async with self._lock:
            self.logger.debug(f"Starting task {self.name}")
            start_time = time.time()
            self.error_url = self.default_error_url.format(**kwargs)
            try:
                await self.load_check()
                response = await self.get_game_details(**kwargs)
            except ReadTimeout as e:
                self.timeout_count += 1
                self.logger.error(f"Timeout on {self.name}")
                raise e
            except Exception as e:
                self.error_count += 1
                self.logger.error(f"Error on {self.name}: {e.__class__.__name__}: {e}")
                raise e
            else:
                run_time = time.time() - start_time
                self.logger.debug(f"Got response in {run_time:.2f}s")
                self.speed_history.append(run_time)
                return response

    async def load_service(self) -> None:
        """Load the service."""
        if self.load_time is not None:  # Already loaded
            return

        self.logger.debug(f"Loading {self.name}")
        start_time = time.time()

        try:
            await self.load()
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Error loading {self.name}: {e.__class__.__name__}: {e}")
            traceback.print_exc()
        else:
            self.load_time = time.time() - start_time
            self.logger.debug(f"Loaded {self.name} in {self.load_time:.2f}s")

    async def load_check(self) -> None:
        """Check if the service is loaded and try to load it if not."""
        if self.load_time is None:
            self.logger.debug(f"Trying to load {self.name}")
            await self.load_service()
            if self.load_time is None:
                raise RuntimeError("Service failed to load")

    def create_task(self, **kwargs) -> asyncio.Task[BaseModel]:
        """Create a task for the service to get the details of the game."""
        return asyncio.create_task(self._get_game_details_task(**kwargs))
