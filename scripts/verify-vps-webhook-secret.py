#!/usr/bin/env python3
"""Проверить, что VPS_WEBHOOK_SECRET в Cloud совпадает с VPS.

Читает секрет из:
  1) переменной окружения VPS_WEBHOOK_SECRET
  2) posts-emdr-memory/browser.env.local (локальная копия, если есть)

Тесты (без запуска публикации):
  - неверный Bearer → HTTP 401
  - верный Bearer + {"dry_run": true} → HTTP 200 auth ok

Usage:
  VPS_WEBHOOK_SECRET='ваш-секрет' python3 scripts/verify-vps-webhook-secret.py
  python3 scripts/verify-vps-webhook-secret.py --host 195.209.210.45 --port 8787
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / "posts-emdr-memory" / "browser.env.local"


def load_secret() -> str:
    secret = os.environ.get("VPS_WEBHOOK_SECRET", "").strip()
    if secret:
        return secret
    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("VPS_WEBHOOK_SECRET="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(
        "VPS_WEBHOOK_SECRET не найден.\n"
        "Вставьте тот же секрет, что в Cursor Cloud Secrets:\n"
        "  VPS_WEBHOOK_SECRET='...' python3 scripts/verify-vps-webhook-secret.py"
    )


def post_json(url: str, secret: str, payload: dict) -> tuple[int, dict]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            text = resp.read().decode("utf-8")
            return resp.status, json.loads(text) if text else {}
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(text) if text else {}
        except json.JSONDecodeError:
            data = {"raw": text[:200]}
        return e.code, data


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify VPS webhook secret matches")
    parser.add_argument("--host", default="195.209.210.45")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    secret = load_secret()
    base = f"http://{args.host}:{args.port}"

    # health
    with urllib.request.urlopen(f"{base}/health", timeout=10) as resp:
        health = json.loads(resp.read().decode("utf-8"))
    if not health.get("ok"):
        raise SystemExit(f"Health check failed: {health}")

    wrong_code, wrong_body = post_json(f"{base}/publish", "wrong-secret-test", {"dry_run": True})
    ok_code, ok_body = post_json(f"{base}/publish", secret, {"dry_run": True})

    result = {
        "health": health,
        "wrong_secret_status": wrong_code,
        "wrong_secret_ok": wrong_code == 401,
        "correct_secret_status": ok_code,
        "correct_secret_ok": ok_code == 200 and ok_body.get("auth") == "ok",
        "hint": (
            "Секрет совпадает — можно использовать в Cloud automation curl webhook."
            if ok_code == 200
            else "Секрет НЕ совпадает. Сверьте Cloud Secrets и VPS browser.env.local"
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["wrong_secret_ok"] or not result["correct_secret_ok"]:
        sys.exit(2)


if __name__ == "__main__":
    main()
