"""core/health_check.py"""
import time, os, shutil
from typing import Dict, Any
from pathlib import Path

class HealthCheck:
    def __init__(self, data_dir="data", log_dir="logs"):
        self.data_dir = Path(data_dir)
        self.log_dir = Path(log_dir)
        self._start = time.time()

    def check(self) -> Dict[str, Any]:
        disk = shutil.disk_usage(str(self.data_dir) if self.data_dir.exists() else ".")
        return {
            "status": "healthy",
            "uptime_sec": int(time.time() - self._start),
            "data_dir_exists": self.data_dir.exists(),
            "log_dir_exists": self.log_dir.exists(),
            "disk_free_gb": round(disk.free / (1024**3), 2),
            "disk_total_gb": round(disk.total / (1024**3), 2),
            "pid": os.getpid(),
            "ts": time.time(),
        }

    def ready(self) -> bool:
        return self.data_dir.exists()
