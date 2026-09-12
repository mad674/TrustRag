from __future__ import annotations

import threading
import time


class CircuitOpenError(RuntimeError):
    """Raised when a dependency is temporarily unavailable after repeated failures."""


class CircuitBreaker:
    def __init__(self, name: str, failure_threshold: int = 3, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = threading.Lock()

    def _is_open(self) -> bool:
        return self._opened_at is not None and time.monotonic() - self._opened_at < self.recovery_timeout

    def before_call(self) -> None:
        with self._lock:
            if self._is_open():
                raise CircuitOpenError(f"{self.name} is temporarily unavailable")
            if self._opened_at is not None:
                self._opened_at = None
                self._failures = 0

    def record_success(self) -> None:
        with self._lock:
            self._failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold:
                self._opened_at = time.monotonic()
