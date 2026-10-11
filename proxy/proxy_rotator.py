"""proxy/proxy_rotator.py — rotation strategies"""
import random
from typing import List, Optional, Any

STRATEGIES = [
    "round_robin", "random", "least_connections", "least_latency",
    "weighted", "sticky", "geo", "adaptive", "failover",
]


class ProxyRotator:
    def __init__(self, proxies: Optional[List] = None, strategy: str = "random"):
        self.proxies = list(proxies or [])
        self.strategy = strategy if strategy in STRATEGIES else "random"
        self._idx = 0
        self._connections = {}
        self._sticky = None
        self._failures = {}

    def add_proxy(self, proxy):
        self.proxies.append(proxy)

    def remove_proxy(self, proxy):
        if proxy in self.proxies:
            self.proxies.remove(proxy)

    def reset(self):
        self._idx = 0
        self._sticky = None

    def mark_failure(self, proxy, max_failures: int = 3):
        pid = id(proxy)
        self._failures[pid] = self._failures.get(pid, 0) + 1
        if self._failures[pid] >= max_failures and proxy in self.proxies:
            self.proxies.remove(proxy)
            if self._sticky is proxy:
                self._sticky = None

    def mark_success(self, proxy):
        self._failures[id(proxy)] = 0

    def get_next(self) -> Optional[Any]:
        if not self.proxies:
            return None
        s = self.strategy
        if s == "random":
            return random.choice(self.proxies)
        if s == "round_robin":
            p = self.proxies[self._idx % len(self.proxies)]
            self._idx += 1
            return p
        if s == "least_latency":
            def lat(x):
                return x.get("latency", 9999) if isinstance(x, dict) else getattr(x, "latency", 9999)
            return min(self.proxies, key=lat)
        if s == "least_connections":
            def key(p):
                return self._connections.get(id(p), 0)
            p = min(self.proxies, key=key)
            self._connections[id(p)] = self._connections.get(id(p), 0) + 1
            return p
        if s == "sticky":
            if self._sticky is None or self._sticky not in self.proxies:
                self._sticky = random.choice(self.proxies)
            return self._sticky
        if s == "weighted":
            def sc(x):
                return max(1, x.get("score", 50) if isinstance(x, dict) else getattr(x, "score", 50))
            weights = [sc(p) for p in self.proxies]
            return random.choices(self.proxies, weights=weights, k=1)[0]
        if s == "failover":
            # prefer lowest failure count
            def fails(p):
                return self._failures.get(id(p), 0)
            return sorted(self.proxies, key=fails)[0]
        # adaptive / geo fallback
        return random.choice(self.proxies)

    def rotate(self) -> Optional[Any]:
        self._sticky = None
        return self.get_next()

    def get_stats(self) -> dict:
        return {
            "count": len(self.proxies),
            "strategy": self.strategy,
            "index": self._idx,
            "failures": len([1 for v in self._failures.values() if v > 0]),
        }
