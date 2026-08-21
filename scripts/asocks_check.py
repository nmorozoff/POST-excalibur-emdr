#!/usr/bin/env python3
"""ASocks health check: balance, sync proxy creds, test tunnel."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from asocks_sync_proxy import sync_from_api, sync_telegram_with_preflight, test_proxy_tunnel
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


def main() -> None:
    parser = argparse.ArgumentParser(description="ASocks balance + proxy tunnel health check")
    parser.add_argument(
        "--target",
        choices=["b17", "telegram"],
        default="b17",
        help="b17 = ipify via B17 proxy; telegram = api.telegram.org via TELEGRAM proxy",
    )
    parser.add_argument(
        "--rotate",
        action="store_true",
        help="For telegram: sync with KZ port rotation until preflight passes",
    )
    args = parser.parse_args()

    balance = _api_get("/v2/user/balance")
    if args.target == "telegram" and args.rotate:
        synced = sync_telegram_with_preflight(write=True)
        proxy_test = (synced.get("attempts") or [{}])[-1].get("proxy_test") or {}
    elif args.target == "telegram":
        synced = sync_from_api(write=True, target="telegram")
        proxy_test = test_proxy_tunnel(
            synced["TELEGRAM_PROXY_SERVER"],
            synced["TELEGRAM_PROXY_USERNAME"],
            synced["TELEGRAM_PROXY_PASSWORD"],
        )
    else:
        synced = sync_from_api(write=True, target="b17")
        proxy_test = test_proxy_tunnel(
            synced["B17_PROXY_SERVER"],
            synced["B17_PROXY_USERNAME"],
            synced["B17_PROXY_PASSWORD"],
            test_url="https://api.ipify.org?format=json",
        )

    traffic = float(balance.get("all_available_traffic") or 0)
    money = float(balance.get("balance") or 0)
    hints: list[str] = []
    if traffic <= 0 and money > 0:
        hints.append(
            "На аккаунте есть деньги ($), но traffic=0 — в кабинете ASocks купите/активируйте трафик (Pay as you go)."
        )
    if not proxy_test.get("ok"):
        hints.append(
            "407 = прокси не пускает. В кабинете ASocks: Whitelist → добавить 195.209.210.45; "
            "тип авторизации порта → Password Authorization."
        )
        if args.target == "telegram":
            hints.append(
                "Telegram timeout/SSL: python3 scripts/asocks_sync_proxy.py --target telegram --preflight "
                "или python3 scripts/asocks_check.py --target telegram --rotate"
            )
        else:
            hints.append(
                "Синхронизация: python3 scripts/asocks_sync_proxy.py && python3 scripts/asocks_check.py"
            )

    result = {
        "target": args.target,
        "balance": balance,
        "proxy": synced,
        "proxy_test": proxy_test,
        "hints": hints,
        "ok": proxy_test.get("ok") and traffic > 0,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if proxy_test.get("ok") else 2)


if __name__ == "__main__":
    main()
