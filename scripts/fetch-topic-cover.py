#!/usr/bin/env python3
"""Download cover.png for topics (not in git) from vk-mcp-handoff cover_public_url."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY


def _cover_url(topic_dir: Path) -> str | None:
    handoff = topic_dir / "vk-mcp-handoff.json"
    if not handoff.is_file():
        return None
    try:
        data = json.loads(handoff.read_text(encoding="utf-8"))
        return data.get("cover_public_url") or data.get("photo_url")
    except (json.JSONDecodeError, OSError):
        return None


def fetch_cover(topic: str) -> dict:
    topic_dir = MEMORY / "output" / topic
    cover = topic_dir / "cover.png"
    if cover.is_file():
        return {"topic": topic, "status": "exists", "path": str(cover)}
    url = _cover_url(topic_dir)
    if not url:
        return {"topic": topic, "status": "no_url", "error": "vk-mcp-handoff.json missing cover_public_url"}
    topic_dir.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "PostsEMDR-cover-fetch/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        cover.write_bytes(resp.read())
    return {"topic": topic, "status": "downloaded", "path": str(cover), "url": url}


def pending_topics() -> list[str]:
    out: list[str] = []
    output = MEMORY / "output"
    if not output.is_dir():
        return out
    for d in sorted(output.iterdir()):
        if d.is_dir() and (d / "browser-local-handoff.md").is_file():
            out.append(d.name)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic")
    parser.add_argument("--all-pending", action="store_true")
    args = parser.parse_args()

    topics = [args.topic] if args.topic else (pending_topics() if args.all_pending else [])
    if not topics:
        print(json.dumps({"status": "nothing_to_do"}, ensure_ascii=False, indent=2))
        return

    results = [fetch_cover(t) for t in topics]
    print(json.dumps({"results": results}, ensure_ascii=False, indent=2))
    failed = [r for r in results if r["status"] not in {"exists", "downloaded"}]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
