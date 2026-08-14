#!/usr/bin/env python3
"""VK stories after wall posts — handoff for MCP vk_publish_story.

Usage:
  # After vk_create_post_with_photo ×2 and vk-publish-log.json exist:
  python3 scripts/publish-vk-story.py --topic sb-16-dog-present-moment --prepare

  # Agent calls MCP vk_publish_story for each entry in calls[], then:
  python3 scripts/publish-vk-story.py --topic sb-16-dog-present-moment --record \\
    --profile-story-id ... --group-story-id ...

  python3 scripts/publish-vk-story.py --topic sb-16 --prepare --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, PROJECT_ROOT

SCRIPTS = Path(__file__).resolve().parent
DEFAULT_LINK_TEXT = "Читать пост"
VK_GROUP_ID = "224685309"


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def cover_public_url(topic: str, topic_dir: Path) -> str:
    vk_handoff = _read_json(topic_dir / "vk-mcp-handoff.json") or {}
    url = vk_handoff.get("cover_public_url")
    if url:
        return url
    site = f"https://morozovanatalia.ru/social-covers/{topic}.jpg"
    meta = _read_json(topic_dir / "vk-cover-public-url.json") or {}
    return meta.get("url") or site


def load_wall_urls(topic_dir: Path) -> tuple[str, str]:
    vk_log = _read_json(topic_dir / "vk-publish-log.json")
    if not vk_log:
        raise SystemExit(
            f"Missing vk-publish-log.json in {topic_dir} — publish VK wall posts first"
        )
    profile = (vk_log.get("profile") or {}).get("url")
    group = (vk_log.get("group") or {}).get("url")
    if not profile or not group:
        raise SystemExit("vk-publish-log.json must contain profile.url and group.url")
    return profile, group


def build_handoff(topic: str, *, photo_url: str, profile_url: str, group_url: str) -> dict:
    return {
        "topic": topic,
        "method": "mcp-kv",
        "tool": "vk_publish_story",
        "cover_public_url": photo_url,
        "link_text": DEFAULT_LINK_TEXT,
        "instructions": (
            "После публикации постов на стене вызвать MCP vk_publish_story "
            "для каждого элемента calls[]. Gate: успешный ответ MCP."
        ),
        "calls": [
            {
                "publish_location": "personal",
                "content_type": "photo",
                "photo_url": photo_url,
                "link_text": DEFAULT_LINK_TEXT,
                "link_url": profile_url,
            },
            {
                "publish_location": "group",
                "group_id": VK_GROUP_ID,
                "content_type": "photo",
                "photo_url": photo_url,
                "link_text": DEFAULT_LINK_TEXT,
                "link_url": group_url,
            },
        ],
        "record_after_publish": (
            f"python3 scripts/publish-vk-story.py --topic {topic} --record "
            "--profile-story-id <id> --group-story-id <id>"
        ),
    }


def cmd_prepare(topic: str, *, dry_run: bool) -> Path | None:
    topic_dir = MEMORY / "output" / topic
    if not topic_dir.is_dir():
        raise SystemExit(f"Missing output/{topic}")

    profile_url, group_url = load_wall_urls(topic_dir)
    photo_url = cover_public_url(topic, topic_dir)
    handoff = build_handoff(
        topic,
        photo_url=photo_url,
        profile_url=profile_url,
        group_url=group_url,
    )

    if dry_run:
        print(json.dumps(handoff, ensure_ascii=False, indent=2))
        return None

    path = topic_dir / "vk-story-mcp-handoff.json"
    path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "handoff": str(path), "calls": len(handoff["calls"])}, indent=2))
    return path


def cmd_record(
    topic: str,
    *,
    profile_story_id: str = "",
    group_story_id: str = "",
    profile_url: str = "",
    group_url: str = "",
    dry_run: bool,
) -> None:
    topic_dir = MEMORY / "output" / topic
    vk_log = _read_json(topic_dir / "vk-publish-log.json") or {}
    wall_profile = (vk_log.get("profile") or {}).get("url", profile_url)
    wall_group = (vk_log.get("group") or {}).get("url", group_url)

    log = {
        "topic": topic,
        "platform": "vk_story",
        "status": "published",
        "method": "mcp-kv",
        "tool": "vk_publish_story",
        "date": date.today().isoformat(),
        "cover_public_url": cover_public_url(topic, topic_dir),
        "link_text": DEFAULT_LINK_TEXT,
        "stories": {
            "personal": {
                "story_id": profile_story_id or None,
                "link_url": wall_profile,
            },
            "group": {
                "story_id": group_story_id or None,
                "group_id": VK_GROUP_ID,
                "link_url": wall_group,
            },
        },
    }

    if dry_run:
        print(json.dumps(log, ensure_ascii=False, indent=2))
        return

    path = topic_dir / "vk-story-publish-log.json"
    path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "log": str(path)}, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description="VK stories MCP handoff + log")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--prepare", action="store_true", help="Write vk-story-mcp-handoff.json")
    parser.add_argument("--record", action="store_true", help="Write vk-story-publish-log.json")
    parser.add_argument("--profile-story-id", default="")
    parser.add_argument("--group-story-id", default="")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.record:
        cmd_record(
            args.topic,
            profile_story_id=args.profile_story_id,
            group_story_id=args.group_story_id,
            dry_run=args.dry_run,
        )
        return

    # default: prepare
    cmd_prepare(args.topic, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
