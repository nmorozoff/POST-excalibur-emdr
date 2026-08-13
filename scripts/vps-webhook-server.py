#!/usr/bin/env python3
"""Minimal webhook: cloud automation → instant VPS phase 3 (Telegram+b17; TenChat out of MSP scope).

Usage on VPS (systemd):
  EnvironmentFile=.../browser.env.local
  python3 scripts/vps-webhook-server.py --port 8787

Cloud automation (last step after git push):
  curl -fsS -X POST "http://195.209.210.45:8787/publish" \\
    -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \\
    -H "Content-Type: application/json" \\
    -d '{"topic":"sb-05-tolerate-uncertainty"}'
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"
WORKER = SCRIPTS / "run-linux-browser-worker.sh"

sys.path.insert(0, str(SCRIPTS))
from posts_emdr_env import materialize_telegram_env_from_os
from vps_publish_guard import lock_held


def _ensure_telegram_env() -> dict[str, object]:
    return materialize_telegram_env_from_os()


class WebhookHandler(BaseHTTPRequestHandler):
    secret = ""

    def _auth_ok(self) -> bool:
        expected = f"Bearer {self.secret}".strip()
        got = self.headers.get("Authorization", "").strip()
        return bool(self.secret) and got == expected

    def _json(self, code: int, payload: dict) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        if self.path in ("/health", "/health/", "/"):
            self._json(200, {"ok": True, "service": "posts-emdr-webhook"})
            return
        self._json(404, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        if self.path not in ("/publish", "/publish/"):
            self._json(404, {"error": "not found"})
            return
        if not self._auth_ok():
            self._json(401, {"error": "unauthorized"})
            return
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except json.JSONDecodeError:
            self._json(400, {"error": "invalid json"})
            return

        topic = (data.get("topic") or "").strip()
        env = os.environ.copy()
        env["POSTS_EMDR_ROOT"] = str(PROJECT_ROOT)

        # Sync telegram/browser secrets from systemd EnvironmentFile → *.env.local
        subprocess.run(
            [sys.executable, str(PROJECT_ROOT / "scripts" / "materialize_vps_env.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env=env,
        )

        if data.get("dry_run") or data.get("auth_check"):
            self._json(200, {"ok": True, "auth": "ok", "dry_run": True, "topic": topic or None})
            return

        # Reject concurrent publish before spawning (flock also held inside guard run).
        if lock_held():
            self._json(
                409,
                {
                    "ok": False,
                    "accepted": False,
                    "status": "busy",
                    "error": "publish_lock_held",
                    "topic": topic or None,
                    "note": "another VPS publish is running; retry later — do not force a second TG send",
                },
            )
            return

        telegram_env = _ensure_telegram_env()

        if topic:
            # Cover fetch + deferred publish share one flock (git pull inside guard).
            import shlex

            t = shlex.quote(topic)
            worker_cmd = (
                f"{sys.executable} {shlex.quote(str(PROJECT_ROOT / 'scripts' / 'fetch-topic-cover.py'))} "
                f"--topic {t}; "
                f"{sys.executable} {shlex.quote(str(PROJECT_ROOT / 'scripts' / 'publish-browser-deferred.py'))} "
                f"--topic {t} --submit --finish --git-push"
            )
            cmd = [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "vps_publish_guard.py"),
                "run",
                "--",
                "bash",
                "-lc",
                worker_cmd,
            ]
        else:
            cmd = [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "vps_publish_guard.py"),
                "run",
                "--",
                str(WORKER),
            ]

        # Async: do not block HTTP thread (Playwright can take many minutes).
        log_path = PROJECT_ROOT / "posts-emdr-memory" / "output" / (topic or "_cron") / "vps-webhook-run.log"
        if topic:
            log_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            log_path = PROJECT_ROOT / "posts-emdr-memory" / "vps-webhook-cron.log"
        log_f = open(log_path, "ab", buffering=0)
        proc = subprocess.Popen(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=log_f,
            stderr=subprocess.STDOUT,
            env=env,
            start_new_session=True,
        )
        self._json(
            202,
            {
                "ok": True,
                "accepted": True,
                "pid": proc.pid,
                "topic": topic or None,
                "telegram_env": telegram_env,
                "log": str(log_path),
                "lock": "vps_publish_guard",
                "note": "publish running in background under flock; poll output logs / git for completion",
            },
        )

    def log_message(self, fmt: str, *args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    secret = os.environ.get("VPS_WEBHOOK_SECRET", "").strip().strip('"')
    if not secret:
        # fallback: browser.env.local
        env_path = PROJECT_ROOT / "posts-emdr-memory" / "browser.env.local"
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("VPS_WEBHOOK_SECRET="):
                    secret = line.split("=", 1)[1].strip().strip('"').strip("'")
                    break
    if not secret:
        raise SystemExit("Set VPS_WEBHOOK_SECRET in environment or browser.env.local")

    WebhookHandler.secret = secret
    telegram_env = _ensure_telegram_env()
    server = HTTPServer((args.host, args.port), WebhookHandler)
    print(
        json.dumps(
            {
                "status": "listening",
                "host": args.host,
                "port": args.port,
                "telegram_env": telegram_env,
            },
            indent=2,
        )
    )
    server.serve_forever()


if __name__ == "__main__":
    main()
