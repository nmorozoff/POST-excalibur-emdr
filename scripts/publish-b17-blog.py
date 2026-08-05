#!/usr/bin/env python3
"""Заполнить заметку b17.ru в Undetectable Browser (Profile1).

Usage:
  python scripts/publish-b17-blog.py --topic sb-01-background-anxiety
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_backend import default_b17_compose_url, publish_b17
from posts_emdr_env import browser_backend_name, normalize_typography, wordpress_media_upload
from undetectable_browser import apply_undetectable_env, load_env_file, strip_urls_from_text

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / "posts-emdr-memory" / "b17.env.local"
ENV_EXAMPLE = PROJECT_ROOT / "posts-emdr-memory" / "b17.env.example"


def extract_title_and_body(md_path: Path) -> tuple[str, str]:
    text = md_path.read_text(encoding="utf-8")
    title_m = re.search(r"^## Заголовок\s*\n\n(.+?)\n", text, re.M)
    body_m = re.search(r"## Текст поста\n\n(.*?)(?=\n---\n|\n## Мета|\Z)", text, re.S)
    if not title_m or not body_m:
        raise SystemExit(f"Cannot parse title/body from {md_path} (need ## Заголовок and ## Текст поста)")
    return title_m.group(1).strip(), body_m.group(1).strip()


def main() -> None:
    parser = argparse.ArgumentParser(description="b17.ru — заполнить форму заметки")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--dry-run", action="store_true", help="Только prep JSON, без браузера")
    parser.add_argument(
        "--submit",
        action="store_true",
        help="После заполнения нажать «Сохранить» (требует открытый Undetectable)",
    )
    args = parser.parse_args()

    topic_dir = PROJECT_ROOT / "posts-emdr-memory" / "output" / args.topic
    md_path = topic_dir / "b17-blog-post.md"
    if not md_path.exists():
        raise SystemExit(f"Missing {md_path}")

    title, body = extract_title_and_body(md_path)
    body = strip_urls_from_text(body)
    body = normalize_typography(body)
    # b17: без URL в тексте; мягкий контакт только через ЛС на площадке
    body = re.sub(
        r"Если тема откликается[^\n]*",
        "Если тема откликается — напишите в личные сообщения здесь на b17.",
        body,
    )
    cover = topic_dir / "cover.png"

    wp_cover = None
    if cover.exists():
        wp_cover = wordpress_media_upload(cover, args.topic)
        if wp_cover.get("error"):
            print("WordPress upload warning:", wp_cover["error"], file=sys.stderr)

    prep = {
        "topic": args.topic,
        "platform": "b17-blog",
        "title": title,
        "body": body,
        "body_chars": len(body),
        "cover_local": str(cover) if cover.exists() else None,
        "cover_wordpress": wp_cover,
        "utm_source": "b17",
    }

    prep_path = topic_dir / "b17-publish-prep.json"
    prep_path.write_text(json.dumps(prep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.dry_run:
        print(json.dumps({**prep, "status": "prep_only", "prep_path": str(prep_path)}, ensure_ascii=False, indent=2))
        return

    env = load_env_file(ENV_FILE)
    apply_undetectable_env(env)
    if browser_backend_name() == "undetectable":
        profile_id = env.get("UNDETECTABLE_PROFILE_ID", "")
        if not profile_id:
            raise SystemExit(f"Set UNDETECTABLE_PROFILE_ID in {ENV_FILE} (see {ENV_EXAMPLE.name})")

    browser_result = publish_b17(
        env=env,
        compose_url=default_b17_compose_url(env),
        title=title,
        body=body,
        cover_path=cover if cover.exists() else None,
        auto_submit=args.submit,
    )

    log = {**prep, **browser_result}
    log_path = topic_dir / "b17-publish-log.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
