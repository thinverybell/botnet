"""core/attack_scheduler.py"""
import time, random, threading
from typing import Optional, Dict, List
from .database import Database
from .cache import Cache
from .bot_manager import BotManager
from .proxy_manager import ProxyManager
from .methods import L4_METHODS, L7_METHODS, ALL_METHODS, method_info

class AttackScheduler:
    def __init__(self, db, cache, bot_manager, proxy_manager):
        self.db, self.cache = db, cache
        self.bot_manager, self.proxy_manager = bot_manager, proxy_manager
        self._running: Dict[int,bool] = {}
        self._threads: Dict[int,threading.Thread] = {}

    def create_attack(self, data: Dict) -> Dict:
        method = data.get("method","UDP-FLOOD").upper().replace("_","-")
        info = method_info(method)
        data["method"] = method
        data.setdefault("status","pending")
        data.setdefault("started_at",None); data.setdefault("ended_at",None)
        data.setdefault("pps",0); data.setdefault("bps",0); data.setdefault("bot_count",0)
        data.setdefault("layer", info.get("layer","L4"))
        data.setdefault("priority","normal"); data.setdefault("created_by","admin")
        return self.db.insert("attacks", data)

    def start_attack(self, attack_id: int) -> bool:
        a = self.db.find_one("attacks",{"id":attack_id})
        if not a or a["status"]=="running": return False
        online = self.bot_manager.get_online()
        bc = min(a.get("threads",100), len(online) or 1)
        self.db.update("attacks", attack_id, {"status":"running","started_at":time.time(),"bot_count":bc})
        self._running[attack_id] = True
        def worker():
            end = time.time() + a.get("duration",60)
            while time.time() < end and self._running.get(attack_id, False):
                self.db.update("attacks", attack_id, {
                    "pps": random.randint(5000,200000),
                    "bps": random.randint(50_000_000, 3_000_000_000)})
                time.sleep(1)
            self.complete_attack(attack_id)
        t = threading.Thread(target=worker, daemon=True)
        self._threads[attack_id] = t; t.start()
        return True

    def stop_attack(self, attack_id: int) -> bool:
        if attack_id not in self._running: return False
        self._running[attack_id] = False
        self.db.update("attacks", attack_id, {"status":"stopped","ended_at":time.time()})
        return True

    def complete_attack(self, attack_id, result=None):
        self._running.pop(attack_id, None)
        self.db.update("attacks", attack_id, {"status":"completed","ended_at":time.time()})

    def get_attack(self, aid): return self.db.find_one("attacks",{"id":aid})
    def get_all_attacks(self): return self.db.find_all("attacks")
    def get_running_attacks(self): return [a for a in self.get_all_attacks() if a.get("status")=="running"]
    def get_completed_attacks(self): return [a for a in self.get_all_attacks() if a.get("status") in ("completed","stopped")]
    def stop_all(self):
        n=0
        for aid in list(self._running):
            if self.stop_attack(aid): n+=1
        return n
    def get_stats(self):
        all_a=self.get_all_attacks()
        return {"total":len(all_a),"running":len(self.get_running_attacks()),
                "completed":len(self.get_completed_attacks()),
                "failed":len([a for a in all_a if a.get("status")=="failed"])}
    @staticmethod
    def list_methods(): return {"L4":L4_METHODS,"L7":L7_METHODS,"all":ALL_METHODS}


    def lab_simulate_attack(self, attack_id: int) -> dict:
        """Run lab-only simulation with optional proxy assignment."""
        attacks = self.db.find_all("attacks")
        atk = None
        for a in attacks:
            if a.get("id") == attack_id:
                atk = a
                break
        if not atk:
            return {"ok": False, "error": "not found"}
        proxy = None
        if self.proxy_mgr and hasattr(self.proxy_mgr, "get_random_proxy"):
            px = self.proxy_mgr.get_random_proxy(only_alive=True)
            if px:
                proxy = px.to_dict() if hasattr(px, "to_dict") else px
        method = (atk.get("method") or "UDP-FLOOD").upper().replace("_", "-")
        from core.methods import is_l4, is_l7
        if is_l4(method):
            from bot.attack_l4 import simulate_l4
            result = simulate_l4(
                method,
                atk.get("target_ip") or atk.get("target") or "127.0.0.1",
                int(atk.get("target_port") or 80),
                int(atk.get("duration") or 5),
                int(atk.get("threads") or 10),
                proxy=proxy,
            )
        else:
            from bot.attack_l7 import simulate_l7
            target = atk.get("target_ip") or atk.get("target") or "http://127.0.0.1/"
            if not str(target).startswith("http"):
                target = f"http://{target}/"
            result = simulate_l7(
                method, str(target),
                int(atk.get("duration") or 5),
                int(atk.get("threads") or 10),
                proxy=proxy,
            )
        # store metrics
        self.db.update("attacks", attack_id, {
            "pps": result.get("simulated_pps") or result.get("simulated_rps") or 0,
            "bps": result.get("simulated_bps") or 0,
            "lab_result": result,
            "proxy_used": result.get("proxy"),
        })
        return result
