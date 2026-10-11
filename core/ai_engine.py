"""core/ai_engine.py"""
import time, random
from typing import Optional, Dict, List

class AIEngine:
    def __init__(self, config=None):
        self.config = config or {}
        self._history: List[Dict] = []
        self._models = ["heuristic-v1","pattern-v1","bypass-v1"]

    def chat(self, message: str, context=None) -> str:
        m = message.lower()
        if "bypass" in m or "cloudflare" in m: return self.bypass({"type":"cloudflare"}).get("recommendation","")
        if "plan" in m or "attack" in m: return "Recommend: SYN-FLOOD then HTTP2-FLOOD. Residential proxies. 60-120s."
        if "status" in m: return "AI online. Models: "+", ".join(self._models)
        return f"AI: {message[:100]}"

    def analyze(self, target: str) -> Dict:
        is_ip = self._is_ip(target)
        p = {"target":target,"type":"ip" if is_ip else "domain",
             "suggested_layer":"L4" if is_ip else "L7","suggested_methods":[],
             "risk":"medium","notes":[],"ts":time.time()}
        if is_ip:
            p["suggested_methods"]=["SYN-FLOOD","UDP-FLOOD","ACK-FLOOD"]
            p["notes"].append("Direct IP — L4 preferred")
        else:
            p["suggested_methods"]=["HTTP-FLOOD","HTTP2-FLOOD","CF-BYPASS","SLOWLORIS"]
            p["notes"].append("Domain — check CDN/WAF")
        self._history.append({"action":"analyze","target":target,"ts":p["ts"]})
        return p

    def plan(self, target: str) -> Dict:
        a = self.analyze(target)
        plan = {"target":target,"phases":[
            {"phase":1,"name":"Probe","methods":a["suggested_methods"][:1],"duration":15,"threads":20},
            {"phase":2,"name":"Main","methods":a["suggested_methods"][:3],"duration":60,"threads":100},
            {"phase":3,"name":"Adaptive","methods":a["suggested_methods"],"duration":30,"threads":50},
        ],"proxy_required":a["type"]=="domain","estimated_success":round(random.uniform(0.55,0.92),3),"risk":a["risk"]}
        self._history.append({"action":"plan","target":target,"ts":time.time()})
        return plan

    def bypass(self, target: Dict) -> Dict:
        t = str(target.get("type",target.get("target",""))).lower()
        strat = {
            "cloudflare":{"methods":["CF-BYPASS","BROWSER-EMULATION","HTTP2-FLOOD"],"recommendation":"Browser emulation + residential proxies. Rotate JA3.","confidence":0.78},
            "ovh":{"methods":["OVH-BYPASS","UDP-BYPASS"],"recommendation":"Short UDP/TCP bursts.","confidence":0.72},
            "akamai":{"methods":["AKAMAI-BYPASS","HTTP2-FLOOD"],"recommendation":"Emulate real browser fingerprints.","confidence":0.70},
        }
        for k,v in strat.items():
            if k in t: return v
        return {"methods":["HTTP-FLOOD","SYN-FLOOD"],"recommendation":"Mix L4+L7, rotate proxies.","confidence":0.60}

    def optimize(self, params: Dict) -> Dict:
        return {"original":params,"suggested_threads":min(max(params.get("threads",100),50),500),
                "suggested_duration":min(max(params.get("duration",60),30),300),
                "tips":["More bots fewer threads","Rotate proxies 10-15s L7","Monitor PPS/BPS"]}

    def predict(self, data: Dict) -> Dict:
        bots=data.get("bot_count",10); base=0.5
        if bots>100: base+=0.2
        if bots>500: base+=0.15
        return {"success_probability":round(min(0.95,base+random.uniform(-0.05,0.1)),3),"bots":bots}

    def detect(self, data: Dict) -> Dict:
        alerts=[]
        if data.get("pps",0)==0 and data.get("status")=="running": alerts.append("Zero PPS while running")
        return {"anomalies":alerts,"severity":"ok" if not alerts else "warn"}

    def report(self, data: Dict) -> str:
        return (f"=== AI Report ===\nTarget:{data.get('target')}\nMethod:{data.get('method')}\n"
                f"Duration:{data.get('duration')}s\nBots:{data.get('bot_count')}\n"
                f"PPS:{data.get('pps',0):,}\nBPS:{data.get('bps',0):,}\n================")

    def get_models(self): return list(self._models)
    def get_history(self): return list(self._history[-50:])
    @staticmethod
    def _is_ip(s):
        parts=s.split(".")
        if len(parts)!=4: return False
        try: return all(0<=int(p)<=255 for p in parts)
        except: return False


    def bypass(self, data):
        try:
            from core.bypass_engine import plan_bypass
            if isinstance(data, dict):
                return plan_bypass(data.get("type") or data.get("vendor"), data.get("headers"))
            return plan_bypass(str(data))
        except Exception:
            return {"vendor": "generic", "recommended_methods": ["HTTP-FLOOD"], "lab_notes": ["fallback"]}
