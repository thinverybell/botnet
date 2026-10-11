"""proxy/proxy_geo.py — geo filter helpers"""
from typing import List, Dict, Any, Optional

# Lightweight static map for demo (prefix-based); production would use MaxMind etc.
COUNTRY_HINTS = {
    "US": ["3.", "4.", "8.", "13.", "23.", "34.", "44.", "50.", "52.", "54.", "100."],
    "DE": ["5.9.", "46.4.", "78.46.", "85.214."],
    "SG": ["8.9.", "45.76.", "103.253."],
    "JP": ["1.0.", "27.", "49.212.", "103.5."],
    "VN": ["14.", "27.67.", "42.", "103.1.", "113.", "115.", "116.", "117.", "118.", "119.", "171."],
}


def guess_country(ip: str) -> str:
    if not ip:
        return "XX"
    for cc, prefixes in COUNTRY_HINTS.items():
        for p in prefixes:
            if ip.startswith(p):
                return cc
    return "XX"


def filter_by_country(proxies: list, country: str) -> list:
    country = (country or "").upper()
    out = []
    for p in proxies:
        if isinstance(p, dict):
            cc = p.get("country") or guess_country(p.get("address", ""))
            addr = p.get("address", "")
        else:
            cc = getattr(p, "country", None) or guess_country(getattr(p, "address", ""))
            addr = getattr(p, "address", "")
        if cc == country or guess_country(addr) == country:
            out.append(p)
    return out


def annotate_geo(proxies: list) -> list:
    for p in proxies:
        if isinstance(p, dict):
            if not p.get("country"):
                p["country"] = guess_country(p.get("address", ""))
        else:
            if not getattr(p, "country", None):
                setattr(p, "country", guess_country(getattr(p, "address", "")))
    return proxies
