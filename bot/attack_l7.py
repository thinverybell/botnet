"""bot/attack_l7.py — L7 lab simulator (no HTTP flood)"""
import random
import time
from typing import Dict, Any, Optional, List
from core.methods import L7_METHODS, is_l7


def list_l7() -> List[str]:
    return list(L7_METHODS)


def simulate_l7(
    method: str,
    target_url: str,
    duration: int = 5,
    threads: int = 10,
    proxy: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Simulate L7 metrics only — does not send attack traffic."""
    method = method.upper().replace("_", "-")
    if not is_l7(method):
        return {"ok": False, "error": "not an L7 method", "method": method}
    t0 = time.time()
    rps = threads * random.randint(5, 40)
    proxy_str = None
    if proxy:
        if isinstance(proxy, dict):
            auth = ""
            if proxy.get("user") and proxy.get("password"):
                auth = f"{proxy['user']}:{proxy['password']}@"
            proxy_str = f"{proxy.get('protocol', 'http')}://{auth}{proxy.get('address')}:{proxy.get('port')}"
        else:
            proxy_str = str(proxy)
    time.sleep(min(0.2, max(0.01, duration / 100)))
    return {
        "ok": True,
        "layer": "L7",
        "method": method,
        "target": target_url,
        "duration": duration,
        "threads": threads,
        "proxy": proxy_str,
        "simulated_rps": rps,
        "elapsed_ms": int((time.time() - t0) * 1000),
        "note": "LAB SIMULATION — no HTTP flood sent",
    }
