"""core/backup_manager.py"""
import time, shutil, tarfile
from pathlib import Path
from typing import List

class BackupManager:
    def __init__(self, data_dir: str = "data", backup_dir: str = "data/backup"):
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def backup(self) -> str:
        ts = time.strftime("%Y%m%d_%H%M%S")
        out = self.backup_dir / f"backup_{ts}.tar.gz"
        with tarfile.open(out, "w:gz") as tar:
            for f in self.data_dir.glob("*.json"):
                tar.add(f, arcname=f.name)
        return str(out)

    def list_backups(self) -> List[str]:
        return sorted([str(p) for p in self.backup_dir.glob("backup_*.tar.gz")], reverse=True)

    def restore(self, backup_path: str) -> bool:
        p = Path(backup_path)
        if not p.exists(): return False
        with tarfile.open(p, "r:gz") as tar:
            tar.extractall(self.data_dir)
        return True
