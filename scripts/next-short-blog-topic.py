#!/usr/bin/env python3
"""Вернуть следующую тему MSP short-blog из очереди (первая pending строка).

Cloud/VPS intake MUST использовать этот скрипт, а не topic_id из handoff.

Usage:
  python3 scripts/next-short-blog-topic.py
  python3 scripts/next-short-blog-topic.py --json
  python3 scripts/next-short-blog-topic.py --sync  # убрать из очереди уже опубликованные
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, PROJECT_ROOT

QUEUE = MEMORY / "topics" / "short-blog-queue.md"
QUEUE_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*(.+?)\s*\|\s*$"
)
SCRIPTS = PROJECT_ROOT / "scripts"


def parse_queue_rows() -> list[dict[str, str]]:
    if not QUEUE.is_file():
        return []
    rows: list[dict[str, str]] = []
    for line in QUEUE.read_text(encoding="utf-8").splitlines():
        m = QUEUE_ROW_RE.match(line.strip())
        if not m:
            continue
        site_path = m.group(4).strip()
        if site_path.startswith("http"):
            site_url = site_path
        else:
            site_url = f"https://morozovanatalia.ru{site_path if site_path.startswith('/') else '/' + site_path}"
        rows.append(
            {
                "topic_id": m.group(1),
                "post_number": m.group(2),
                "format": m.group(3).strip(),
                "site_path": site_path,
                "site_url": site_url,
                "title": m.group(5).strip(),
            }
        )
    return rows


def is_published(topic_id: str) -> bool:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "is-topic-published.py"), "--topic", topic_id, "--json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if proc.returncode == 0:
        return True
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return False
    return bool(data.get("published"))


def sync_published_from_queue() -> list[str]:
    """mark-short-blog-published для строк очереди, которые уже end-to-end опубликованы."""
    moved: list[str] = []
    for row in parse_queue_rows():
        tid = row["topic_id"]
        if not is_published(tid):
            continue
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "mark-short-blog-published.py"), "--topic-id", tid],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            moved.append(tid)
    return moved


def resolve_next(*, sync: bool = False) -> dict:
    if sync:
        synced = sync_published_from_queue()
    else:
        synced = []
    rows = parse_queue_rows()
    if not rows:
        return {
            "topic_id": None,
            "reason": "queue_empty",
            "synced": synced,
        }
    first = rows[0]
    if is_published(first["topic_id"]):
        return {
            "topic_id": first["topic_id"],
            "reason": "already_published_still_in_queue",
            "synced": synced,
            **first,
        }
    return {"reason": "next_pending", "synced": synced, **first}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true")
    p.add_argument(
        "--sync",
        action="store_true",
        help="Перенести уже опубликованные темы из очереди в published",
    )
    args = p.parse_args()
    result = resolve_next(sync=args.sync)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        tid = result.get("topic_id")
        if not tid:
            print("QUEUE_EMPTY")
        else:
            print(tid)
    if not result.get("topic_id"):
        sys.exit(1)
    if result.get("reason") == "already_published_still_in_queue":
        sys.exit(2)
    sys.exit(0)


if __name__ == "__main__":
    main()
