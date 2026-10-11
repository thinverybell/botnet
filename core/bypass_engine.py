"""core/bypass_engine.py — structured CDN/WAF profile notes (defensive/lab)"""
from typing import Dict, Any, List

PROFILES = {
    "cloudflare": {
        "signals": ["cf-ray", "cf-cache-status", "__cf_bm", "challenge-platform"],
        "layers": ["anycast", "WAF", "bot_management", "turnstile"],
        "lab_notes": [
            "Respect robots and authorized scope only",
            "Challenge pages require browser-like TLS/JA3 diversity in real red-team tools",
            "Rate limits apply per IP/class",
        ],
        "recommended_methods": ["HTTP2-FLOOD", "TLS-SPOOF", "JA3-SPOOF", "SLOWLORIS"],
    },
    "aws": {
        "signals": ["x-amz-cf-id", "x-amz-request-id", "Server: Amazon"],
        "layers": ["CloudFront", "ALB", "WAF", "Shield"],
        "lab_notes": ["Shield Advanced is subscription", "WAF rules vary per ACL"],
        "recommended_methods": ["HTTP-FLOOD", "HTTP2-FLOOD", "CDN-FLOOD"],
    },
    "akamai": {
        "signals": ["akamai", "x-akamai", "ghost"],
        "layers": ["edge", "WAF", "bot_manager"],
        "lab_notes": ["Sensor data cookies common"],
        "recommended_methods": ["BROWSER-SPOOF", "BEHAVIOR-BYPASS", "HTTP2-FLOOD"],
    },
    "ovh": {
        "signals": ["ovh", "x-ovh"],
        "layers": ["VAC", "network_filter"],
        "lab_notes": ["VAC mitigates L3/L4 volumetric"],
        "recommended_methods": ["HTTP-FLOOD", "SLOWLORIS"],
    },
    "google": {
        "signals": ["Server: ghs", "x-goog", "Google Frontend"],
        "layers": ["Cloud Armor", "LB", "CDN"],
        "lab_notes": ["Armor policies per backend"],
        "recommended_methods": ["HTTPS-FLOOD", "HTTP2-FLOOD"],
    },
    "azure": {
        "signals": ["x-azure", "Microsoft-Azure", "ARRAffinity"],
        "layers": ["Front Door", "WAF", "App Gateway"],
        "lab_notes": ["WAF managed rulesets"],
        "recommended_methods": ["HTTP-FLOOD", "HEADER-FLOOD"],
    },
    "imperva": {
        "signals": ["incap_ses", "visid_incap", "Imperva"],
        "layers": ["WAF", "bot"],
        "lab_notes": ["Cookie/session based"],
        "recommended_methods": ["COOKIE-FLOOD", "BROWSER-SPOOF"],
    },
    "generic": {
        "signals": [],
        "layers": ["unknown"],
        "lab_notes": ["Fingerprint target before choosing method"],
        "recommended_methods": ["HTTP-FLOOD", "UDP-FLOOD", "SYN-FLOOD"],
    },
}

def detect_vendor(headers: Dict[str, str] = None, body_snippet: str = "") -> str:
    headers = {str(k).lower(): str(v) for k, v in (headers or {}).items()}
    blob = " ".join(list(headers.keys()) + list(headers.values())) + " " + (body_snippet or "")
    blob_l = blob.lower()
    for name, prof in PROFILES.items():
        if name == "generic":
            continue
        for sig in prof["signals"]:
            if sig.lower() in blob_l:
                return name
        if name in blob_l:
            return name
    return "generic"

def plan_bypass(vendor: str = None, headers: Dict = None) -> Dict[str, Any]:
    vendor = (vendor or detect_vendor(headers) or "generic").lower()
    prof = PROFILES.get(vendor, PROFILES["generic"])
    return {
        "vendor": vendor,
        "layers": prof["layers"],
        "signals": prof["signals"],
        "lab_notes": prof["lab_notes"],
        "recommended_methods": prof["recommended_methods"],
        "disclaimer": "Authorized testing only. No exploit payloads included.",
    }
