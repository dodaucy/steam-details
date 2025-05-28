import logging
import time
from typing import Any, Hashable

from pydantic import BaseModel

from .cli import args


class CacheItem(BaseModel):
    timestamp: float
    key: Hashable
    value: Any


class Cache:
    instances: list["Cache"] = []

    def __init__(self, name: str, logger: logging.Logger) -> None:
        """
        Cache for storing game details.

        :param name: Name of the cache.
        :param logger: Logger to use for logging.
        :param timeout: Timeout in seconds.
        """
        self.name = name
        self._logger = logger
        self._timeout = args.cache_timeout
        self._cache: list[CacheItem] = []

        self.instances.append(self)

    def log(self, message: str) -> None:
        self._logger.debug(f"Cache {repr(self.name)}: {message}")

    def check_timeout(self) -> None:
        """Check if any items in the cache have expired."""
        self.log("Checking timeout")
        for item in self._cache.copy():
            if time.time() - item.timestamp > self._timeout:
                self.log(f"{repr(item.key)} expired")
                self._cache.remove(item)

    def get(self, key: Any) -> CacheItem | None:
        """Get a value from the cache."""
        self.check_timeout()
        self.log(f"Getting {repr(key)}")
        for item in self._cache:
            if item.key == key:
                self.log(f"Found {repr(item.key)}")
                return item.value
        self.log(f"Did not find {repr(key)}")
        return None

    def __getitem__(self, key: Any) -> Any:
        """Get a value from the cache. Does not check timeouts! Use after `in` or use `get` instead."""
        self.log(f"Blindly getting {repr(key)}")
        for item in self._cache:
            if item.key == key:
                self.log(f"Found {repr(item.key)}")
                return item.value
        raise KeyError(f"Key {repr(key)} not found")

    def __setitem__(self, key: Any, value: Any) -> None:
        """Set a value in the cache."""
        self.log(f"Setting {repr(key)} to {repr(value)}")
        self._cache.append(CacheItem(
            timestamp=time.time(),
            key=key,
            value=value
        ))

    def __contains__(self, key: Any) -> bool:
        """Check if a key is in the cache with checking timeouts."""
        return self.get(key) is not None

    def __len__(self) -> int:
        """Get the length of the cache."""
        self.check_timeout()
        return len(self._cache)

    def clear(self) -> None:
        """Clear the cache."""
        self.log("Clearing cache")
        self._cache.clear()

    def destroy(self) -> None:
        """Destroy the cache."""
        self.log("Destroying cache")
        self._cache.clear()
        self.instances.remove(self)
