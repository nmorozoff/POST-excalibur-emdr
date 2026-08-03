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
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
WORKER = PROJECT_ROOT / "scripts" / "run-linux-browser-worker.sh"


def _git_pull() -> dict:
    env_file = PROJECT_ROOT / "posts-emdr-memory" / "github.env.local"
    env = os.environ.copy()
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    token = env.get("GITHUB_TOKEN", "").strip()
    if not (PROJECT_ROOT / ".git").is_dir():
        return {"ok": False, "reason": "no_git"}
    if token:
        url = f"https://{token}@github.com/nmorozoff/POST-excalibur-emdr.git"
        proc = subprocess.run(
            ["git", "pull", url, "main"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env=env,
        )
    else:
        proc = subprocess.run(
            ["git", "pull", "--ff-only", "origin", "main"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env=env,
        )
    return {
        "ok": proc.returncode == 0,
        "stdout_tail": (proc.stdout or "")[-500:],
        "stderr_tail": (proc.stderr or "")[-500:],
    }


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
        pull = _git_pull()

        if topic:
            # cover may be gitignored — fetch from site/FTP
            subprocess.run(
                [
                    sys.executable,
                    str(PROJECT_ROOT / "scripts" / "fetch-topic-cover.py"),
                    "--topic",
                    topic,
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
                env=env,
            )
            cmd = [
                sys.executable,
                str(PROJECT_ROOT / "scripts" / "publish-browser-deferred.py"),
                "--topic",
                topic,
                "--submit",
                "--finish",
                "--git-push",
            ]
        else:
            cmd = [str(WORKER)]

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
                "git_pull": pull,
                "log": str(log_path),
                "note": "publish running in background; poll output logs / git for completion",
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
    server = HTTPServer((args.host, args.port), WebhookHandler)
    print(json.dumps({"status": "listening", "host": args.host, "port": args.port}, indent=2))
    server.serve_forever()


if __name__ == "__main__":
    main()
