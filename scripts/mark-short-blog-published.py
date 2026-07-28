#!/usr/bin/env python3
"""Перенести topic_id из short-blog-queue.md → short-blog-published.md."""

from __future__ import annotations

import argparse
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TOPICS = ROOT / "posts-emdr-memory" / "topics"
QUEUE = TOPICS / "short-blog-queue.md"
PUBLISHED = TOPICS / "short-blog-published.md"


def _parse_queue_row(line: str) -> dict | None:
    m = re.match(
        r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*(.+?)\s*\|\s*$",
        line.strip(),
    )
    if not m:
        return None
    return {
        "topic_id": m.group(1),
        "msp": m.group(2),
        "format": m.group(3).strip(),
        "site": m.group(4).strip(),
        "title": m.group(5).strip(),
    }


def _site_url(site_cell: str) -> str:
    site = site_cell.strip()
    if site.startswith("http"):
        return site
    if not site.startswith("/"):
        site = f"/{site}"
    return f"https://morozovanatalia.ru{site}"


def mark_published(topic_id: str, *, pub_date: str | None = None) -> dict:
    if not QUEUE.is_file():
        raise SystemExit(f"Missing {QUEUE}")
    lines = QUEUE.read_text(encoding="utf-8").splitlines()
    row_data = None
    new_lines: list[str] = []
    for line in lines:
        if line.strip().startswith(f"| `{topic_id}`"):
            row_data = _parse_queue_row(line)
            if not row_data:
                raise SystemExit(f"Cannot parse queue row for {topic_id}")
            continue
        new_lines.append(line)
    if not row_data:
        raise SystemExit(f"topic_id not in queue: {topic_id}")

    d = pub_date or date.today().isoformat()
    site_url = _site_url(row_data["site"])
    pub_row = (
        f"| `{topic_id}` | {row_data['msp']} | {d} | {row_data['title']} | {site_url} |"
    )

    pub_lines = PUBLISHED.read_text(encoding="utf-8").splitlines()
    insert_at = None
    for i, line in enumerate(pub_lines):
        if line.strip().startswith("|----------|") and i > 0 and "topic_id" in pub_lines[i - 1]:
            insert_at = i + 1
            break
    if insert_at is None:
        raise SystemExit(f"Cannot find insert point in {PUBLISHED}")
    pub_lines.insert(insert_at, pub_row)
    PUBLISHED.write_text("\n".join(pub_lines) + "\n", encoding="utf-8")
    QUEUE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    return {"topic_id": topic_id, "date": d, "site_url": site_url, "title": row_data["title"]}


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--topic-id", required=True)
    p.add_argument("--date", default=date.today().isoformat())
    args = p.parse_args()
    result = mark_published(args.topic_id, pub_date=args.date)
    print(f"OK marked published: {result['topic_id']} → {PUBLISHED.name}")


if __name__ == "__main__":
    main()
