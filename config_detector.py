import hashlib
import json
import re


URI_PATTERN = re.compile(
    r'('
    r'vmess://[A-Za-z0-9+/=_\-]+(?:[?\#][^\s]*)?'
    r'|vless://[^\s]+'
    r'|ss://[^\s]+'
    r'|trojan://[^\s]+'
    r'|reality://[^\s]+'
    r'|hy2://[^\s]+'
    r'|hysteria2://[^\s]+'
    r'|hysteria://[^\s]+'
    r'|wireguard://[^\s]+'
    r')',
    re.IGNORECASE,
)

TG_PROXY_PATTERN = re.compile(
    r'(tg://proxy\?[^\s]+|https?://t\.me/proxy\?[^\s]+)',
    re.IGNORECASE,
)

V2RAY_JSON_KEYS = {"v", "ps", "add", "port"}
V2RAY_FULL_KEYS = {"outbounds", "inbounds"}


def _hash_config(raw: str) -> str:
    normalized = raw.strip().lower()
    return hashlib.sha256(normalized.encode()).hexdigest()


def _classify_uri(uri: str) -> str:
    lower = uri.lower()
    for proto in ("vmess", "vless", "ss", "trojan", "reality", "hysteria2", "hysteria", "hy2", "wireguard"):
        if lower.startswith(proto + "://"):
            return proto
    return "unknown"


def _find_json_configs(text: str) -> list[dict]:
    results = []
    i = 0
    while i < len(text):
        if text[i] == '{':
            depth = 0
            j = i
            while j < len(text):
                if text[j] == '{':
                    depth += 1
                elif text[j] == '}':
                    depth -= 1
                    if depth == 0:
                        candidate = text[i:j + 1]
                        try:
                            obj = json.loads(candidate)
                            if isinstance(obj, dict):
                                keys = set(obj.keys())
                                if V2RAY_JSON_KEYS.issubset(keys) or V2RAY_FULL_KEYS.intersection(keys):
                                    results.append({
                                        "type": "json_v2ray",
                                        "raw": candidate,
                                        "hash": _hash_config(candidate),
                                    })
                        except (json.JSONDecodeError, ValueError):
                            pass
                        break
                j += 1
        i += 1
    return results


def extract_configs(text: str) -> list[dict]:
    """Extract all V2Ray and Telegram proxy configs from a text message.

    Returns a list of dicts with keys: type, raw, hash
    """
    if not text:
        return []

    seen_hashes = set()
    configs = []

    # URI-scheme configs
    for match in URI_PATTERN.finditer(text):
        raw = match.group(0).rstrip(".,;:!?)'\"")
        h = _hash_config(raw)
        if h not in seen_hashes:
            seen_hashes.add(h)
            configs.append({
                "type": _classify_uri(raw),
                "raw": raw,
                "hash": h,
            })

    # Telegram proxy links
    for match in TG_PROXY_PATTERN.finditer(text):
        raw = match.group(0).rstrip(".,;:!?)'\"")
        h = _hash_config(raw)
        if h not in seen_hashes:
            seen_hashes.add(h)
            configs.append({
                "type": "tg_proxy",
                "raw": raw,
                "hash": h,
            })

    # Raw JSON V2Ray configs
    for cfg in _find_json_configs(text):
        if cfg["hash"] not in seen_hashes:
            seen_hashes.add(cfg["hash"])
            configs.append(cfg)

    return configs
