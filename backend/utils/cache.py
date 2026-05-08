from collections.abc import Callable
from time import monotonic
from typing import TypeVar


T = TypeVar("T")


class TTLCache:
    def __init__(self, ttl_seconds: int = 300):
        self.ttl_seconds = ttl_seconds
        self._values: dict[str, tuple[float, object]] = {}

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        now = monotonic()
        expires_at, value = self._values.get(key, (0, None))
        if now < expires_at:
            return value  # type: ignore[return-value]

        value = factory()
        self._values[key] = (now + self.ttl_seconds, value)
        return value

