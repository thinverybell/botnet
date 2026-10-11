"""core/security.py - Security utilities"""
import time, hashlib, secrets
from typing import Dict, List, Optional, Set

class SecurityManager:
    def __init__(self):
        self._blacklist: Set[str] = set()
        self._rate: Dict[str, List[float]] = {}
        self._audit: List[Dict] = []

    def blacklist_ip(self, ip: str):
        self._blacklist.add(ip)
        self.audit("blacklist", {"ip": ip})

    def unblacklist_ip(self, ip: str):
        self._blacklist.discard(ip)

    def is_blacklisted(self, ip: str) -> bool:
        return ip in self._blacklist

    def check_rate(self, key: str, limit: int = 100, window: int = 60) -> bool:
        """Return True if under limit."""
        now = time.time()
        bucket = self._rate.setdefault(key, [])
        self._rate[key] = [t for t in bucket if now - t < window]
        if len(self._rate[key]) >= limit:
            return False
        self._rate[key].append(now)
        return True

    def audit(self, action: str, data: Optional[Dict] = None):
        self._audit.append({"ts": time.time(), "action": action, "data": data or {}})
        if len(self._audit) > 10000:
            self._audit = self._audit[-5000:]

    def get_audit(self, limit: int = 50) -> List[Dict]:
        return self._audit[-limit:]

    def generate_api_key(self) -> str:
        return secrets.token_hex(32)

    def hash_api_key(self, key: str) -> str:
        return hashlib.sha256(key.encode()).hexdigest()
