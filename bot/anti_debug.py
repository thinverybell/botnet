"""bot/anti_debug.py — debugger presence heuristics (lab)"""
import os
import sys
from typing import Dict, List


def is_debugged() -> bool:
    return detect().get("is_debugged", False)


def detect() -> Dict:
    signals: List[str] = []
    # TracerPid (Linux)
    try:
        with open("/proc/self/status", encoding="utf-8") as f:
            for line in f:
                if line.startswith("TracerPid:"):
                    pid = int(line.split()[1])
                    if pid != 0:
                        signals.append(f"TracerPid={pid}")
    except Exception:
        pass
    # sys.gettrace
    if sys.gettrace() is not None:
        signals.append("sys.gettrace")
    # common env
    for k in ("PYTHONBREAKPOINT", "LINEPROF", "PYCHARM_HOSTED"):
        if os.environ.get(k):
            signals.append(f"env:{k}")
    return {"is_debugged": len(signals) > 0, "signals": signals}
