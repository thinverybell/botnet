"""bot/anti_vm.py — lightweight VM detection heuristics (lab)"""
import os
import platform
import re
from pathlib import Path
from typing import Dict, List


def _read(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8", errors="ignore").lower()
    except Exception:
        return ""


def is_vm() -> bool:
    return detect().get("is_vm", False)


def detect() -> Dict:
    signals: List[str] = []
    system = platform.system().lower()
    # DMI / sysfs (Linux)
    if system == "linux":
        for p in ["/sys/class/dmi/id/product_name", "/sys/class/dmi/id/sys_vendor",
                  "/sys/class/dmi/id/board_vendor", "/proc/scsi/scsi", "/proc/cpuinfo"]:
            data = _read(p)
            for kw in ("vmware", "virtualbox", "qemu", "kvm", "xen", "bochs", "parallels", "hyper-v", "microsoft corporation"):
                if kw in data:
                    signals.append(f"{p}:{kw}")
        # common virtio / hypervisor flag
        cpu = _read("/proc/cpuinfo")
        if "hypervisor" in cpu:
            signals.append("cpuinfo:hypervisor")
    # macOS
    if system == "darwin":
        import subprocess
        try:
            out = subprocess.check_output(["sysctl", "-n", "machdep.cpu.features"], stderr=subprocess.DEVNULL).decode().lower()
            if "vmm" in out:
                signals.append("sysctl:vmm")
        except Exception:
            pass
    # Windows
    if system == "windows":
        for envk in ("SESSIONNAME",):
            if "RDP" in os.environ.get(envk, ""):
                signals.append("session:rdp")
        try:
            import subprocess
            out = subprocess.check_output(["wmic", "computersystem", "get", "model"], stderr=subprocess.DEVNULL, timeout=3).decode().lower()
            for kw in ("virtual", "vmware", "virtualbox", "kvm", "xen"):
                if kw in out:
                    signals.append(f"wmic:{kw}")
        except Exception:
            pass
    # generic MAC prefixes (weak signal)
    return {
        "is_vm": len(signals) > 0,
        "signals": signals,
        "os": platform.system(),
    }
