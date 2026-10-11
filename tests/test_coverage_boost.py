#!/usr/bin/env python3
import sys, tempfile, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import Database
from core.cache import Cache
from core.auth import AuthManager, totp_at
from core.bot_manager import BotManager
from core.attack_scheduler import AttackScheduler
from core.proxy_manager import ProxyManager
from core.logger import Logger
from core.health_check import HealthCheck
from core.analytics_engine import AnalyticsEngine
from core.ai_engine import AIEngine
from core.security import SecurityManager
from core.utils import format_bytes, format_number, format_datetime
from core.realtime import HUB
from core.anti_scan import is_sensitive_path

def test_attack_scheduler_lifecycle():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        cache = Cache({"l2_path": tmp+"/c"})
        bm = BotManager(db, cache)
        bm.simulate(5)
        pm = ProxyManager(db, cache, config_path=str(Path(__file__).resolve().parent.parent/"config.json"))
        am = AttackScheduler(db, cache, bm, pm)
        a = am.create_attack({"method":"UDP-FLOOD","target_ip":"1.2.3.4","target_port":80,"duration":5,"threads":10})
        assert a["id"]
        am.start_attack(a["id"])
        running = am.get_running_attacks()
        assert isinstance(running, list)
        am.stop_attack(a["id"])
        if hasattr(am, "stop_all"):
            am.stop_all()
        time.sleep(0.05)
        st = am.get_stats()
        assert "total" in st or "running" in st

def test_logger_and_health():
    with tempfile.TemporaryDirectory() as tmp:
        log = Logger({"log_path": str(Path(tmp)/"t.log"), "level": "INFO"})
        log.info("hello")
        h = HealthCheck(tmp, tmp)
        assert h.check()["status"] == "healthy"

def test_analytics_ai_security_utils():
    ae = AnalyticsEngine()
    if hasattr(ae, "record_event"):
        ae.record_event("x", {})
    if hasattr(ae, "get_summary"):
        ae.get_summary()
    ai = AIEngine()
    ai.chat("hi")
    ai.bypass({"type":"aws"})
    sm = SecurityManager()
    assert format_bytes(2048)
    assert format_number(1000)
    assert format_datetime(time.time())

def test_realtime_hub():
    q = HUB.subscribe("t")
    HUB.publish("t", {"ok": True})
    msg = q.get(timeout=1)
    assert msg["ok"] is True
    HUB.unsubscribe("t", q)

def test_proxy_check_one():
    with tempfile.TemporaryDirectory() as tmp:
        pm = ProxyManager(config_path=str(Path(__file__).resolve().parent.parent/"config.json"))
        from core.proxy_manager import Proxy
        p = Proxy("127.0.0.1", 1, 5)  # closed port -> dead
        pm.check_proxy(p, timeout=0.3)
        assert p.last_check is not None
