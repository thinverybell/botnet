"""bot/proxy_rotator.py"""
import random
from typing import List, Optional

class ProxyRotator:
    def __init__(self, proxies: Optional[List[str]] = None):
        self.proxies = proxies or []
        self._idx = 0

    def add(self, proxy: str):
        self.proxies.append(proxy)

    def next(self) -> Optional[str]:
        if not self.proxies: return None
        p = self.proxies[self._idx % len(self.proxies)]
        self._idx += 1
        return p

    def random(self) -> Optional[str]:
        return random.choice(self.proxies) if self.proxies else None
