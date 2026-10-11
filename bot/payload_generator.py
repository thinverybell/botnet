"""bot/payload_generator.py — generate lab bot client payloads"""
from typing import Dict, Optional
import base64
import textwrap


def generate_python_bot(host: str, port: int, key: str, interval: int = 30) -> str:
    return textwrap.dedent(f'''\
    #!/usr/bin/env python3
    # Generated RyzenC2 lab bot — authorized testing only
    import json, platform, time, uuid, urllib.request

    HOST, PORT, KEY, INTERVAL = {host!r}, {port}, {key!r}, {interval}
    BOT_ID = str(uuid.uuid4())
    BASE = f"http://{{HOST}}:{{PORT}}"

    def post(path, data):
        body = json.dumps(data).encode()
        req = urllib.request.Request(
            BASE + path, data=body,
            headers={{"Content-Type": "application/json", "X-API-Key": KEY}},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode())

    def main():
        info = {{
            "uuid": BOT_ID,
            "ip": "0.0.0.0",
            "os": platform.system(),
            "arch": platform.machine(),
            "hostname": platform.node(),
            "version": "8.0.0",
            "status": "online",
        }}
        print(f"[*] lab bot {{BOT_ID[:12]}} -> {{BASE}}")
        try:
            post("/api/v1/bots/register", info)
        except Exception as e:
            print("[!] register", e)
        while True:
            try:
                post("/api/v1/bots/heartbeat", {{"uuid": BOT_ID, "status": "online"}})
            except Exception as e:
                print("[!] hb", e)
            time.sleep(INTERVAL)

    if __name__ == "__main__":
        main()
    ''')


def generate_bash_bot(host: str, port: int, key: str, interval: int = 30) -> str:
    return textwrap.dedent(f'''\
    #!/bin/bash
    # RyzenC2 lab bot (curl) — authorized only
    HOST={host!r}; PORT={port}; KEY={key!r}; INTERVAL={interval}
    UUID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || uuidgen 2>/dev/null || echo "lab-$RANDOM")
    BASE="http://$HOST:$PORT"
    curl -s -X POST -H "Content-Type: application/json" -H "X-API-Key: $KEY" \\
      -d "{{\\"uuid\\":\\"$UUID\\",\\"os\\":\\"$(uname)\\",\\"arch\\":\\"$(uname -m)\\",\\"status\\":\\"online\\"}}" \\
      "$BASE/api/v1/bots/register" >/dev/null
    while true; do
      curl -s -X POST -H "Content-Type: application/json" -H "X-API-Key: $KEY" \\
        -d "{{\\"uuid\\":\\"$UUID\\",\\"status\\":\\"online\\"}}" \\
        "$BASE/api/v1/bots/heartbeat" >/dev/null
      sleep $INTERVAL
    done
    ''')


def generate_powershell_bot(host: str, port: int, key: str, interval: int = 30) -> str:
    return textwrap.dedent(f'''\
    # RyzenC2 lab bot (PowerShell) — authorized only
    $HostApi = "{host}"; $Port = {port}; $Key = "{key}"; $Interval = {interval}
    $Uuid = [guid]::NewGuid().ToString()
    $Base = "http://$HostApi`:$Port"
    $headers = @{{ "X-API-Key" = $Key; "Content-Type" = "application/json" }}
    try {{
      Invoke-RestMethod -Method POST -Uri "$Base/api/v1/bots/register" -Headers $headers -Body ({{uuid=$Uuid;os="Windows";status="online"}} | ConvertTo-Json)
    }} catch {{}}
    while ($true) {{
      try {{
        Invoke-RestMethod -Method POST -Uri "$Base/api/v1/bots/heartbeat" -Headers $headers -Body ({{uuid=$Uuid;status="online"}} | ConvertTo-Json)
      }} catch {{}}
      Start-Sleep -Seconds $Interval
    }}
    ''')


def generate_all(host: str = "127.0.0.1", port: int = 8080, key: str = "ryzenc2_api_key_change_me") -> Dict[str, str]:
    return {
        "python": generate_python_bot(host, port, key),
        "bash": generate_bash_bot(host, port, key),
        "powershell": generate_powershell_bot(host, port, key),
    }


def to_b64(script: str) -> str:
    return base64.b64encode(script.encode()).decode()
