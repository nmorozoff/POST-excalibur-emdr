#!/usr/bin/env python3
"""Sync B17 proxy settings from ASocks API into browser.env.local fields."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
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


def _proxy_ports(payload: dict) -> list[dict]:
    message = payload.get("message") or {}
    return message.get("proxies") or payload.get("data") or []


def _pick_port(payload: dict, name: str | None, port_id: str | None) -> dict:
    proxies = _proxy_ports(payload)
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


def _telegram_port_candidates(payload: dict, env: dict[str, str]) -> list[dict]:
    """Order: configured default → env fallback names → other KZ ports."""
    proxies = _proxy_ports(payload)
    if not proxies:
        return []

    default_name = env.get("TELEGRAM_ASOCKS_PORT_NAME", "ResKazakhstan - Turkestan").strip()
    default_id = env.get("TELEGRAM_ASOCKS_PORT_ID", "").strip() or None
    fallback_names = [
        item.strip()
        for item in env.get("TELEGRAM_ASOCKS_FALLBACK_NAMES", "").split(",")
        if item.strip()
    ]

    ordered: list[dict] = []
    seen_ids: set[str] = set()

    def add_port(port: dict | None) -> None:
        if not port:
            return
        pid = str(port.get("id") or "")
        if pid and pid in seen_ids:
            return
        if pid:
            seen_ids.add(pid)
        ordered.append(port)

    add_port(_pick_port(payload, default_name or None, default_id))
    for name in fallback_names:
        add_port(_pick_port(payload, name, None))
    for port in proxies:
        if (port.get("countryCode") or "").upper() == "KZ":
            add_port(port)
    return ordered


def test_proxy_tunnel(
    server: str,
    user: str,
    password: str,
    *,
    test_url: str = "https://api.telegram.org",
    max_time_sec: int = 25,
) -> dict:
    proxy = f"http://{user}:{password}@{server}"
    cmd = [
        "/usr/bin/curl",
        "-sS",
        "-o",
        "/dev/null",
        "-w",
        "%{http_code}",
        "--max-time",
        str(max_time_sec),
        "--proxy",
        proxy,
        test_url,
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    code = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    ok = code.isdigit() and int(code) > 0
    return {
        "http_code": code,
        "ok": ok,
        "error": err or None,
        "proxy_server": server,
        "test_url": test_url,
    }


def _build_sync_result(port: dict, *, target: str, env: dict[str, str]) -> dict:
    if target == "telegram":
        prefix = "TELEGRAM_"
        connect_key = "TELEGRAM_PROXY_CONNECT_PORT"
    else:
        prefix = "B17_"
        connect_key = "B17_PROXY_CONNECT_PORT"

    template = port.get("template") or ""
    host, port_num, login = _parse_template(template)
    password = port.get("password") or ""
    login = port.get("login") or login
    connect_port = env.get(connect_key, "").strip()
    if connect_port.isdigit():
        port_num = connect_port

    return {
        "target": target,
        "asocks_port_id": port.get("id"),
        "asocks_port_name": port.get("name"),
        f"{prefix}PROXY_SERVER": f"{host}:{port_num}",
        f"{prefix}PROXY_USERNAME": login,
        f"{prefix}PROXY_PASSWORD": password,
        "template": template,
    }


def _write_env_updates(updates: dict[str, str]) -> None:
    if not ENV_PATH.is_file():
        return
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


def sync_telegram_with_preflight(
    *,
    write: bool = True,
    max_time_sec: int = 25,
    exclude_port_ids: set[str] | None = None,
) -> dict:
    """Sync TELEGRAM_PROXY_* and rotate KZ ASocks ports until curl preflight passes."""
    env = load_env("browser.env.local")
    api_key = env.get("ASOCKS_API_KEY", "").strip()
    base = env.get("ASOCKS_API_BASE", "https://api.asocks.com").strip()
    if not api_key:
        raise SystemExit("Missing ASOCKS_API_KEY in browser.env.local")

    payload = _api_get("/v2/proxy/ports", api_key, base)
    if not payload.get("success"):
        raise SystemExit(f"ASocks API error: {payload}")

    candidates = _telegram_port_candidates(payload, env)
    if not candidates:
        raise SystemExit("ASocks: no telegram proxy candidates")

    attempts: list[dict] = []
    last_result: dict | None = None
    skip_ids = exclude_port_ids or set()
    for port in candidates:
        pid = str(port.get("id") or "")
        if pid and pid in skip_ids:
            continue
        result = _build_sync_result(port, target="telegram", env=env)
        last_result = result
        proxy_test = test_proxy_tunnel(
            result["TELEGRAM_PROXY_SERVER"],
            result["TELEGRAM_PROXY_USERNAME"],
            result["TELEGRAM_PROXY_PASSWORD"],
            max_time_sec=max_time_sec,
        )
        attempts.append(
            {
                "asocks_port_name": result.get("asocks_port_name"),
                "proxy_test": proxy_test,
            }
        )
        if proxy_test["ok"]:
            if write and ENV_PATH.is_file():
                _write_env_updates(
                    {
                        "TELEGRAM_PROXY_SERVER": result["TELEGRAM_PROXY_SERVER"],
                        "TELEGRAM_PROXY_USERNAME": result["TELEGRAM_PROXY_USERNAME"],
                        "TELEGRAM_PROXY_PASSWORD": result["TELEGRAM_PROXY_PASSWORD"],
                        "TELEGRAM_ASOCKS_PORT_ID": str(result["asocks_port_id"] or ""),
                        "TELEGRAM_ASOCKS_PORT_NAME": str(result["asocks_port_name"] or ""),
                    }
                )
                result["written"] = str(ENV_PATH)
            result["preflight_ok"] = True
            result["attempts"] = attempts
            return result

    assert last_result is not None
    if write and ENV_PATH.is_file():
        _write_env_updates(
            {
                "TELEGRAM_PROXY_SERVER": last_result["TELEGRAM_PROXY_SERVER"],
                "TELEGRAM_PROXY_USERNAME": last_result["TELEGRAM_PROXY_USERNAME"],
                "TELEGRAM_PROXY_PASSWORD": last_result["TELEGRAM_PROXY_PASSWORD"],
                "TELEGRAM_ASOCKS_PORT_ID": str(last_result["asocks_port_id"] or ""),
                "TELEGRAM_ASOCKS_PORT_NAME": str(last_result["asocks_port_name"] or ""),
            }
        )
        last_result["written"] = str(ENV_PATH)
    last_result["preflight_ok"] = False
    last_result["attempts"] = attempts
    return last_result


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
    result = _build_sync_result(port, target=target, env=env)

    if write and ENV_PATH.is_file():
        updates = {
            f"{prefix}PROXY_SERVER": result[f"{prefix}PROXY_SERVER"],
            f"{prefix}PROXY_USERNAME": result[f"{prefix}PROXY_USERNAME"],
            f"{prefix}PROXY_PASSWORD": result[f"{prefix}PROXY_PASSWORD"],
            id_key: str(result["asocks_port_id"] or ""),
            name_key: str(result["asocks_port_name"] or ""),
        }
        _write_env_updates(updates)
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
    parser.add_argument(
        "--preflight",
        action="store_true",
        help="For --target telegram: rotate KZ ports until curl preflight to api.telegram.org passes",
    )
    args = parser.parse_args()
    if args.target == "telegram" and args.preflight:
        result = sync_telegram_with_preflight(write=not args.dry_run)
    else:
        result = sync_from_api(port_name=args.name, write=not args.dry_run, target=args.target)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
