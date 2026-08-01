#!/usr/bin/env python3
"""ASocks health check: balance, sync proxy creds, test tunnel."""

from __future__ import annotations

import json
import subprocess
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asocks_sync_proxy import sync_from_api
from posts_emdr_env import load_env


def _api_get(path: str) -> dict:
    env = load_env("browser.env.local")
    api_key = env.get("ASOCKS_API_KEY", "").strip()
    base = env.get("ASOCKS_API_BASE", "https://api.asocks.com").strip()
    if not api_key:
        raise SystemExit("Missing ASOCKS_API_KEY in browser.env.local")
    url = f"{base.rstrip('/')}{path}"
    sep = "&" if "?" in url else "?"
    url = f"{url}{sep}apiKey={urllib.parse.quote(api_key)}"
    with urllib.request.urlopen(
        urllib.request.Request(url, headers={"Accept": "application/json"}), timeout=45
    ) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _test_proxy(server: str, user: str, password: str) -> dict:
    proxy = f"http://{user}:{password}@{server}"
    cmd = [
        "/usr/bin/curl",
        "-sS",
        "-o",
        "/dev/null",
        "-w",
        "%{http_code}",
        "--max-time",
        "25",
        "--proxy",
        proxy,
        "https://api.ipify.org?format=json",
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    code = (proc.stdout or "").strip()
    err = (proc.stderr or "").strip()
    return {
        "http_code": code,
        "ok": code == "200",
        "error": err or None,
        "proxy_server": server,
    }


def main() -> None:
    balance = _api_get("/v2/user/balance")
    synced = sync_from_api(write=True)
    proxy_test = _test_proxy(
        synced["B17_PROXY_SERVER"],
        synced["B17_PROXY_USERNAME"],
        synced["B17_PROXY_PASSWORD"],
    )

    traffic = float(balance.get("all_available_traffic") or 0)
    money = float(balance.get("balance") or 0)
    hints: list[str] = []
    if traffic <= 0 and money > 0:
        hints.append(
            "На аккаунте есть деньги ($), но traffic=0 — в кабинете ASocks купите/активируйте трафик (Pay as you go)."
        )
    if not proxy_test["ok"]:
        hints.append(
            "407 = прокси не пускает. В кабинете ASocks: Whitelist → добавить 195.209.210.45; "
            "тип авторизации порта → Password Authorization."
        )
        hints.append(
            "Синхронизация: python3 scripts/asocks_sync_proxy.py && python3 scripts/asocks_check.py"
        )

    result = {
        "balance": balance,
        "proxy": synced,
        "proxy_test": proxy_test,
        "hints": hints,
        "ok": proxy_test["ok"] and traffic > 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if proxy_test["ok"] else 2)


if __name__ == "__main__":
    main()
