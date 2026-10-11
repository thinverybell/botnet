"""
Geo lookup with optional MaxMind GeoLite2 City/Country DB.
Falls back to prefix hints if maxminddb / geoip2 not installed or DB missing.

Env:
  MAXMIND_DB_PATH=/path/to/GeoLite2-Country.mmdb
Or place file at data/GeoLite2-Country.mmdb
"""
import os
from pathlib import Path
from typing import Optional, Dict

# reuse hint map
from proxy.proxy_geo import guess_country, COUNTRY_HINTS

_reader = None
_reader_failed = False


def _get_reader():
    global _reader, _reader_failed
    if _reader is not None or _reader_failed:
        return _reader
    db_path = os.getenv("MAXMIND_DB_PATH", "")
    candidates = []
    if db_path:
        candidates.append(Path(db_path))
    candidates.extend([
        Path("data/GeoLite2-Country.mmdb"),
        Path("data/GeoLite2-City.mmdb"),
        Path("/usr/share/GeoIP/GeoLite2-Country.mmdb"),
    ])
    try:
        import maxminddb  # type: ignore
    except ImportError:
        _reader_failed = True
        return None
    for c in candidates:
        if c.is_file():
            try:
                _reader = maxminddb.open_database(str(c))
                return _reader
            except Exception:
                continue
    _reader_failed = True
    return None


class GeoLookup:
    def __init__(self):
        self.reader = _get_reader()

    @property
    def maxmind_ready(self) -> bool:
        return self.reader is not None

    def country(self, ip: str) -> str:
        if not ip:
            return "XX"
        if self.reader:
            try:
                rec = self.reader.get(ip)
                if rec:
                    # country.iso_code or registered_country
                    cc = None
                    if "country" in rec and rec["country"]:
                        cc = rec["country"].get("iso_code")
                    if not cc and "registered_country" in rec:
                        cc = (rec.get("registered_country") or {}).get("iso_code")
                    if cc:
                        return str(cc).upper()
            except Exception:
                pass
        return guess_country(ip)

    def lookup(self, ip: str) -> Dict:
        cc = self.country(ip)
        return {
            "ip": ip,
            "country": cc,
            "source": "maxmind" if self.maxmind_ready else "hint",
        }

    def status(self) -> Dict:
        return {
            "maxmind_ready": self.maxmind_ready,
            "hint": "pip install maxminddb && download GeoLite2-Country.mmdb to data/",
            "env": "MAXMIND_DB_PATH",
        }
