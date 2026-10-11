"""core/logger.py"""
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

class Logger:
    LEVELS = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
    def __init__(self, config: Optional[Dict] = None):
        cfg = config or {}
        self.log_path = Path(cfg.get("log_path", "logs/panel.log"))
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.level = cfg.get("level", "INFO")
        self._idx = self.LEVELS.index(self.level) if self.level in self.LEVELS else 1

    def _ok(self, level): 
        try: return self.LEVELS.index(level) >= self._idx
        except ValueError: return True

    def log(self, level: str, message: str, **kw):
        if not self._ok(level): return
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        extra = " ".join(f"{k}={v}" for k,v in kw.items())
        line = f"[{ts}] [{level}] {message} {extra}".strip()
        with open(self.log_path, "a", encoding="utf-8") as f: f.write(line+"\n")
        colors = {"DEBUG":"\033[90m","INFO":"\033[36m","WARN":"\033[33m","ERROR":"\033[31m","FATAL":"\033[91m"}
        print(f"{colors.get(level,'')}{line}\033[0m")

    def debug(self, m, **k): self.log("DEBUG", m, **k)
    def info(self, m, **k): self.log("INFO", m, **k)
    def warn(self, m, **k): self.log("WARN", m, **k)
    def error(self, m, **k): self.log("ERROR", m, **k)
    def fatal(self, m, **k): self.log("FATAL", m, **k)

    def get_logs(self, limit=50) -> List[str]:
        if not self.log_path.exists(): return []
        return self.log_path.read_text(encoding="utf-8").strip().splitlines()[-limit:]

    def clear(self):
        if self.log_path.exists(): self.log_path.write_text("")
