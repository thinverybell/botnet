"""
core/proxy_manager.py — MHDDoS-style multi-source proxy manager
"""
import json, time, random, socket, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Dict, List, Any
from urllib.request import urlopen, Request

from .database import Database
from .cache import Cache

TYPE_MAP = {0: "all", 1: "http", 4: "socks4", 5: "socks5"}
TYPE_REV = {"http": 1, "https": 1, "socks4": 4, "socks5": 5, "all": 0}

class Proxy:
    def __init__(self, address: str, port: int, ptype: int = 5, user: str = None, password: str = None):
        self.address = address
        self.port = int(port)
        self.type = int(ptype)
        self.user = user
        self.password = password
        self.alive = False
        self.latency = 0
        self.last_check = None
        self.score = 50
        self.failures = 0
        self.country = None

    def to_dict(self) -> Dict:
        return {
            "address": self.address, "port": self.port, "type": self.type,
            "protocol": TYPE_MAP.get(self.type, "socks5"),
            "status": "alive" if self.alive else "dead", "alive": self.alive,
            "latency": self.latency, "last_check": self.last_check,
            "score": self.score, "failures": self.failures,
            "user": self.user, "password": self.password,
            "country": self.country,
        }

    def as_request(self) -> Dict[str, str]:
        proto = TYPE_MAP.get(self.type, "socks5")
        if proto == "all":
            proto = "http"
        auth = f"{self.user}:{self.password}@" if self.user and self.password else ""
        url = f"{proto}://{auth}{self.address}:{self.port}"
        return {"http": url, "https": url}

    def __str__(self):
        return f"{TYPE_MAP.get(self.type,'?')}://{self.address}:{self.port}"


class ProxyManager:
    def __init__(self, db: Database = None, cache: Cache = None, config_path: str = "config.json"):
        self.db = db
        self.cache = cache
        self.config_path = Path(config_path)
        self.config: Dict = {}
        self.providers: List[Dict] = []
        self.proxies: List[Proxy] = []
        self.proxy_pool_path = Path("proxy/proxy_pool.txt")
        self.log_path = Path("logs/proxy.log")
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.proxy_pool_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self.load_config()

    def _log(self, msg: str):
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            with open(self.log_path, "a", encoding="utf-8") as f:
                f.write(f"[{ts}] {msg}\n")
        except Exception:
            pass

    def load_config(self) -> Dict:
        if self.config_path.exists():
            try:
                self.config = json.loads(self.config_path.read_text(encoding="utf-8"))
            except Exception:
                self.config = {}
        self.providers = self.config.get("proxy-providers", [])
        self._log(f"Loaded {len(self.providers)} providers")
        return self.config

    def download(self, provider: Dict) -> List[Proxy]:
        url = provider.get("url", "")
        ptype = int(provider.get("type", 0))
        timeout = int(provider.get("timeout", 5))
        out: List[Proxy] = []
        try:
            req = Request(url, headers={"User-Agent": "RyzenC2-ProxyScraper/8.0"})
            with urlopen(req, timeout=timeout) as resp:
                text = resp.read().decode("utf-8", errors="ignore")
            out = self.parse_proxy(text, ptype)
            self._log(f"OK {url[:50]} -> {len(out)}")
        except Exception as e:
            self._log(f"FAIL {url[:50]} {e}")
        return out

    def download_from_config(self, max_workers: int = 20) -> int:
        if not self.providers:
            self.load_config()
        collected: List[Proxy] = []
        seen = set()
        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futs = {ex.submit(self.download, p): p for p in self.providers}
            for fut in as_completed(futs):
                try:
                    for px in fut.result():
                        key = f"{px.address}:{px.port}"
                        if key not in seen:
                            seen.add(key)
                            collected.append(px)
                except Exception:
                    pass
        with self._lock:
            for px in self.proxies:
                key = f"{px.address}:{px.port}"
                if key not in seen:
                    seen.add(key)
                    collected.append(px)
            self.proxies = collected
        self._log(f"Total unique: {len(self.proxies)}")
        self.save_pool_txt()
        return len(self.proxies)

    def parse_proxy(self, data: str, default_type: int = 0) -> List[Proxy]:
        result = []
        for line in data.splitlines():
            px = self._parse_line(line.strip(), default_type)
            if px:
                result.append(px)
        return result

    def _parse_line(self, line: str, default_type: int = 0) -> Optional[Proxy]:
        if not line or line.startswith("#") or line.startswith("//"):
            return None
        ptype = default_type
        user = password = None
        if "://" in line:
            proto, rest = line.split("://", 1)
            ptype = TYPE_REV.get(proto.lower(), default_type or 5)
            line = rest
        if "@" in line:
            cred, line = line.rsplit("@", 1)
            if ":" in cred:
                user, password = cred.split(":", 1)
            else:
                user = cred
        if ":" not in line:
            return None
        try:
            host, port_s = line.rsplit(":", 1)
            port = int(port_s.strip())
            host = host.strip()
            if not host or port < 1 or port > 65535:
                return None
            if ptype == 0:
                ptype = 5
            return Proxy(host, port, ptype, user=user, password=password)
        except Exception:
            return None

    def check_proxy(self, proxy: Proxy, target: str = None, timeout: float = None) -> Proxy:
        cfg = self.config.get("proxy-check", {})
        timeout = timeout if timeout is not None else float(cfg.get("timeout", 10))
        threshold = int(cfg.get("latency-threshold", 5000))
        start = time.time()
        alive = False
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(min(timeout, 5))
            sock.connect((proxy.address, proxy.port))
            sock.close()
            alive = True
        except Exception:
            alive = False
        latency_ms = int((time.time() - start) * 1000)
        proxy.alive = alive and latency_ms < threshold
        proxy.latency = latency_ms if alive else 0
        proxy.last_check = time.time()
        if proxy.alive:
            proxy.score = max(10, 100 - latency_ms // 50)
            proxy.failures = 0
        else:
            proxy.score = max(0, proxy.score - 10)
            proxy.failures += 1
        return proxy

    def check_proxies(self, max_workers: int = None) -> Dict[str, int]:
        cfg = self.config.get("proxy-check", {})
        workers = max_workers or int(cfg.get("threads", 50))
        with self._lock:
            proxies = list(self.proxies)
        if not proxies:
            return {"total": 0, "alive": 0, "dead": 0}
        alive = dead = 0
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futs = [ex.submit(self.check_proxy, p) for p in proxies]
            for fut in as_completed(futs):
                try:
                    p = fut.result()
                    if p.alive:
                        alive += 1
                    else:
                        dead += 1
                except Exception:
                    dead += 1
        self._log(f"Check: alive={alive} dead={dead}")
        self.save_proxies()
        self.save_pool_txt()
        return {"total": len(proxies), "alive": alive, "dead": dead}

    def remove_dead(self) -> int:
        with self._lock:
            before = len(self.proxies)
            self.proxies = [p for p in self.proxies if p.alive]
            removed = before - len(self.proxies)
        self.save_proxies()
        self.save_pool_txt()
        return removed

    def save_proxies(self) -> None:
        records = [p.to_dict() for p in self.proxies]
        if self.db:
            self.db.clear("proxies")
            for r in records:
                self.db.insert("proxies", r)
        else:
            path = Path("data/proxies.json")
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(records, indent=2), encoding="utf-8")

    def load_proxies(self) -> int:
        loaded = []
        if self.db:
            for r in self.db.find_all("proxies"):
                p = Proxy(r.get("address",""), r.get("port",0), r.get("type", TYPE_REV.get(r.get("protocol","socks5"),5)))
                p.alive = r.get("alive", r.get("status")=="alive")
                p.latency = r.get("latency", 0)
                p.last_check = r.get("last_check")
                p.score = r.get("score", 50)
                p.failures = r.get("failures", 0)
                if p.address:
                    loaded.append(p)
        with self._lock:
            self.proxies = loaded
        return len(loaded)

    def save_pool_txt(self) -> None:
        lines = []
        for p in self.proxies:
            if p.alive or not p.last_check:
                lines.append(f"{TYPE_MAP.get(p.type,'socks5')}://{p.address}:{p.port}")
        self.proxy_pool_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

    def has_proxies(self) -> bool:
        return len(self.proxies) > 0

    def get_random_proxy(self, only_alive: bool = True) -> Optional[Proxy]:
        with self._lock:
            pool = [p for p in self.proxies if p.alive] if only_alive else list(self.proxies)
        if not pool:
            pool = list(self.proxies)
        return random.choice(pool) if pool else None

    def get_proxy_by_type(self, ptype) -> List[Proxy]:
        if isinstance(ptype, str):
            ptype = TYPE_REV.get(ptype.lower(), 5)
        with self._lock:
            return [p for p in self.proxies if p.type == ptype or ptype == 0]

    def get_alive_proxies(self) -> List[Proxy]:
        with self._lock:
            return [p for p in self.proxies if p.alive]

    def get_dead_proxies(self) -> List[Proxy]:
        with self._lock:
            return [p for p in self.proxies if not p.alive]

    def rotate(self) -> Optional[Proxy]:
        return self.get_random_proxy(True)

    def add_proxy(self, address: str = None, port: int = None, ptype: int = 5, proxy_data: Dict = None) -> Any:
        if proxy_data:
            address = proxy_data.get("address") or proxy_data.get("proxy", "").split(":")[0]
            port = proxy_data.get("port") or 1080
            ptype = proxy_data.get("type", TYPE_REV.get(proxy_data.get("protocol","socks5"),5))
        p = Proxy(address, port, ptype)
        with self._lock:
            self.proxies.append(p)
        if self.db:
            self.db.insert("proxies", p.to_dict())
        return p

    def remove_proxy(self, address: str = None, port: int = None, proxy_id: int = None) -> bool:
        if proxy_id is not None and self.db:
            return self.db.delete("proxies", proxy_id)
        with self._lock:
            before = len(self.proxies)
            self.proxies = [p for p in self.proxies if not (p.address == address and p.port == port)]
            return before > len(self.proxies)

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            total = len(self.proxies)
            alive = sum(1 for p in self.proxies if p.alive)
            by_type = {}
            for p in self.proxies:
                t = TYPE_MAP.get(p.type, str(p.type))
                by_type[t] = by_type.get(t, 0) + 1
            avg_lat = 0
            al = [p for p in self.proxies if p.alive and p.latency]
            if al:
                avg_lat = int(sum(p.latency for p in al) / len(al))
        return {"total": total, "alive": alive, "dead": total - alive,
                "by_type": by_type, "providers": len(self.providers), "avg_latency_ms": avg_lat}

    def get_providers(self) -> List[Dict]:
        return list(self.providers)

    def ensure_proxies(self, min_count: int = 10) -> int:
        if len(self.proxies) < min_count:
            self._log("Auto scrape")
            self.download_from_config()
            if self.proxies:
                sample = self.proxies[:min(100, len(self.proxies))]
                with ThreadPoolExecutor(max_workers=20) as ex:
                    list(ex.map(self.check_proxy, sample))
                self.save_proxies()
                self.save_pool_txt()
        return len(self.proxies)

    def get_all_proxies(self) -> List[Dict]:
        return [p.to_dict() for p in self.proxies]

    def get_best_proxies(self, n: int = 10) -> List[Dict]:
        alive = sorted(self.get_alive_proxies(), key=lambda p: p.score, reverse=True)
        return [p.to_dict() for p in alive[:n]]

    def simulate(self, count: int = 100) -> int:
        for _ in range(count):
            self.add_proxy(
                f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                random.choice([1080, 8080, 3128, 9050]),
                random.choice([1, 4, 5]),
            )
        return count

    def load_from_file(self, filepath: str) -> int:
        path = Path(filepath)
        if not path.exists():
            return 0
        parsed = self.parse_proxy(path.read_text(encoding="utf-8", errors="ignore"), 5)
        with self._lock:
            seen = {f"{p.address}:{p.port}" for p in self.proxies}
            n = 0
            for p in parsed:
                key = f"{p.address}:{p.port}"
                if key not in seen:
                    self.proxies.append(p)
                    seen.add(key)
                    n += 1
        return n


    def get_chain(self, hops: int = 2, only_alive: bool = True) -> list:
        from proxy.proxy_chain import build_chain
        pool = self.get_alive_proxies() if only_alive else list(self.proxies)
        if not pool:
            pool = list(self.proxies)
        return build_chain(pool, hops)

    def get_sticky_rotator(self, strategy: str = "sticky"):
        from proxy.proxy_rotator import ProxyRotator
        alive = self.get_alive_proxies() or list(self.proxies)
        return ProxyRotator(alive, strategy=strategy)

    def filter_geo(self, country: str) -> list:
        from proxy.proxy_geo import filter_by_country, annotate_geo
        annotate_geo(self.proxies)
        return filter_by_country(self.proxies, country)

    def score_all(self):
        from proxy.proxy_scorer import score as score_fn
        for p in self.proxies:
            p.score = score_fn(latency=p.latency or 999, reliability=0.7 if p.alive else 0.2)
        return len(self.proxies)


    def load_paid_providers(self, countries=None, sessions: int = 1) -> int:
        """Import Bright Data / Oxylabs endpoints if credentials present."""
        from proxy.providers.brightdata import BrightDataProvider
        from proxy.providers.oxylabs import OxylabsProvider
        n = 0
        for prov in (BrightDataProvider(), OxylabsProvider()):
            for ep in prov.list_endpoints(countries=countries, sessions=sessions):
                self.add_proxy(
                    ep.get("address"), int(ep.get("port") or 0),
                    int(ep.get("type") or 1),
                )
                # enrich last proxy
                if self.proxies:
                    last = self.proxies[-1]
                    last.user = ep.get("user")
                    last.password = ep.get("password")
                    last.country = ep.get("country")
                    last.score = ep.get("score", 85)
                    last.alive = True
                n += 1
        self._log(f"Paid providers loaded: {n}")
        return n

    def load_tor_i2p(self) -> int:
        """Add local Tor / I2P SOCKS if ports open."""
        from proxy.providers.tor_i2p import TorProvider, I2PProvider
        n = 0
        for prov in (TorProvider(), I2PProvider()):
            for ep in prov.list_endpoints():
                self.add_proxy(ep["address"], ep["port"], int(ep.get("type") or 5))
                if self.proxies:
                    last = self.proxies[-1]
                    last.score = ep.get("score", 70)
                    last.alive = True
                    last.country = ep.get("country")
                n += 1
        self._log(f"Tor/I2P loaded: {n}")
        return n

    def enrich_geo_maxmind(self) -> int:
        """Annotate country via MaxMind if DB available, else hints."""
        from proxy.providers.maxmind_geo import GeoLookup
        geo = GeoLookup()
        for p in self.proxies:
            p.country = geo.country(p.address)
        return len(self.proxies)

    def providers_status(self) -> dict:
        from proxy.providers.brightdata import BrightDataProvider
        from proxy.providers.oxylabs import OxylabsProvider
        from proxy.providers.tor_i2p import TorProvider, I2PProvider
        from proxy.providers.maxmind_geo import GeoLookup
        return {
            "brightdata": BrightDataProvider().status(),
            "oxylabs": OxylabsProvider().status(),
            "tor": TorProvider().status(),
            "i2p": I2PProvider().status(),
            "geo": GeoLookup().status(),
            "public_providers": len(self.providers),
        }
