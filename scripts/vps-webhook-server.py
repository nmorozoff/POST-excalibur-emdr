#!/usr/bin/env python3
"""Minimal webhook: cloud automation → instant VPS phase 3 (no Mac).

Usage on VPS (systemd or screen):
  export VPS_WEBHOOK_SECRET=your-secret
  python3 scripts/vps-webhook-server.py --port 8787

Cloud automation (last step):
  curl -fsS -X POST "http://195.209.210.45:8787/publish" \\
    -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \\
    -H "Content-Type: application/json" \\
    -d '{"topic":"sb-04-what-if-phrase"}'
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKER = PROJECT_ROOT / "scripts" / "run-linux-browser-worker.sh"


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
        if topic:
            cmd = [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "publish-browser-deferred.py"),
                "--topic",
                topic,
                "--submit",
                "--finish",
            ]
        else:
            cmd = [str(WORKER)]

        proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True, env=env)
        self._json(
            200 if proc.returncode == 0 else 500,
            {
                "ok": proc.returncode == 0,
                "topic": topic or None,
                "stdout_tail": (proc.stdout or "")[-3000:],
                "stderr_tail": (proc.stderr or "")[-1500:],
            },
        )

    def log_message(self, fmt: str, *args: object) -> None:
        return


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args()

    secret = os.environ.get("VPS_WEBHOOK_SECRET", "").strip()
    if not secret:
        raise SystemExit("Set VPS_WEBHOOK_SECRET in environment")

    WebhookHandler.secret = secret
    server = HTTPServer((args.host, args.port), WebhookHandler)
    print(json.dumps({"status": "listening", "host": args.host, "port": args.port}, indent=2))
    server.serve_forever()


if __name__ == "__main__":
    main()
