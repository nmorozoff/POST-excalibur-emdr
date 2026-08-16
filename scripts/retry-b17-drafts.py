#!/usr/bin/env python3
"""Retry b17 topics stuck in draft_saved (rate-limit). Publishes up to --limit per run.

Usage (VPS cron, before deferred worker):
  python3 scripts/retry-b17-drafts.py --limit 1
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY

SCRIPTS = Path(__file__).resolve().parent


def find_draft_topics() -> list[str]:
    topics: list[str] = []
    for log_path in sorted((MEMORY / "output").glob("*/b17-publish-log.json")):
        try:
            data = json.loads(log_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if data.get("status") == "draft_saved":
            topics.append(log_path.parent.name)
    return topics


def main() -> None:
    parser = argparse.ArgumentParser(description="Retry b17 draft_saved topics")
    parser.add_argument("--limit", type=int, default=1, help="Max topics per run (rate-limit safe)")
    parser.add_argument("--sleep-sec", type=int, default=90, help="Pause before submit when retrying")
    args = parser.parse_args()

    topics = find_draft_topics()[: max(args.limit, 0)]
    if not topics:
        print(json.dumps({"status": "ok", "published": [], "note": "no draft_saved topics"}, indent=2))
        return

    results: list[dict] = []
    for index, topic in enumerate(topics):
        if index > 0 and args.sleep_sec > 0:
            time.sleep(args.sleep_sec)
        elif index == 0 and args.sleep_sec > 0:
            time.sleep(args.sleep_sec)
        proc = subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "publish-b17-blog.py"),
                "--topic",
                topic,
                "--submit",
            ],
            capture_output=True,
            text=True,
        )
        log_path = MEMORY / "output" / topic / "b17-publish-log.json"
        status = None
        if log_path.is_file():
            try:
                status = json.loads(log_path.read_text(encoding="utf-8")).get("status")
            except (json.JSONDecodeError, OSError):
                pass
        results.append(
            {
                "topic": topic,
                "exit_code": proc.returncode,
                "status": status,
                "stderr_tail": (proc.stderr or "")[-400:],
            }
        )

    failed = [r for r in results if r.get("status") != "published"]
    print(json.dumps({"status": "ok" if not failed else "partial", "results": results}, indent=2))
    sys.exit(0 if not failed else 2)


if __name__ == "__main__":
    main()
