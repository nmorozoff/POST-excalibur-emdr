#!/usr/bin/env python3
"""Безопасно вызвать VPS webhook с правильным JSON и секретом.

Usage:
  python3 scripts/trigger-vps-webhook.py --topic sb-06-cant-sleep-anxiety
  python3 scripts/trigger-vps-webhook.py --topic sb-06 --dry-run

Читает секрет из:
  1) переменная окружения VPS_WEBHOOK_SECRET
  2) posts-emdr-memory/browser.env.local
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / "posts-emdr-memory" / "browser.env.local"


def check_on_main(*, skip: bool) -> None:
    if skip:
        return
    proc = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        capture_output=True,
        text=True,
        cwd=PROJECT_ROOT,
    )
    branch = (proc.stdout or "").strip()
    if branch and branch != "main":
        raise SystemExit(
            f"VPS webhook делает git pull origin main — сначала merge/push в main "
            f"(текущая ветка: {branch}). Для обхода: --skip-main-check"
        )


def load_secret() -> str:
    secret = os.environ.get("VPS_WEBHOOK_SECRET", "").strip()
    if secret:
        return secret
    if ENV_FILE.is_file():
        for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
            if line.strip().startswith("VPS_WEBHOOK_SECRET="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(
        "VPS_WEBHOOK_SECRET не найден. Установите в Cloud Secrets или browser.env.local"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Trigger VPS webhook with safe JSON")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--host", default="195.209.210.45")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--dry-run", action="store_true", help="Auth check only")
    parser.add_argument(
        "--skip-main-check",
        action="store_true",
        help="Не проверять, что локально на ветке main (VPS всё равно тянет main)",
    )
    args = parser.parse_args()

    check_on_main(skip=args.skip_main_check or args.dry_run)

    secret = load_secret()
    payload = {"topic": args.topic}
    if args.dry_run:
        payload["dry_run"] = True

    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"http://{args.host}:{args.port}/publish",
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            text = resp.read().decode("utf-8")
            data = json.loads(text) if text else {}
            print(json.dumps({"status": resp.status, **data}, ensure_ascii=False, indent=2))
            if resp.status != 202 and not (args.dry_run and resp.status == 200):
                sys.exit(2)
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        print(json.dumps({"status": e.code, "error": text[:500]}, ensure_ascii=False, indent=2))
        sys.exit(2)


if __name__ == "__main__":
    main()
