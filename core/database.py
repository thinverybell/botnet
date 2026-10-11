"""core/database.py - File-based JSON storage with atomic write"""
import json, os, time, shutil, threading
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable
from copy import deepcopy

class Database:
    def __init__(self, path: str = "data"):
        self.path = Path(path)
        self.path.mkdir(parents=True, exist_ok=True)
        (self.path / "backup").mkdir(exist_ok=True)
        self._locks: Dict[str, threading.RLock] = {}
        self._cache: Dict[str, List[Dict]] = {}
        self._glock = threading.RLock()

    def _tpath(self, table: str) -> Path:
        return self.path / f"{table}.json"

    def _lock(self, table: str) -> threading.RLock:
        with self._glock:
            if table not in self._locks:
                self._locks[table] = threading.RLock()
            return self._locks[table]

    def _atomic_write(self, table: str, data: List[Dict]):
        final = self._tpath(table)
        tmp = final.with_suffix(".json.tmp")
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            f.flush(); os.fsync(f.fileno())
        tmp.replace(final)

    def load(self, table: str) -> List[Dict]:
        with self._lock(table):
            if table in self._cache:
                return deepcopy(self._cache[table])
            p = self._tpath(table)
            if not p.exists():
                self._cache[table] = []; return []
            try:
                data = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(data, list): data = []
            except Exception:
                data = []
            self._cache[table] = data
            return deepcopy(data)

    def save(self, table: str):
        with self._lock(table):
            data = self._cache.get(table, [])
            src = self._tpath(table)
            if src.exists():
                ts = int(time.time())
                shutil.copy2(src, self.path / "backup" / f"{table}_{ts}.json")
            self._atomic_write(table, data)

    def insert(self, table: str, record: Dict) -> Dict:
        with self._lock(table):
            data = self.load(table)
            if "id" not in record:
                record["id"] = max((r.get("id", 0) for r in data), default=0) + 1
            record.setdefault("created_at", time.time())
            data.append(record)
            self._cache[table] = data
            self.save(table)
            return deepcopy(record)

    def update(self, table: str, id_: int, record: Dict) -> Optional[Dict]:
        with self._lock(table):
            data = self.load(table)
            for i, r in enumerate(data):
                if r.get("id") == id_:
                    record["id"] = id_
                    record["updated_at"] = time.time()
                    data[i] = {**r, **record}
                    self._cache[table] = data
                    self.save(table)
                    return deepcopy(data[i])
            return None

    def delete(self, table: str, id_: int) -> bool:
        with self._lock(table):
            data = self.load(table)
            new = [r for r in data if r.get("id") != id_]
            if len(new) == len(data): return False
            self._cache[table] = new
            self.save(table)
            return True

    def find(self, table: str, filt: Dict) -> List[Dict]:
        return [deepcopy(r) for r in self.load(table)
                if all(r.get(k) == v for k, v in filt.items())]

    def find_all(self, table: str) -> List[Dict]:
        return self.load(table)

    def find_one(self, table: str, filt: Dict) -> Optional[Dict]:
        r = self.find(table, filt)
        return r[0] if r else None

    def count(self, table: str) -> int:
        return len(self.load(table))

    def clear(self, table: str):
        with self._lock(table):
            self._cache[table] = []
            self.save(table)

    def paginate(self, table: str, page: int = 1, size: int = 50) -> Dict:
        data = self.load(table)
        total = len(data)
        start = (page - 1) * size
        return {"data": deepcopy(data[start:start+size]), "page": page,
                "size": size, "total": total, "pages": (total+size-1)//size if size else 0}

    def search(self, table: str, query: str) -> List[Dict]:
        q = query.lower()
        out = []
        for r in self.load(table):
            if any(isinstance(v, str) and q in v.lower() for v in r.values()):
                out.append(deepcopy(r))
        return out

    def export(self, table: str, fmt: str = "json") -> str:
        data = self.load(table)
        out = self.path / f"export_{table}_{int(time.time())}.{fmt}"
        out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        return str(out)

    def transaction(self, callback: Callable) -> Any:
        snap = {t: deepcopy(d) for t, d in self._cache.items()}
        try:
            return callback(self)
        except Exception:
            self._cache = snap
            raise
