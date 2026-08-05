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
import sys
import time
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
        "VPS_WEBHOOK_SECRET не найден. Установите в Cloud Secrets или browser.env.local"
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Trigger VPS webhook with safe JSON")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--host", default="195.209.210.45")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--dry-run", action="store_true", help="Auth check only")
    args = parser.parse_args()

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
    last_err = None
    for attempt in range(1, 4):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                text = resp.read().decode("utf-8")
                data = json.loads(text) if text else {}
                print(json.dumps({"status": resp.status, **data}, ensure_ascii=False, indent=2))
                if resp.status == 202 or (args.dry_run and resp.status == 200):
                    sys.exit(0)
                sys.exit(2)
        except urllib.error.HTTPError as e:
            text = e.read().decode("utf-8", errors="replace")
            last_err = {"status": e.code, "error": text[:500]}
            if e.code in (401, 403):
                print(json.dumps(last_err, ensure_ascii=False, indent=2))
                sys.exit(2)
        except Exception as e:
            last_err = {"error": str(e)[:500]}
        if attempt < 3:
            wait = 10 * attempt
            print(json.dumps({"attempt": attempt, "wait_seconds": wait, **last_err}, ensure_ascii=False, indent=2))
            time.sleep(wait)

    print(json.dumps({"status": "timeout", "attempts": 3, **last_err}, ensure_ascii=False, indent=2))
    sys.exit(2)


if __name__ == "__main__":
    main()
