"""bot/attack_l4.py — L4 lab simulator (no packet flood)"""
import random
import time
from typing import Dict, Any, Optional, List
from core.methods import L4_METHODS, is_l4


def list_l4() -> List[str]:
    return list(L4_METHODS)


def simulate_l4(
    method: str,
    target_ip: str,
    target_port: int,
    duration: int = 5,
    threads: int = 10,
    proxy: Optional[Dict] = None,
) -> Dict[str, Any]:
    """Simulate L4 metrics only — does not send attack traffic."""
    method = method.upper().replace("_", "-")
    if not is_l4(method):
        return {"ok": False, "error": "not an L4 method", "method": method}
    t0 = time.time()
    # synthetic metrics
    pps = threads * random.randint(50, 200)
    bps = pps * random.randint(64, 512)
    proxy_str = None
    if proxy:
        if isinstance(proxy, dict):
            proxy_str = f"{proxy.get('protocol', 'socks5')}://{proxy.get('address')}:{proxy.get('port')}"
        else:
            proxy_str = str(proxy)
    # sleep small amount to mimic work window (capped)
    time.sleep(min(0.2, max(0.01, duration / 100)))
    return {
        "ok": True,
        "layer": "L4",
        "method": method,
        "target": f"{target_ip}:{target_port}",
        "duration": duration,
        "threads": threads,
        "proxy": proxy_str,
        "simulated_pps": pps,
        "simulated_bps": bps,
        "elapsed_ms": int((time.time() - t0) * 1000),
        "note": "LAB SIMULATION — no packets sent",
    }
