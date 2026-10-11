"""
Oxylabs residential / datacenter proxy adapter.
Env: OXYLABS_USERNAME, OXYLABS_PASSWORD, OXYLABS_HOST (default pr.oxylabs.io), OXYLABS_PORT (7777)
"""
import os
from typing import List, Dict, Optional


class OxylabsProvider:
    def __init__(self, username: str = None, password: str = None, host: str = None, port: int = 7777):
        self.username = username or os.getenv("OXYLABS_USERNAME", "")
        self.password = password or os.getenv("OXYLABS_PASSWORD", "")
        self.host = host or os.getenv("OXYLABS_HOST", "pr.oxylabs.io")
        self.port = int(port or os.getenv("OXYLABS_PORT", "7777"))

    @property
    def configured(self) -> bool:
        return bool(self.username and self.password)

    def build_proxy(self, country: str = None, session_id: str = None) -> Optional[Dict]:
        if not self.configured:
            return None
        # customer-USER-cc-COUNTRY-sessid-SESSION
        user = self.username
        if country:
            user = f"customer-{self.username}-cc-{country.lower()}"
            if session_id:
                user += f"-sessid-{session_id}"
        elif session_id:
            user = f"customer-{self.username}-sessid-{session_id}"
        return {
            "address": self.host,
            "port": self.port,
            "type": 1,
            "protocol": "http",
            "user": user,
            "password": self.password,
            "provider": "oxylabs",
            "country": (country or "").upper() or None,
            "alive": True,
            "score": 85,
        }

    def list_endpoints(self, countries: List[str] = None, sessions: int = 1) -> List[Dict]:
        if not self.configured:
            return []
        countries = countries or [None]
        out = []
        for cc in countries:
            for i in range(max(1, sessions)):
                sid = f"sess{i}" if sessions > 1 else None
                p = self.build_proxy(country=cc, session_id=sid)
                if p:
                    out.append(p)
        return out

    def status(self) -> Dict:
        return {
            "provider": "oxylabs",
            "configured": self.configured,
            "host": self.host,
            "port": self.port,
            "hint": "Set OXYLABS_USERNAME + OXYLABS_PASSWORD",
        }
