#!/usr/bin/env python3
"""Materialize VPS secrets (telegram + browser) from process environment.

Run on VPS before webhook worker / cron (systemd ExecStartPre):
  python3 scripts/materialize_vps_env.py

systemd EnvironmentFile vars are copied into posts-emdr-memory/*.env.local so
send-telegram-post.py and publish-browser-deferred always see fresh secrets.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import PROJECT_ROOT, materialize_vps_runtime_env

if __name__ == "__main__":
    report = materialize_vps_runtime_env()
    print(json.dumps({"project_root": str(PROJECT_ROOT), **report}, ensure_ascii=False, indent=2))
    tg = report.get("telegram") or {}
    if not tg.get("ok") and not (PROJECT_ROOT / "posts-emdr-memory" / "telegram.env.local").is_file():
        sys.exit(2)
