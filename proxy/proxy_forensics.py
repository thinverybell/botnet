"""proxy/proxy_forensics.py — cleanup helpers"""
from pathlib import Path
import time


def cleanup_logs(log_path: str = "logs/proxy.log", keep_lines: int = 5000):
    p = Path(log_path)
    if not p.exists():
        return 0
    lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
    if len(lines) <= keep_lines:
        return 0
    p.write_text("\n".join(lines[-keep_lines:]) + "\n", encoding="utf-8")
    return len(lines) - keep_lines


def wipe_history(pool_path: str = "proxy/proxy_pool.txt"):
    p = Path(pool_path)
    if p.exists():
        p.write_text("", encoding="utf-8")
    return True


def audit_snapshot(proxies: list) -> dict:
    alive = sum(1 for p in proxies if (p.get("alive") if isinstance(p, dict) else getattr(p, "alive", False)))
    return {"ts": time.time(), "total": len(proxies), "alive": alive}
