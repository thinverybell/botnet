"""core/migration_manager.py"""
from pathlib import Path
from typing import List

class MigrationManager:
    def __init__(self, migrations_dir: str = "data/migrations"):
        self.dir = Path(migrations_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self._applied: List[str] = []

    def list_pending(self) -> List[str]:
        return [p.name for p in sorted(self.dir.glob("*.py")) if p.name not in self._applied]

    def apply(self, name: str) -> bool:
        # Placeholder: real migrations would exec migration scripts
        self._applied.append(name)
        return True

    def applied(self) -> List[str]:
        return list(self._applied)
