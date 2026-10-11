#!/usr/bin/env python3
import sys
import tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.database import Database
from core.cache import Cache
from core.proxy_manager import ProxyManager, Proxy


def test_parse_and_add():
    with tempfile.TemporaryDirectory() as tmp:
        db = Database(tmp)
        pm = ProxyManager(db, Cache({"l2_path": tmp + "/c"}), config_path=str(Path(__file__).resolve().parent.parent / "config.json"))
        assert len(pm.providers) > 10
        n = pm.simulate(5)
        assert n == 5
        assert pm.get_stats()["total"] >= 5
        p = Proxy("1.2.3.4", 8080, 1)
        assert "http" in p.as_request()["http"]


def test_parse_line():
    with tempfile.TemporaryDirectory() as tmp:
        pm = ProxyManager(config_path=str(Path(__file__).resolve().parent.parent / "config.json"))
        parsed = pm.parse_proxy("1.1.1.1:1080\nsocks5://2.2.2.2:9050\n# comment\n", 5)
        assert len(parsed) == 2
