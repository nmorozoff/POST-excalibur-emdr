#!/usr/bin/env python3
"""Regenerate ok-mcp-handoff.json from ok-post.md with current format_ok_publish_text.

Usage:
  python3 scripts/regenerate-ok-handoff.py --topic sb-16-dog-present-moment
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, format_ok_publish_text, markdown_to_ok_text_tokens, ok_group_gid

SCRIPTS = Path(__file__).resolve().parent


def regenerate(topic: str) -> Path:
    topic_dir = MEMORY / "output" / topic
    ok_md = topic_dir / "ok-post.md"
    if not ok_md.is_file():
        raise SystemExit(f"Missing {ok_md}")

    old = {}
    handoff_path = topic_dir / "ok-mcp-handoff.json"
    if handoff_path.is_file():
        old = json.loads(handoff_path.read_text(encoding="utf-8"))

    image_url = old.get("image_url") or f"https://morozovanatalia.ru/social-covers/{topic}.jpg"

    raw_md = ok_md.read_text(encoding="utf-8")
    m = re.search(r"## Текст поста\n\n(.*?)(?:\n\n---\n\n## |\Z)", raw_md, re.S)
    if not m:
        raise SystemExit("Cannot parse ## Текст поста in ok-post.md")
    source_body = m.group(1).strip()
    publish_text = format_ok_publish_text(source_body)

    handoff = {
        "topic": topic,
        "method": "mcp-kv",
        "tool": "ok_create_post_with_photo",
        "image_url": image_url,
        "gid": old.get("gid") or ok_group_gid(),
        "onBehalfOfGroup": True,
        "text": publish_text,
        "text_tokens": markdown_to_ok_text_tokens(source_body),
        "text_tokens_note": old.get("text_tokens_note")
        or (
            "OK API MediaTextToken: якоря через text_tokens[].link. "
            "Текущий MCP ok_create_post_with_photo принимает только text — "
            "используй text (plain). text_tokens — для апгрейда MCP."
        ),
        "instructions": "posts-emdr-memory/profile/cloud-publish-phases.md",
        "record_after_publish": old.get("record_after_publish")
        or (
            f"python3 scripts/record-ok-publish.py --topic {topic} "
            "--url <post_url> --mediatopic-id <id> --title <title> --site-url <site> --tags <tags>"
        ),
    }
    handoff_path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return handoff_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    args = parser.parse_args()
    path = regenerate(args.topic)
    print(json.dumps({"status": "ok", "handoff": str(path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
