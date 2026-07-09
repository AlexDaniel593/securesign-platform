import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional


@dataclass
class RateLimitEntry:
    count: int = 0
    window_start: float = 0.0


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._entries: dict[str, RateLimitEntry] = defaultdict(RateLimitEntry)
        self._lock = Lock()

    def is_allowed(self, key: str) -> tuple[bool, Optional[int]]:
        with self._lock:
            now = time.time()
            entry = self._entries[key]

            if now - entry.window_start >= self.window_seconds:
                entry.count = 1
                entry.window_start = now
                return True, None

            if entry.count >= self.max_requests:
                retry_after = int(self.window_seconds - (now - entry.window_start)) + 1
                return False, retry_after

            entry.count += 1
            return True, None

    def reset(self, key: str) -> None:
        with self._lock:
            if key in self._entries:
                del self._entries[key]


login_rate_limiter = RateLimiter(max_requests=5, window_seconds=300)
