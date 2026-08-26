#!/usr/bin/env python3
"""Безопасно вызвать VPS webhook с правильным JSON и секретом.

Usage:
  python3 scripts/trigger-vps-webhook.py --topic sb-06-cant-sleep-anxiety
  python3 scripts/trigger-vps-webhook.py --topic sb-06 --wait-for-lock
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
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / "posts-emdr-memory" / "browser.env.local"

sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
from vps_webhook_client import post_json, probe_health


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


def _post_publish(
    base: str,
    secret: str,
    payload: dict,
    *,
    timeout: float,
) -> tuple[int, dict]:
    return post_json(f"{base}/publish", secret, payload, timeout=timeout)


def main() -> None:
    parser = argparse.ArgumentParser(description="Trigger VPS webhook with safe JSON")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--host", default="195.209.210.45")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--dry-run", action="store_true", help="Auth check only")
    parser.add_argument("--timeout", type=int, default=90, help="POST /publish timeout seconds")
    parser.add_argument("--health-timeout", type=int, default=10, help="GET /health timeout seconds")
    parser.add_argument("--skip-health", action="store_true", help="Skip GET /health pre-check")
    parser.add_argument(
        "--wait-for-lock",
        action="store_true",
        default=True,
        help="При 409 publish_lock_held ждать и повторять (default: on)",
    )
    parser.add_argument(
        "--no-wait-for-lock",
        action="store_false",
        dest="wait_for_lock",
        help="Сразу fail при 409",
    )
    parser.add_argument(
        "--lock-wait-sec",
        type=int,
        default=2400,
        help="Макс. ожидание освобождения lock при 409 (сек)",
    )
    parser.add_argument(
        "--lock-poll-sec",
        type=int,
        default=60,
        help="Интервал опроса при 409 (сек)",
    )
    args = parser.parse_args()

    secret = load_secret()
    base = f"http://{args.host}:{args.port}"

    if not args.skip_health:
        health_ok, health = probe_health(args.host, args.port, timeout=args.health_timeout)
        if not health_ok:
            print(json.dumps({"health_ok": False, **health}, ensure_ascii=False, indent=2))
            if health.get("vps_down"):
                sys.exit(3)
            sys.exit(2)

    payload = {"topic": args.topic}
    if args.dry_run:
        payload["dry_run"] = True

    deadline = time.time() + max(args.lock_wait_sec, 0)
    last_err: dict = {}
    lock_waits = 0

    while True:
        status, data = _post_publish(
            base,
            secret,
            payload,
            timeout=float(args.timeout),
        )
        if status in (202, 200):
            print(json.dumps({"status": status, **data}, ensure_ascii=False, indent=2))
            if status == 202 or (args.dry_run and status == 200):
                sys.exit(0)
            sys.exit(2)
        if status == 409:
            last_err = {"status": 409, "accepted": False, "busy": True, **data}
            if not args.wait_for_lock or time.time() >= deadline:
                print(json.dumps(last_err, ensure_ascii=False, indent=2))
                sys.exit(4)
            lock_waits += 1
            print(
                json.dumps(
                    {
                        **last_err,
                        "action": "wait_for_lock",
                        "lock_wait_attempt": lock_waits,
                        "sleep_sec": args.lock_poll_sec,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            time.sleep(args.lock_poll_sec)
            continue
        if status in (401, 403):
            print(json.dumps({"status": status, **data}, ensure_ascii=False, indent=2))
            sys.exit(2)
        last_err = {"status": status, **data} if status else data
        if data.get("vps_down"):
            break
        # transient network — short retry
        if time.time() < deadline:
            time.sleep(15)
            continue
        break

    print(json.dumps({"status": "failed", **last_err}, ensure_ascii=False, indent=2))
    sys.exit(3 if last_err.get("vps_down") else 2)


if __name__ == "__main__":
    main()
