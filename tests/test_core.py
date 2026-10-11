#!/usr/bin/env python3
"""Core module tests — database, cache, auth, methods"""
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.database import Database
from core.cache import Cache
from core.auth import AuthManager, totp_at, verify_totp
from core.methods import ALL_METHODS, L4_METHODS, L7_METHODS, method_info, is_l4, is_l7
from core.rate_limit import RateLimiter
from core.bypass_engine import plan_bypass, detect_vendor
from core.service_mesh import MESH
from core.message_queue import MessageQueue
from core.event_bus import EventBus


def test_database_crud():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        r = db.insert("users", {"username": "t1"})
        assert r["id"] == 1
        assert db.count("users") == 1
        db.update("users", 1, {"username": "t2"})
        assert db.find_one("users", {"username": "t2"})
        db.delete("users", 1)
        assert db.count("users") == 0


def test_cache_l1():
    with tempfile.TemporaryDirectory() as tmp:
        c = Cache({"l2_path": str(Path(tmp) / "c")})
        c.set("k", "v", ttl=60)
        assert c.get("k") == "v"
        c.delete("k")
        assert c.get("k") is None


def test_auth_login_and_mfa():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        auth = AuthManager(db, "admin", "ryzenc2_secure_2026")
        s = auth.login("admin", "ryzenc2_secure_2026")
        assert s and s.get("session_id")
        assert auth.has_permission(s, "bots:read")
        mfa = auth.enable_mfa("admin")
        assert mfa.get("secret")
        code = totp_at(mfa["secret"])
        assert verify_totp(mfa["secret"], code)
        assert auth.verify_mfa("admin", code)
        # wrong password
        assert auth.login("admin", "wrong") is None


def test_abac_tenant():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        auth = AuthManager(db)
        s = auth.login("admin", "ryzenc2_secure_2026")
        assert auth.check_abac(s, {"tenant_id": "default"})
        assert auth.check_abac(s, {"requires_clearance": "high"}) is False or s.get("role") == "admin"


def test_methods_registry():
    assert len(L4_METHODS) >= 100
    assert len(L7_METHODS) >= 100
    assert len(ALL_METHODS) >= 200
    assert is_l4("UDP-FLOOD")
    assert is_l7("HTTP-FLOOD")
    assert method_info("UDP-FLOOD")["layer"] == "L4"


def test_rate_limiter():
    rl = RateLimiter(max_requests=5, window_sec=60)
    for _ in range(5):
        assert rl.allow("ip1")
    assert rl.allow("ip1") is False
    assert rl.allow("ip2") is True


def test_bypass_engine():
    p = plan_bypass("cloudflare")
    assert p["vendor"] == "cloudflare"
    assert "recommended_methods" in p
    assert detect_vendor({"cf-ray": "abc"}) == "cloudflare"


def test_mesh_mq_bus():
    MESH.register("testsvc", "127.0.0.1", 9999)
    assert MESH.resolve("testsvc")["port"] == 9999
    mq = MessageQueue()
    mq.publish("t", {"a": 1})
    msg = mq.consume("t", timeout=0.5)
    assert msg["payload"]["a"] == 1
    bus = EventBus()
    hit = []
    bus.on("e", lambda p: hit.append(p))
    bus.emit("e", 42)
    assert hit == [42]
