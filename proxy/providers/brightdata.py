"""
Bright Data (formerly Luminati) residential / datacenter proxy adapter.
Requires env or config:
  BRIGHTDATA_CUSTOMER, BRIGHTDATA_PASSWORD, BRIGHTDATA_ZONE (optional)
Docs: https://docs.brightdata.com/
Does NOT call API without credentials — builds proxy URLs only.
"""
import os
from typing import List, Dict, Optional


class BrightDataProvider:
    def __init__(self, customer: str = None, password: str = None, zone: str = None, host: str = None, port: int = 22225):
        self.customer = customer or os.getenv("BRIGHTDATA_CUSTOMER", "")
        self.password = password or os.getenv("BRIGHTDATA_PASSWORD", "")
        self.zone = zone or os.getenv("BRIGHTDATA_ZONE", "residential")
        self.host = host or os.getenv("BRIGHTDATA_HOST", "brd.superproxy.io")
        self.port = int(port or os.getenv("BRIGHTDATA_PORT", "22225"))

    @property
    def configured(self) -> bool:
        return bool(self.customer and self.password)

    def build_proxy(self, country: str = None, session_id: str = None) -> Optional[Dict]:
        if not self.configured:
            return None
        # username format: brd-customer-<CUSTOMER>-zone-<ZONE>[-country-<CC>][-session-<SID>]
        user = f"brd-customer-{self.customer}-zone-{self.zone}"
        if country:
            user += f"-country-{country.lower()}"
        if session_id:
            user += f"-session-{session_id}"
        return {
            "address": self.host,
            "port": self.port,
            "type": 1,  # HTTP
            "protocol": "http",
            "user": user,
            "password": self.password,
            "provider": "brightdata",
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
                sid = f"s{i}" if sessions > 1 else None
                p = self.build_proxy(country=cc, session_id=sid)
                if p:
                    out.append(p)
        return out

    def status(self) -> Dict:
        return {
            "provider": "brightdata",
            "configured": self.configured,
            "host": self.host,
            "port": self.port,
            "zone": self.zone,
            "hint": "Set BRIGHTDATA_CUSTOMER + BRIGHTDATA_PASSWORD (+ optional ZONE)",
        }
