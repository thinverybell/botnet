"""proxy/proxy_checker.py — alive/latency checks"""
import socket
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any, Optional

DEFAULT_TARGETS = [
    "http://httpbin.org/ip",
    "http://api.ipify.org",
    "http://checkip.amazonaws.com",
    "http://icanhazip.com",
]


def check_proxy(proxy, target: Optional[str] = None, timeout: float = 5.0) -> Dict[str, Any]:
    if isinstance(proxy, dict):
        host, port = proxy.get("address"), int(proxy.get("port") or 0)
        user, password = proxy.get("user"), proxy.get("password")
    else:
        host, port = getattr(proxy, "address", None), int(getattr(proxy, "port", 0) or 0)
        user = getattr(proxy, "user", None)
        password = getattr(proxy, "password", None)
    start = time.time()
    alive = False
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(timeout)
        s.connect((host, port))
        s.close()
        alive = True
    except Exception:
        alive = False
    latency = int((time.time() - start) * 1000)
    if latency >= 5000:
        alive = False
    return {
        "address": host,
        "port": port,
        "alive": alive,
        "latency": latency if alive else 0,
        "user": user,
        "password": password,
    }


def check_all(proxies: List, target: Optional[str] = None, timeout: float = 5.0, threads: int = 50) -> List[Dict]:
    results = []
    with ThreadPoolExecutor(max_workers=threads) as ex:
        futs = {ex.submit(check_proxy, p, target, timeout): p for p in proxies}
        for fut in as_completed(futs):
            try:
                results.append(fut.result())
            except Exception:
                pass
    return results


def check_http(proxy, target=None, timeout=5.0):
    return check_proxy(proxy, target, timeout)


def check_socks4(proxy, target=None, timeout=5.0):
    return check_proxy(proxy, target, timeout)


def check_socks5(proxy, target=None, timeout=5.0):
    return check_proxy(proxy, target, timeout)


def measure_latency(proxy, target=None) -> int:
    return int(check_proxy(proxy, target).get("latency") or 0)


def measure_bandwidth(proxy, target=None) -> int:
    return 0


def validate_proxy(proxy_str: str) -> bool:
    try:
        s = proxy_str
        if "://" in s:
            s = s.split("://", 1)[1]
        if "@" in s:
            s = s.rsplit("@", 1)[-1]
        host, port = s.rsplit(":", 1)
        return bool(host) and 1 <= int(port) <= 65535
    except Exception:
        return False
