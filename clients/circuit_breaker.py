import time
from enum import Enum
from typing import Callable


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitOpenError(Exception):
    pass


class CircuitBreaker:
    def __init__(
        self, name: str, threshold: int = 5, reset_timeout: int = 60
    ):
        self.name = name
        self.threshold = threshold
        self.reset_timeout = reset_timeout
        self.state = CircuitState.CLOSED
        self._failure_count = 0
        self._last_failure_time = 0.0

    @property
    def failure_count(self) -> int:
        return self._failure_count

    def _try_half_open(self) -> None:
        if self.state == CircuitState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.reset_timeout:
                self.state = CircuitState.HALF_OPEN

    def record_success(self) -> None:
        self._failure_count = 0
        self.state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        self._last_failure_time = time.monotonic()
        if self._failure_count >= self.threshold:
            self.state = CircuitState.OPEN

    def check(self) -> None:
        self._try_half_open()
        if self.state == CircuitState.OPEN:
            raise CircuitOpenError(
                f"Circuit '{self.name}' is OPEN "
                f"({self._failure_count} consecutive failures)"
            )

    def wrap(self, fn: Callable) -> Callable:
        async def wrapped(*args, **kwargs):
            self.check()
            try:
                result = await fn(*args, **kwargs)
                self.record_success()
                return result
            except CircuitOpenError:
                raise
            except Exception:
                self.record_failure()
                raise

        return wrapped

    def __repr__(self) -> str:
        return (
            f"CircuitBreaker(name='{self.name}', state={self.state.value}, "
            f"failures={self._failure_count}/{self.threshold})"
        )
