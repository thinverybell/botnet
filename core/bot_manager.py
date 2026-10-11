"""core/bot_manager.py"""
import time, random
from typing import Optional, Dict, List
from .database import Database
from .cache import Cache
from .utils import generate_uuid, group_by, filter_by

class BotManager:
    def __init__(self, db: Database, cache: Cache, timeout: int = 120):
        self.db, self.cache, self.timeout = db, cache, timeout

    def register(self, data: Dict) -> Dict:
        data.setdefault("uuid", generate_uuid())
        data.setdefault("status", "online")
        data.setdefault("last_seen", time.time())
        data.setdefault("registered_at", time.time())
        data.setdefault("attack_id", None)
        data.setdefault("methods", ["UDP-FLOOD","TCP-FLOOD","HTTP-FLOOD"])
        data.setdefault("bandwidth", 100_000_000)
        r = self.db.insert("bots", data)
        self.cache.delete("bot:online")
        return r

    def unregister(self, uuid: str) -> bool:
        bots = self.db.find("bots", {"uuid": uuid})
        if not bots: return False
        self.db.delete("bots", bots[0]["id"])
        return True

    def heartbeat(self, uuid: str, data: Optional[Dict]=None) -> bool:
        bots = self.db.find("bots", {"uuid": uuid})
        if not bots: return False
        upd = {"last_seen": time.time(), "status": "online"}
        if data: upd.update({k:data[k] for k in ("cpu_usage","ram_usage","network_usage","bandwidth") if k in data})
        self.db.update("bots", bots[0]["id"], upd)
        return True

    def get(self, uuid): 
        b=self.db.find("bots",{"uuid":uuid}); return b[0] if b else None
    def get_all(self): return self.db.find_all("bots")
    def update(self, uuid, data):
        b=self.get(uuid); return self.db.update("bots", b["id"], data) if b else None
    def delete(self, uuid): return self.unregister(uuid)

    def get_online(self):
        now=time.time(); out=[]
        for b in self.get_all():
            if b.get("status")=="online" and (now-b.get("last_seen",0))<self.timeout: out.append(b)
            elif b.get("status")=="online": self.db.update("bots", b["id"], {"status":"offline"})
        return out

    def get_offline(self): return filter_by(self.get_all(),"status","offline")
    def get_attacking(self): return [b for b in self.get_all() if b.get("attack_id")]
    def get_idle(self): return [b for b in self.get_online() if not b.get("attack_id")]

    def get_stats(self):
        allb=self.get_all(); online=self.get_online()
        return {"total":len(allb),"online":len(online),"offline":len(allb)-len(online),
                "attacking":len(self.get_attacking()),"idle":len(self.get_idle()),
                "by_os":{k:len(v) for k,v in group_by(allb,"os").items()},
                "by_country":{k:len(v) for k,v in group_by(allb,"country").items()}}

    def cleanup(self):
        now=time.time(); n=0
        for b in self.get_all():
            if b.get("status")=="online" and (now-b.get("last_seen",0))>=self.timeout:
                self.db.update("bots", b["id"], {"status":"offline"}); n+=1
        return n

    def simulate(self, count=50):
        os_l=["Linux","Windows","Android","Router","IoT","FreeBSD","OpenWRT"]
        arch=["x86_64","arm64","armv7","mips","mipsel"]
        countries=["US","DE","RU","CN","BR","IN","JP","KR","VN","FR"]
        for _ in range(count):
            self.register({"ip":f"{random.randint(1,223)}.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}",
                "os":random.choice(os_l),"arch":random.choice(arch),"country":random.choice(countries),
                "version":"8.0.0","bandwidth":random.choice([50,100,200,500,1000])*1_000_000})
        return count
