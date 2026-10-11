#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from bot.payload_generator import generate_python_bot, generate_all, to_b64
from bot.attack_l4 import simulate_l4, list_l4
from bot.attack_l7 import simulate_l7, list_l7
from bot.evasion import full_report, sleep_jitter
from bot.persistence import install_cron, list_methods
from bot.anti_vm import detect as vm_detect
from bot.anti_debug import detect as dbg_detect
from bot.anti_sandbox import detect as sb_detect


def test_payloads():
    py = generate_python_bot("127.0.0.1", 8080, "k")
    assert "BOT_ID" in py and "heartbeat" in py
    allp = generate_all()
    assert "python" in allp and "bash" in allp and "powershell" in allp
    assert to_b64("abc")


def test_simulate_l4_l7_with_proxy():
    proxy = {"protocol": "socks5", "address": "1.2.3.4", "port": 1080}
    r = simulate_l4("UDP-FLOOD", "127.0.0.1", 80, duration=1, threads=5, proxy=proxy)
    assert r["ok"] and r["proxy"] and "LAB" in r["note"]
    r2 = simulate_l7("HTTP-FLOOD", "http://127.0.0.1/", duration=1, proxy=proxy)
    assert r2["ok"] and "LAB" in r2["note"]
    assert len(list_l4()) > 50
    assert len(list_l7()) > 50


def test_evasion_and_persistence_dry_run():
    assert "vm" in full_report()
    assert isinstance(vm_detect()["is_vm"], bool)
    assert isinstance(dbg_detect()["is_debugged"], bool)
    assert isinstance(sb_detect()["is_sandbox"], bool)
    sleep_jitter(0.01, 0.0)
    c = install_cron(apply=False)
    assert c["method"] == "cron" and c["applied"] is False
    assert "cron" in list_methods()
