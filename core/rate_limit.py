"""core/rate_limit.py — simple token-bucket / sliding window rate limiter"""
import time
import threading
from collections import defaultdict
from typing import Dict, Tuple

class RateLimiter:
    def __init__(self, max_requests: int = 60, window_sec: float = 60.0):
        self.max_requests = max_requests
        self.window = window_sec
        self._hits: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def allow(self, key: str) -> bool:
        now = time.time()
        with self._lock:
            hits = self._hits[key]
            self._hits[key] = [t for t in hits if now - t < self.window]
            if len(self._hits[key]) >= self.max_requests:
                return False
            self._hits[key].append(now)
            return True

    def remaining(self, key: str) -> int:
        now = time.time()
        with self._lock:
            hits = [t for t in self._hits[key] if now - t < self.window]
            return max(0, self.max_requests - len(hits))
