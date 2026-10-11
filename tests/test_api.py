#!/usr/bin/env python3
import sys
import tempfile
import threading
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import Database
from core.cache import Cache
from core.auth import AuthManager
from core.bot_manager import BotManager
from core.proxy_manager import ProxyManager
from core.attack_scheduler import AttackScheduler
from core.ai_engine import AIEngine
from core.health_check import HealthCheck
from core.logger import Logger
from api.server import start_api_server
from api.graphql_api import execute
import urllib.request
import json


def test_graphql_execute():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        cache = Cache({"l2_path": tmp + "/c"})
        bm = BotManager(db, cache)
        bm.simulate(2)
        r = execute("{ bots stats }", {}, {"bot_mgr": bm, "proxy_mgr": None, "attack_mgr": None})
        assert "data" in r
        assert r["data"]["bots"]["count"] == 2
