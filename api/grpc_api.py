"""api/grpc_api.py — gRPC service stubs (ready for grpcio codegen)"""
SERVICES = ["BotService", "AttackService", "ProxyService", "UserService", "StatsService"]

# Pseudo service implementations for documentation / future grpcio wire-up
class BotService:
    def ListBots(self, request, context=None):
        return {"bots": []}
    def RegisterBot(self, request, context=None):
        return {"ok": True}
    def Heartbeat(self, request, context=None):
        return {"ok": True}

class AttackService:
    def ListAttacks(self, request, context=None):
        return {"attacks": []}
    def CreateAttack(self, request, context=None):
        return {"ok": True}
    def StopAttack(self, request, context=None):
        return {"ok": True}

class ProxyService:
    def ListProxies(self, request, context=None):
        return {"proxies": []}
    def Scrape(self, request, context=None):
        return {"ok": True}

class StatsService:
    def GetStats(self, request, context=None):
        return {"status": "online"}

def get_services():
    return {
        "BotService": BotService(),
        "AttackService": AttackService(),
        "ProxyService": ProxyService(),
        "StatsService": StatsService(),
    }
