"""core/service_mesh.py — lightweight service registry (Istio-ready interface)"""
import time
from typing import Dict, Any, Optional

class ServiceMesh:
    def __init__(self):
        self._services: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, host: str, port: int, meta: Dict = None):
        self._services[name] = {
            "name": name, "host": host, "port": port,
            "meta": meta or {}, "registered_at": time.time(), "healthy": True,
        }

    def deregister(self, name: str):
        self._services.pop(name, None)

    def resolve(self, name: str) -> Optional[Dict]:
        return self._services.get(name)

    def list_services(self):
        return list(self._services.values())

    def heartbeat(self, name: str):
        if name in self._services:
            self._services[name]["last_hb"] = time.time()
            self._services[name]["healthy"] = True

MESH = ServiceMesh()
# default local services
MESH.register("api", "127.0.0.1", 8080, {"role": "panel"})
MESH.register("panel", "127.0.0.1", 5000, {"role": "cli"})
