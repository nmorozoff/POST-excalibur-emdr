#!/usr/bin/env python3
"""Безопасно вызвать VPS webhook с правильным JSON и секретом.

Usage:
  python3 scripts/trigger-vps-webhook.py --topic sb-06-cant-sleep-anxiety
  python3 scripts/trigger-vps-webhook.py --topic sb-06 --dry-run
  python3 scripts/trigger-vps-webhook.py --topic sb-08 --timeout 120

Читает секрет из:
  1) переменная окружения VPS_WEBHOOK_SECRET
  2) posts-emdr-memory/browser.env.local
"""

from __future__ import annotations

import argparse
import json
import os
import socket
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
        "VPS_WEBHOOK_SECRET не найден. Установите в Cloud Secrets или browser.env.local"
    )


def probe_health(host: str, port: int, *, timeout: int = 10) -> dict:
    url = f"http://{host}:{port}/health"
    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8", errors="replace")
            data = json.loads(text) if text.strip().startswith("{") else {"raw": text[:200]}
            return {"ok": resp.status == 200, "status": resp.status, **data}
    except urllib.error.HTTPError as e:
        return {"ok": False, "status": e.code, "error": e.read().decode("utf-8", errors="replace")[:300]}
    except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
        return {"ok": False, "error": str(e)}


def main() -> None:
    parser = argparse.ArgumentParser(description="Trigger VPS webhook with safe JSON")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--host", default="195.209.210.45")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--dry-run", action="store_true", help="Auth check only")
    parser.add_argument(
        "--timeout",
        type=int,
        default=90,
        help="HTTP read timeout seconds for POST /publish (default 90)",
    )
    parser.add_argument(
        "--skip-health",
        action="store_true",
        help="Skip GET /health pre-check",
    )
    args = parser.parse_args()

    secret = load_secret()
    payload = {"topic": args.topic}
    if args.dry_run:
        payload["dry_run"] = True

    if not args.skip_health:
        health = probe_health(args.host, args.port)
        print(json.dumps({"health_check": health}, ensure_ascii=False, indent=2))
        if not health.get("ok") and not args.dry_run:
            print(
                json.dumps(
                    {
                        "warning": "health check failed; continuing POST anyway",
                        "hint": "VPS: systemctl status posts-emdr-webhook; curl /health on VPS",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )

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
        with urllib.request.urlopen(req, timeout=args.timeout) as resp:
            text = resp.read().decode("utf-8")
            data = json.loads(text) if text else {}
            print(json.dumps({"status": resp.status, **data}, ensure_ascii=False, indent=2))
            if resp.status != 202 and not (args.dry_run and resp.status == 200):
                sys.exit(2)
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        print(json.dumps({"status": e.code, "error": text[:500]}, ensure_ascii=False, indent=2))
        sys.exit(2)
    except (urllib.error.URLError, TimeoutError, socket.timeout) as e:
        print(
            json.dumps(
                {
                    "error": "TimeoutError",
                    "detail": str(e),
                    "host": args.host,
                    "port": args.port,
                    "timeout_seconds": args.timeout,
                    "recovery": [
                        f"curl -fsS http://{args.host}:{args.port}/health",
                        "VPS: systemctl is-active posts-emdr-webhook",
                        f"python3 scripts/trigger-vps-webhook.py --topic {args.topic} --timeout 120",
                    ],
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        sys.exit(2)


if __name__ == "__main__":
    main()
