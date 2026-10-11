"""proxy/proxy_chain.py — N-hop proxy chains"""
from typing import List, Any, Optional
import random


def build_chain(proxies: list, hops: int = 2) -> list:
    """Return up to N proxies for chaining (exit last)."""
    if not proxies:
        return []
    hops = max(1, min(hops, len(proxies)))
    if len(proxies) <= hops:
        return list(proxies)
    return random.sample(list(proxies), hops)


def chain_to_urls(chain: list) -> List[str]:
    urls = []
    for p in chain:
        if isinstance(p, dict):
            proto = p.get("protocol") or {1: "http", 4: "socks4", 5: "socks5"}.get(p.get("type"), "socks5")
            user, password = p.get("user"), p.get("password")
            host, port = p.get("address"), p.get("port")
        else:
            proto = getattr(p, "protocol", None) or {1: "http", 4: "socks4", 5: "socks5"}.get(getattr(p, "type", 5), "socks5")
            user, password = getattr(p, "user", None), getattr(p, "password", None)
            host, port = getattr(p, "address", None), getattr(p, "port", None)
        auth = f"{user}:{password}@" if user and password else ""
        urls.append(f"{proto}://{auth}{host}:{port}")
    return urls


def format_chain(chain: list) -> str:
    return " -> ".join(chain_to_urls(chain))
