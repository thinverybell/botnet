"""core/cache.py - Multi-tier L1/L2 cache"""
import time, json, threading
from pathlib import Path
from typing import Any, Optional, Dict
from collections import OrderedDict

class Cache:
    def __init__(self, config: Optional[Dict] = None):
        cfg = config or {}
        self.l1_max = cfg.get("l1_max", 10000)
        self.l1_ttl = cfg.get("l1_ttl", 60)
        self.l2_path = Path(cfg.get("l2_path", "data/cache"))
        self.l2_path.mkdir(parents=True, exist_ok=True)
        self.l2_ttl = cfg.get("l2_ttl", 300)
        self._l1: OrderedDict = OrderedDict()
        self._lock = threading.RLock()
        self._stats = {"hits": 0, "misses": 0, "evictions": 0, "sets": 0}

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            if key in self._l1:
                e = self._l1[key]
                if e["expires"] > time.time():
                    self._l1.move_to_end(key)
                    self._stats["hits"] += 1
                    return e["value"]
                del self._l1[key]
            p = self.l2_path / f"{key}.json"
            if p.exists():
                try:
                    e = json.loads(p.read_text(encoding="utf-8"))
                    if e.get("expires", 0) > time.time():
                        self._set_l1(key, e["value"], e["expires"] - time.time())
                        self._stats["hits"] += 1
                        return e["value"]
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
            self._stats["misses"] += 1
            return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        with self._lock:
            ttl = ttl if ttl is not None else self.l1_ttl
            self._set_l1(key, value, ttl)
            try:
                (self.l2_path / f"{key}.json").write_text(
                    json.dumps({"value": value, "expires": time.time() + max(ttl, self.l2_ttl)}),
                    encoding="utf-8")
            except Exception:
                pass
            self._stats["sets"] += 1

    def _set_l1(self, key, value, ttl):
        if len(self._l1) >= self.l1_max:
            self._l1.popitem(last=False)
            self._stats["evictions"] += 1
        self._l1[key] = {"value": value, "expires": time.time() + ttl}
        self._l1.move_to_end(key)

    def delete(self, key: str):
        with self._lock:
            self._l1.pop(key, None)
            (self.l2_path / f"{key}.json").unlink(missing_ok=True)

    def clear(self):
        with self._lock:
            self._l1.clear()
            for f in self.l2_path.glob("*.json"):
                f.unlink(missing_ok=True)

    def invalidate(self, pattern: str) -> int:
        n = 0
        with self._lock:
            for k in [k for k in self._l1 if pattern in k]:
                del self._l1[k]; n += 1
            for f in self.l2_path.glob("*.json"):
                if pattern in f.stem:
                    f.unlink(missing_ok=True); n += 1
        return n

    def warmup(self):
        with self._lock:
            for f in self.l2_path.glob("*.json"):
                try:
                    e = json.loads(f.read_text(encoding="utf-8"))
                    if e.get("expires", 0) > time.time():
                        self._set_l1(f.stem, e["value"], e["expires"] - time.time())
                except Exception:
                    pass

    def get_stats(self) -> Dict:
        with self._lock:
            t = self._stats["hits"] + self._stats["misses"]
            return {**self._stats, "l1_size": len(self._l1),
                    "hit_rate": round(self._stats["hits"] / t, 4) if t else 0}
