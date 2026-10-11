"""core/plugin_manager.py"""
import json
from pathlib import Path
from typing import Dict, List, Optional

class PluginManager:
    def __init__(self, plugin_dir: str = "plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugin_dir.mkdir(parents=True, exist_ok=True)
        self._plugins: Dict[str, Dict] = {}

    def discover(self) -> List[str]:
        found = []
        for d in self.plugin_dir.iterdir():
            if d.is_dir() and (d / "plugin.py").exists():
                cfg = {}
                cp = d / "config.json"
                if cp.exists():
                    try: cfg = json.loads(cp.read_text(encoding="utf-8"))
                    except: pass
                self._plugins[d.name] = {"path": str(d), "config": cfg, "enabled": cfg.get("enabled", True)}
                found.append(d.name)
        return found

    def list_plugins(self) -> Dict[str, Dict]:
        return dict(self._plugins)

    def enable(self, name: str) -> bool:
        if name in self._plugins:
            self._plugins[name]["enabled"] = True
            return True
        return False

    def disable(self, name: str) -> bool:
        if name in self._plugins:
            self._plugins[name]["enabled"] = False
            return True
        return False

    def get(self, name: str) -> Optional[Dict]:
        return self._plugins.get(name)
