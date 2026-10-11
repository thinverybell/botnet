"""core/command_parser.py"""
from typing import Dict, List, Optional, Callable, Any

class CommandParser:
    def __init__(self):
        self._handlers: Dict[str, Callable] = {}
        self._help: Dict[str, str] = {}

    def register_command(self, name: str, handler: Callable, help_text: str = ""):
        self._handlers[name.lower()] = handler
        self._help[name.lower()] = help_text or name

    def parse(self, command: str) -> Dict[str, Any]:
        parts = command.strip().split()
        if not parts:
            return {"cmd": "", "args": [], "flags": {}, "raw": command}
        cmd, args, flags, i = parts[0].lower(), [], {}, 1
        while i < len(parts):
            p = parts[i]
            if p.startswith("--"):
                key = p[2:]
                if i+1 < len(parts) and not parts[i+1].startswith("-"):
                    flags[key] = parts[i+1]; i += 2
                else:
                    flags[key] = True; i += 1
            elif p.startswith("-") and len(p)==2:
                key = p[1]
                if i+1 < len(parts) and not parts[i+1].startswith("-"):
                    flags[key] = parts[i+1]; i += 2
                else:
                    flags[key] = True; i += 1
            else:
                args.append(p); i += 1
        return {"cmd": cmd, "args": args, "flags": flags, "raw": command}

    def execute(self, command: str) -> Any:
        p = self.parse(command)
        h = self._handlers.get(p["cmd"])
        if not h: raise ValueError(f"Unknown: {p['cmd']}")
        return h(p["args"], p["flags"])

    def get_commands(self) -> List[str]:
        return sorted(self._handlers.keys())

    def get_help(self, command: Optional[str] = None) -> str:
        if command: return self._help.get(command.lower(), "No help")
        return "\n".join(f"  {n:<16} {self._help.get(n,'')}" for n in self.get_commands())
