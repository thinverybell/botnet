#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.proxy_manager import ProxyManager, Proxy
from proxy.proxy_chain import build_chain, format_chain, chain_to_urls
from proxy.proxy_geo import guess_country, filter_by_country, annotate_geo
from proxy.proxy_rotator import ProxyRotator
from proxy.proxy_scorer import score, rank
from proxy.proxy_checker import validate_proxy, check_proxy
from proxy.proxy_forensics import audit_snapshot


def test_proxy_auth_parse():
    pm = ProxyManager(config_path="config.json")
    parsed = pm.parse_proxy("socks5://user:pass@10.0.0.1:1080\n", 5)
    assert len(parsed) == 1
    assert parsed[0].user == "user"
    assert parsed[0].password == "pass"
    d = parsed[0].as_request()
    assert "user:pass@" in d["http"]


def test_chain_and_rotator():
    proxies = [Proxy(f"1.2.3.{i}", 1080, 5) for i in range(5)]
    chain = build_chain(proxies, 3)
    assert len(chain) == 3
    assert "->" in format_chain(chain)
    rot = ProxyRotator(proxies, strategy="sticky")
    a = rot.get_next()
    b = rot.get_next()
    assert a is b  # sticky
    rot.mark_failure(a, max_failures=1)
    # may remove after failures


def test_geo_and_score():
    assert guess_country("8.8.8.8") in ("US", "XX")
    ps = [Proxy("8.8.8.8", 80, 1), Proxy("171.1.1.1", 80, 1)]
    annotate_geo(ps)
    assert score(latency=50, reliability=0.9) > score(latency=900, reliability=0.2)
    assert validate_proxy("1.2.3.4:8080")
    r = check_proxy(Proxy("127.0.0.1", 1, 5), timeout=0.2)
    assert "alive" in r
    assert audit_snapshot([{"alive": True}, {"alive": False}])["total"] == 2
