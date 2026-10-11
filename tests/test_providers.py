#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from proxy.providers.brightdata import BrightDataProvider
from proxy.providers.oxylabs import OxylabsProvider
from proxy.providers.tor_i2p import TorProvider, I2PProvider
from proxy.providers.maxmind_geo import GeoLookup


def test_brightdata_not_configured():
    p = BrightDataProvider(customer="", password="")
    assert not p.configured
    assert p.list_endpoints() == []
    assert p.status()["provider"] == "brightdata"


def test_brightdata_build():
    p = BrightDataProvider(customer="cust", password="secret", zone="residential")
    assert p.configured
    ep = p.build_proxy(country="us", session_id="abc")
    assert ep["user"].startswith("brd-customer-cust")
    assert "country-us" in ep["user"]
    assert ep["password"] == "secret"
    assert len(p.list_endpoints(countries=["us", "de"], sessions=2)) == 4


def test_oxylabs_build():
    p = OxylabsProvider(username="user1", password="pw")
    ep = p.build_proxy(country="de", session_id="s1")
    assert "customer-user1" in ep["user"]
    assert "cc-de" in ep["user"]


def test_tor_i2p_status():
    t = TorProvider()
    assert "provider" in t.status()
    i = I2PProvider()
    assert "provider" in i.status()


def test_geo_lookup_fallback():
    g = GeoLookup()
    r = g.lookup("8.8.8.8")
    assert r["country"]
    assert r["source"] in ("maxmind", "hint")
