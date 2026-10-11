#!/usr/bin/env python3
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import Database
from core.cache import Cache
from core.bot_manager import BotManager


def test_simulate_and_register():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        bm = BotManager(db, Cache({"l2_path": tmp + "/c"}))
        bm.simulate(3)
        assert bm.get_stats()["total"] == 3
        b = bm.register({"uuid": "test-uuid-1", "os": "Linux", "arch": "x64"})
        assert b.get("uuid") == "test-uuid-1"
        assert bm.heartbeat("test-uuid-1", {"status": "online"})
