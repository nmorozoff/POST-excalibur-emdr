#!/usr/bin/env python3
"""Записать результат публикации OK после MCP ok_create_post_with_photo.

Usage:
  python3 scripts/record-ok-publish.py --topic sb-09-one-question-calms \\
    --url "https://ok.ru/group/70000034253679/topic/1234567890" \\
    --mediatopic-id "1234567890" \\
    --title "Заголовок" \\
    --site-url "https://morozovanatalia.ru/anxiety" \\
    --tags "тревога,EMDR"
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, ok_group_gid

SCRIPTS = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser(description="Record OK publish log + registry")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--url", required=True, help="Public URL of OK topic")
    parser.add_argument("--mediatopic-id", default="", help="OK mediatopic / topic id")
    parser.add_argument("--title", required=True)
    parser.add_argument("--site-url", required=True)
    parser.add_argument("--tags", default="")
    parser.add_argument("--gid", default="", help="OK group GID (default from env)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    topic_dir = MEMORY / "output" / args.topic
    if not topic_dir.is_dir():
        raise SystemExit(f"Missing output/{args.topic}")

    gid = args.gid or ok_group_gid()
    log = {
        "topic": args.topic,
        "platform": "ok",
        "status": "published",
        "gid": gid,
        "group_url": f"https://ok.ru/group/{gid}",
        "url": args.url,
        "post_url": args.url,
        "mediatopic_id": args.mediatopic_id or None,
        "title": args.title,
        "site_url": args.site_url,
        "tags": args.tags,
        "date": date.today().isoformat(),
    }

    if args.dry_run:
        print(json.dumps(log, ensure_ascii=False, indent=2))
        return

    log_path = topic_dir / "ok-publish-log.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "update-post-registry.py"),
            "--platform",
            "ok",
            "--topic-id",
            args.topic,
            "--title",
            args.title,
            "--url",
            args.url,
            "--site-url",
            args.site_url,
            "--tags",
            args.tags,
            "--mediatopic-id",
            args.mediatopic_id or "?",
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(f"update-post-registry failed:\n{proc.stderr}")

    print(json.dumps({"status": "ok", "log": str(log_path), "url": args.url}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
