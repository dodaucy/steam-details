import asyncio
import logging
import time

from pydantic import BaseModel


class Service:
    """Base class for all services."""

    def __init__(self, name: str) -> None:
        # Logging
        self.logger = logging.getLogger(name)

        # Stats
        self.load_time: float | None = None
        self.speed_history: list[float] = []
        self.timeout_count: int = 0
        self.error_count: int = 0

        self.logger.debug(f"Initialized {self.__class__.__name__}")

    async def load(self) -> None:
        """Load the service. You can override this."""
        self.logger.debug("Nothing to load")

    async def get_game_details(self, *args, **kwargs) -> BaseModel | None:
        """Get the details of the game. You should override this."""
        raise NotImplementedError

    async def _get_game_details_task(self, *args, **kwargs) -> BaseModel | None:
        """Get the details of the game."""
        if self.load_time is None:
            raise Exception("Service not loaded")

        self.logger.debug(f"Starting task {self.__class__.__name__}")
        start_time = time.time()

        response = await self.get_game_details(*args, **kwargs)

        run_time = time.time() - start_time
        self.logger.debug(f"Got response in {run_time:.2f}s")
        self.speed_history.append(run_time)
        return response

    async def load_service(self) -> None:
        """Load the service."""
        self.logger.debug(f"Loading {self.__class__.__name__}")
        start_time = time.time()

        await self.load()

        self.load_time = time.time() - start_time
        self.logger.debug(f"Loaded {self.__class__.__name__} in {self.load_time:.2f}s")

    def create_task(self, *args, **kwargs) -> asyncio.Task[BaseModel | None]:
        """Create a task for the service to get the details of the game."""
        return asyncio.create_task(self._get_game_details_task(*args, **kwargs))
