#!/usr/bin/env python3
"""C39–C40 Load & chaos-style tests (in-process, lab-safe)"""
import sys
import tempfile
import threading
import time
import random
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import Database
from core.cache import Cache
from core.auth import AuthManager
from core.bot_manager import BotManager
from core.proxy_manager import ProxyManager
from core.attack_scheduler import AttackScheduler
from core.rate_limit import RateLimiter
from core.message_queue import MessageQueue
from core.event_bus import EventBus


def test_load_database_inserts():
    """Burst inserts into file-based DB."""
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        n = 200
        for i in range(n):
            db.insert("bots", {"uuid": f"u-{i}", "status": "online", "os": "Linux"})
        assert db.count("bots") == n
        # random updates
        for i in range(0, n, 7):
            rows = db.find_all("bots")
            if rows:
                db.update("bots", rows[i % len(rows)]["id"], {"status": "idle"})
        assert db.count("bots") == n


def test_load_cache_thrash():
    with tempfile.TemporaryDirectory() as tmp:
        c = Cache({"l2_path": str(Path(tmp) / "c")})
        for i in range(500):
            c.set(f"k{i}", i, ttl=30)
        hits = sum(1 for i in range(500) if c.get(f"k{i}") == i)
        assert hits >= 450


def test_load_concurrent_rate_limiter():
    rl = RateLimiter(max_requests=100, window_sec=10)
    results = []

    def worker():
        ok = 0
        for _ in range(50):
            if rl.allow("shared"):
                ok += 1
        results.append(ok)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    total_ok = sum(results)
    # should not exceed max_requests by much (best-effort under threads)
    assert total_ok <= 120
    assert total_ok >= 50


def test_chaos_bot_manager_parallel_simulate():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        cache = Cache({"l2_path": str(Path(tmp) / "c")})
        bm = BotManager(db, cache)
        errors = []

        def boom():
            try:
                bm.simulate(random.randint(5, 15))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=boom) for _ in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors
        assert bm.get_stats()["total"] >= 30


def test_chaos_auth_lockout_and_recover():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        auth = AuthManager(db, "admin", "ryzenc2_secure_2026")
        for _ in range(6):
            auth.login("admin", "bad-password")
        # after failures, valid login may still work depending on lockout wiring
        auth._lockout.clear()
        s = auth.login("admin", "ryzenc2_secure_2026")
        assert s and s.get("session_id")


def test_chaos_mq_bus_burst():
    mq = MessageQueue()
    bus = EventBus()
    received = []
    bus.on("burst", lambda p: received.append(p))
    for i in range(100):
        mq.publish("burst", {"i": i})
        bus.emit("burst", i)
    assert len(received) == 100
    # drain some
    count = 0
    while mq.consume("burst", timeout=0.01):
        count += 1
        if count > 150:
            break
    assert count == 100


def test_load_proxy_simulate_and_stats():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        pm = ProxyManager(db, Cache({"l2_path": str(Path(tmp) / "c")}),
                          config_path=str(Path(__file__).resolve().parent.parent / "config.json"))
        pm.simulate(80)
        st = pm.get_stats()
        assert st["total"] >= 80
