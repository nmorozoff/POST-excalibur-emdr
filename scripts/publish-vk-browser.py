#!/usr/bin/env python3
"""VK wall — Undetectable Browser (Profile1), без MCP (нет flood control).

Usage:
  python3 scripts/publish-vk-browser.py --topic sb-26 --location personal --submit
  python3 scripts/publish-vk-browser.py --topic sb-26 --location group --from-group --submit
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_backend import browser_health
from posts_emdr_env import MEMORY, extract_post_body_from_md, format_vk_publish_text
from publish_idempotency import vk_location_published
from undetectable_browser import (
    VK_FEED_URL,
    VK_GROUP_CLUB_URL,
    apply_undetectable_env,
    fill_vk_wall_post,
    load_env_file,
)

SCRIPTS = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS.parent
BROWSER_ENV = PROJECT_ROOT / "posts-emdr-memory" / "b17.env.local"
BROWSER_ENV_EXAMPLE = PROJECT_ROOT / "posts-emdr-memory" / "b17.env.example"


def _extract_post(md_path: Path) -> str:
    return format_vk_publish_text(extract_post_body_from_md(md_path.read_text(encoding="utf-8")))


def main() -> None:
    parser = argparse.ArgumentParser(description="VK publish via Undetectable browser")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--location", choices=("personal", "group"), default="personal")
    parser.add_argument("--from-group", action="store_true")
    parser.add_argument("--submit", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--wall-url", default="", help="После ручной публикации — записать URL")
    args = parser.parse_args()

    if not args.force and vk_location_published(args.topic, args.location):
        print(
            json.dumps(
                {"status": "skipped", "reason": "vk_already_published", "location": args.location},
                ensure_ascii=False,
            )
        )
        return

    topic_dir = MEMORY / "output" / args.topic
    md = topic_dir / ("vk-group-post.md" if args.location == "group" else "vk-profile-post.md")
    if not md.is_file():
        raise SystemExit(f"Missing {md}")
    cover = topic_dir / "cover.png"
    if not cover.is_file():
        raise SystemExit(f"Missing {cover}")

    message = _extract_post(md)
    env = load_env_file(BROWSER_ENV if BROWSER_ENV.is_file() else BROWSER_ENV_EXAMPLE)
    apply_undetectable_env(env)
    profile_id = env.get("UNDETECTABLE_PROFILE_ID", "").strip()
    if not profile_id:
        raise SystemExit(f"Set UNDETECTABLE_PROFILE_ID in {BROWSER_ENV}")

    health = browser_health()
    if not health.get("ok"):
        raise SystemExit(f"Undetectable not ready: {health}")

    compose_url = VK_GROUP_CLUB_URL if args.location == "group" else VK_FEED_URL
    result = fill_vk_wall_post(
        base_url=env.get("UNDETECTABLE_BASE_URL", "http://127.0.0.1:25325"),
        profile_id=profile_id,
        compose_url=compose_url,
        message=message,
        cover_path=cover,
        auto_submit=args.submit,
    )
    result["topic"] = args.topic
    result["location"] = args.location
    result["from_group"] = args.from_group or args.location == "group"
    result["via"] = "undetectable-browser"

    if args.wall_url:
        result["wall_url"] = args.wall_url
        result["status"] = "published"
        subprocess.run(
            [
                sys.executable,
                str(SCRIPTS / "record-vk-mcp-publish.py"),
                "--topic",
                args.topic,
                "--location",
                args.location,
                *(
                    ["--from-group"]
                    if args.location == "group"
                    else []
                ),
                "--wall-url",
                args.wall_url,
                "--title",
                args.topic,
                "--site-url",
                "https://morozovanatalia.ru/anxiety",
                "--tags",
                "",
            ],
            cwd=PROJECT_ROOT,
            check=True,
        )

    log_path = topic_dir / "vk-publish-log.json"
    rows: list[dict] = []
    if log_path.is_file():
        try:
            raw = json.loads(log_path.read_text(encoding="utf-8"))
            rows = raw if isinstance(raw, list) else [raw]
        except json.JSONDecodeError:
            rows = []
    rows = [r for r in rows if r.get("location") != args.location]
    rows.append({**result, "date": date.today().isoformat(), "message_chars": len(message)})
    log_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
