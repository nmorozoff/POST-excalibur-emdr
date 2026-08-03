#!/usr/bin/env python3
"""Sync B17 proxy settings from ASocks API into browser.env.local fields."""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, load_env

ENV_PATH = MEMORY / "browser.env.local"


def _api_get(path: str, api_key: str, base: str) -> dict:
    url = f"{base.rstrip('/')}{path}"
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}apiKey={urllib.parse.quote(api_key)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _pick_port(payload: dict, name: str | None, port_id: str | None) -> dict:
    message = payload.get("message") or {}
    proxies = message.get("proxies") or payload.get("data") or []
    if not proxies:
        raise SystemExit(f"ASocks: no proxy ports in response: {payload}")
    if port_id:
        for item in proxies:
            if str(item.get("id")) == str(port_id):
                return item
    if name:
        name_l = name.strip().lower()
        for item in proxies:
            if (item.get("name") or "").strip().lower() == name_l:
                return item
    for item in proxies:
        if (item.get("countryCode") or "").upper() == "RU":
            return item
    return proxies[0]


def _parse_template(template: str) -> tuple[str, str, str]:
    # http://login:pass@host:port
    m = re.match(r"^https?://([^:]+):([^@]+)@([^:/]+):(\d+)$", template.strip())
    if not m:
        raise SystemExit(f"Cannot parse ASocks template: {template}")
    login, password, host, port = m.groups()
    return host, port, login


def sync_from_api(
    *,
    port_name: str | None = None,
    write: bool = True,
    target: str = "b17",
) -> dict:
    """target: b17 → B17_PROXY_* ; telegram → TELEGRAM_PROXY_* (ASocks KZ для api.telegram.org)."""
    env = load_env("browser.env.local")
    api_key = env.get("ASOCKS_API_KEY", "").strip()
    base = env.get("ASOCKS_API_BASE", "https://api.asocks.com").strip()
    if not api_key:
        raise SystemExit("Missing ASOCKS_API_KEY in browser.env.local")

    payload = _api_get("/v2/proxy/ports", api_key, base)
    if not payload.get("success"):
        raise SystemExit(f"ASocks API error: {payload}")

    if target == "telegram":
        default_name = env.get("TELEGRAM_ASOCKS_PORT_NAME", "ResKazakhstan - Turkestan").strip()
        default_id = env.get("TELEGRAM_ASOCKS_PORT_ID", "").strip() or None
        prefix = "TELEGRAM_"
        id_key = "TELEGRAM_ASOCKS_PORT_ID"
        name_key = "TELEGRAM_ASOCKS_PORT_NAME"
        connect_key = "TELEGRAM_PROXY_CONNECT_PORT"
    else:
        default_name = env.get("ASOCKS_PORT_NAME", "").strip()
        default_id = env.get("ASOCKS_PORT_ID", "").strip() or None
        prefix = "B17_"
        id_key = "ASOCKS_PORT_ID"
        name_key = "ASOCKS_PORT_NAME"
        connect_key = "B17_PROXY_CONNECT_PORT"

    port = _pick_port(payload, port_name or default_name or None, default_id)
    template = port.get("template") or ""
    host, port_num, login = _parse_template(template)
    password = port.get("password") or ""
    login = port.get("login") or login
    # Only apply CONNECT_PORT for this target — do NOT fall back to B17 port for Telegram.
    # ASocks KZ template uses :9999; forcing :443 breaks HTTPS CONNECT (SSL EOF).
    connect_port = env.get(connect_key, "").strip()
    if connect_port.isdigit():
        port_num = connect_port

    result = {
        "target": target,
        "asocks_port_id": port.get("id"),
        "asocks_port_name": port.get("name"),
        f"{prefix}PROXY_SERVER": f"{host}:{port_num}",
        f"{prefix}PROXY_USERNAME": login,
        f"{prefix}PROXY_PASSWORD": password,
        "template": template,
    }

    if write and ENV_PATH.is_file():
        updates = {
            f"{prefix}PROXY_SERVER": result[f"{prefix}PROXY_SERVER"],
            f"{prefix}PROXY_USERNAME": result[f"{prefix}PROXY_USERNAME"],
            f"{prefix}PROXY_PASSWORD": result[f"{prefix}PROXY_PASSWORD"],
            id_key: str(result["asocks_port_id"] or ""),
            name_key: str(result["asocks_port_name"] or ""),
        }
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
        out: list[str] = []
        seen: set[str] = set()
        for line in lines:
            if line.strip().startswith("#") or "=" not in line:
                out.append(line)
                continue
            key = line.split("=", 1)[0].strip()
            if key in updates:
                val = updates[key]
                if key == "VPS_WEBHOOK_SECRET" or ";" in val or " " in val:
                    out.append(f'{key}="{val}"')
                else:
                    out.append(f"{key}={val}")
                seen.add(key)
            elif key in {"API_asocks", "Domen_asocks"}:
                continue
            else:
                out.append(line)
        for key, val in updates.items():
            if key not in seen and val:
                out.append(f"{key}={val}")
        ENV_PATH.write_text("\n".join(out).rstrip() + "\n", encoding="utf-8")
        result["written"] = str(ENV_PATH)

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Sync proxy from ASocks API → browser.env.local")
    parser.add_argument("--name", help="ASocks port name")
    parser.add_argument(
        "--target",
        choices=["b17", "telegram"],
        default="b17",
        help="b17 = B17_PROXY_* ; telegram = TELEGRAM_PROXY_* (KZ для Bot API)",
    )
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = sync_from_api(port_name=args.name, write=not args.dry_run, target=args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
