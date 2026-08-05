#!/usr/bin/env python3
"""One-off edit b17 post cover (experimental). Uses Playwright backend.

Usage:
  python scripts/edit-b17-post.py --topic sb-07-five-minute-pause --post-id 665989
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, PROJECT_ROOT, normalize_typography, wordpress_media_upload
from browser_backend import publish_b17
from undetectable_browser import load_env_file, apply_undetectable_env, strip_urls_from_text

ENV_FILE = PROJECT_ROOT / "posts-emdr-memory" / "b17.env.local"


def extract_title_and_body(md_path: Path) -> tuple[str, str]:
    text = md_path.read_text(encoding="utf-8")
    title_m = re.search(r"^## Заголовок\s*\n\n(.+?)\n", text, re.M)
    body_m = re.search(r"## Текст поста\n\n(.*?)(?=\n---\n|\n## Мета|\Z)", text, re.S)
    if not title_m or not body_m:
        raise SystemExit(f"Cannot parse {md_path}")
    return title_m.group(1).strip(), body_m.group(1).strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--post-id", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    topic_dir = MEMORY / "output" / args.topic
    md_path = topic_dir / "b17-blog-post.md"
    cover = topic_dir / "cover.png"
    title, body = extract_title_and_body(md_path)
    body = strip_urls_from_text(body)
    body = normalize_typography(body)
    body = re.sub(
        r"Если тема откликается[^\n]*",
        "Если тема откликается — напишите в личные сообщения здесь на b17.",
        body,
    )

    if cover.exists():
        wp_cover = wordpress_media_upload(cover, args.topic)
        if wp_cover.get("error"):
            print("WordPress upload warning:", wp_cover["error"], file=sys.stderr)

    env = load_env_file(ENV_FILE)
    apply_undetectable_env(env)
    compose_url = f"https://www.b17.ru/my_blog.php?mod=edit&id={args.post_id}"

    print(f"Edit URL: {compose_url}")
    if args.dry_run:
        return

    result = publish_b17(
        env=env,
        compose_url=compose_url,
        title=title,
        body=body,
        cover_path=cover if cover.exists() else None,
        auto_submit=True,
        edit_mode=True,
    )
    print(result)


if __name__ == "__main__":
    main()
