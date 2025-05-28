import asyncio
import logging
import time
import traceback
from typing import Any, Callable, Hashable

from httpx import ReadTimeout
from pydantic import BaseModel

from .cache import Cache


class ModuleResponse(BaseModel):
    data: Any
    from_cache: bool


class NetworkFunction:
    """An extended async function with stats and cache."""
    def __init__(self, function: Callable[..., Any], logger: logging.Logger) -> None:
        self.name = function.__name__
        self._func = function
        self._lock = asyncio.Lock()
        self.logger = logger

        # Stats
        self.speed_history: list[float] = []
        self.timeout_count: int = 0
        self.error_count: int = 0

        # Cache
        self._cache = Cache(self.name, logger)

        self.logger.debug(f"Initialized network function {self.name}")

    async def __call__(self, *args, _network_cache_key: Hashable | None = None, **kwargs) -> ModuleResponse:
        async with self._lock:
            if _network_cache_key is not None and _network_cache_key in self._cache:
                return ModuleResponse(data=self._cache[_network_cache_key], from_cache=True)
            self.logger.debug(f"Starting task {self.name}")
            start_time = time.time()
            try:
                response = await self._func(*args, **kwargs)
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
                if _network_cache_key is not None:
                    self._cache[_network_cache_key] = response
                return ModuleResponse(data=response, from_cache=False)


class NetworkModule:
    """Base class for all network modules. You can overwrite .load()."""
    def __init__(self, name: str, logger: logging.Logger) -> None:
        self.name = name
        self.logger = logger

        # Stats
        self.load_time: float | None = None

        self.logger.debug(f"Initialized {self.name}")

    @property
    def loaded(self) -> bool:
        return self.load_time is not None

    async def load(self) -> None:
        """Load the service. You can overwrite this."""
        self.logger.debug("Nothing to load")

    async def load_module(self, *, raise_error: bool = True) -> None:
        """Load the network module."""
        if self.loaded:  # Already loaded
            return

        self.logger.info(f"Loading {self.name}")
        start_time = time.time()

        try:
            await self.load()
        except Exception as e:  # noqa: BLE001
            self.logger.error(f"Error loading {self.name}: {e.__class__.__name__}: {e}")
            if raise_error:
                raise
            else:
                traceback.print_exc()
        else:
            self.load_time = time.time() - start_time
            self.logger.info(f"Loaded {self.name} in {self.load_time:.2f}s")
