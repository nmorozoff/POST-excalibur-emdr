#!/usr/bin/env python3
"""Записать VK после MCP vk_create_post_with_photo."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY

SCRIPTS = Path(__file__).resolve().parent
WALL_RE = re.compile(r"wall(-?\d+)_(\d+)")


def _parse_wall(wall_url: str) -> tuple[str, str]:
    m = WALL_RE.search(wall_url)
    if not m:
        raise SystemExit(f"Cannot parse VK wall URL: {wall_url}")
    return m.group(1), m.group(2)


def main() -> None:
    parser = argparse.ArgumentParser(description="Record VK MCP publish")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--location", choices=("personal", "group"), required=True)
    parser.add_argument("--wall-url", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--site-url", required=True)
    parser.add_argument("--tags", default="")
    parser.add_argument("--from-group", action="store_true")
    args = parser.parse_args()

    topic_dir = MEMORY / "output" / args.topic
    handoff_path = topic_dir / "vk-mcp-handoff.json"
    cover_url = ""
    if handoff_path.is_file():
        try:
            cover_url = json.loads(handoff_path.read_text(encoding="utf-8")).get("cover_public_url") or ""
        except json.JSONDecodeError:
            pass

    owner, post_id = _parse_wall(args.wall_url)
    entry = {
        "topic": args.topic,
        "location": args.location,
        "from_group": args.from_group or args.location == "group",
        "status": "published",
        "post_id": int(post_id),
        "wall_url": args.wall_url,
        "photo_url": cover_url,
        "date": date.today().isoformat(),
        "via": "mcp-kv",
    }

    log_path = topic_dir / "vk-publish-log.json"
    rows: list[dict] = []
    if log_path.is_file():
        try:
            raw = json.loads(log_path.read_text(encoding="utf-8"))
            rows = raw if isinstance(raw, list) else [raw]
        except json.JSONDecodeError:
            rows = []
    rows = [r for r in rows if r.get("location") != args.location]
    rows.append(entry)
    log_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    platform = "vk-group" if args.location == "group" else "vk-profile"
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "update-post-registry.py"),
            "--platform",
            platform,
            "--topic-id",
            args.topic,
            "--title",
            args.title,
            "--url",
            args.wall_url,
            "--post-id",
            post_id,
            "--site-url",
            args.site_url,
            "--tags",
            args.tags,
        ],
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr or proc.stdout)

    print(json.dumps({"status": "ok", "location": args.location, "wall_url": args.wall_url}, ensure_ascii=False))


if __name__ == "__main__":
    main()
