"""core/config_manager.py"""
import json
from pathlib import Path
from typing import Any, Dict, Optional

class ConfigManager:
    def __init__(self, path: str = "data/config.json"):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict = {}
        self.load()

    def load(self):
        if self.path.exists():
            try: self._data = json.loads(self.path.read_text(encoding="utf-8"))
            except: self._data = {}
        else:
            self._data = {}

    def save(self):
        self.path.write_text(json.dumps(self._data, indent=2, ensure_ascii=False), encoding="utf-8")

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self.save()

    def all(self) -> Dict:
        return dict(self._data)
