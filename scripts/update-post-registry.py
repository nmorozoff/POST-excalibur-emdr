#!/usr/bin/env python3
"""Добавить строку в реестр постов одной платформы (после публикации).

Примеры:
  python scripts/update-post-registry.py --platform max \\
    --topic-id 02-airplane-panic --title "..." --url "https://max.ru/..." \\
    --site-url "https://morozovanatalia.ru/phobias" --tags "паника,авиафобия"

  python scripts/update-post-registry.py --platform vk-group \\
    --topic-id 02-airplane-panic --title "..." --url "https://vk.com/wall-224685309_145" \\
    --post-id 145 --site-url "https://morozovanatalia.ru/phobias" --tags "..."
"""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE = ROOT / "posts-emdr-memory" / "profile"

REGISTRY_FILES = {
    "max": PROFILE / "max-posts-registry.md",
    "telegram": PROFILE / "telegram-posts-registry.md",
    "vk-profile": PROFILE / "vk-profile-posts-registry.md",
    "vk-group": PROFILE / "vk-group-posts-registry.md",
    "facebook": PROFILE / "facebook-posts-registry.md",
    "b17": PROFILE / "b17-posts-registry.md",
    "tenchat": PROFILE / "tenchat-posts-registry.md",
}


def _append_under_published(path: Path, row: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    insert_at = None
    for i, line in enumerate(lines):
        if line.strip() == "## Опубликованные" and i + 2 < len(lines):
            insert_at = i + 2  # after table header + separator
            break
    if insert_at is None:
        raise SystemExit(f"Не найдена секция ## Опубликованные в {path}")
    lines.insert(insert_at, row)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _build_row(args: argparse.Namespace) -> str:
    d = args.date
    tags = args.tags.replace("|", "/")
    if args.platform == "max":
        return f"| {args.topic_id} | {d} | {args.title} | {args.url} | {args.site_url} | {tags} |"
    if args.platform == "telegram":
        channel = args.channel or "@morozova_emdr"
        msg_id = args.message_id or "?"
        return (
            f"| {args.topic_id} | {d} | {args.title} | {channel} | {msg_id} | {args.url} | "
            f"{args.site_url} | {tags} |"
        )
    if args.platform in ("vk-profile", "vk-group"):
        post_id = args.post_id or "?"
        return (
            f"| {args.topic_id} | {d} | {args.title} | {post_id} | {args.url} | "
            f"{args.site_url} | {tags} |"
        )
    if args.platform == "facebook":
        platform_post_id = args.platform_post_id or "?"
        return (
            f"| {args.topic_id} | {d} | {args.title} | {platform_post_id} | {args.url} | "
            f"{args.site_url} | {tags} |"
        )
    if args.platform == "b17":
        return f"| {args.topic_id} | {d} | {args.title} | {args.url} | {args.site_url} | {tags} |"
    if args.platform == "tenchat":
        return f"| {args.topic_id} | {d} | {args.title} | {args.url} | {args.site_url} | {tags} |"
    raise SystemExit(f"Неизвестная платформа: {args.platform}")


def main() -> None:
    p = argparse.ArgumentParser(description="Обновить реестр постов одной платформы")
    p.add_argument("--platform", required=True, choices=sorted(REGISTRY_FILES))
    p.add_argument("--topic-id", required=True)
    p.add_argument("--title", required=True)
    p.add_argument("--url", required=True)
    p.add_argument("--site-url", required=True)
    p.add_argument("--tags", default="")
    p.add_argument("--date", default=date.today().isoformat())
    p.add_argument("--post-id", help="VK post_id")
    p.add_argument("--message-id", help="Telegram message_id")
    p.add_argument("--channel", help="Telegram @channel")
    p.add_argument("--platform-post-id", help="Facebook post id")
    args = p.parse_args()

    path = REGISTRY_FILES[args.platform]
    if not path.exists():
        raise SystemExit(f"Нет файла: {path}")

    row = _build_row(args)
    _append_under_published(path, row)
    print(f"OK {path.name}: {args.topic_id} → {args.url}")


if __name__ == "__main__":
    main()
