#!/usr/bin/env python3
"""Заполнить пост TenChat в Undetectable Browser (Profile1).

Usage:
  python scripts/publish-tenchat-post.py --topic sb-01-background-anxiety
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from undetectable_browser import TENCHAT_COMPOSE_URL_DEFAULT, fill_tenchat_compose, load_env_file

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / "posts-emdr-memory" / "tenchat.env.local"
ENV_EXAMPLE = PROJECT_ROOT / "posts-emdr-memory" / "tenchat.env.example"


def extract_title_and_paste_body(md_path: Path) -> tuple[str, str]:
    text = md_path.read_text(encoding="utf-8")

    header_m = re.search(r"^## Заголовок[^\n]*\n\n", text, re.M)
    if not header_m:
        raise SystemExit(f"Cannot parse {md_path}: missing ## Заголовок section")

    after_header = text[header_m.end() :]
    title = ""
    for line in after_header.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("*(") or stripped.startswith("("):
            continue
        if stripped.startswith("---"):
            break
        if stripped.startswith("## "):
            break
        title = stripped.strip("*").strip()
        break

    paste_m = re.search(
        r"## Текст для вставки[^\n]*\n\n(.*?)(?=\n---\n\n## |\Z)",
        text,
        re.S,
    )
    if not title or not paste_m:
        raise SystemExit(
            f"Cannot parse {md_path} (need ## Заголовок and ## Текст для вставки)"
        )
    return title, paste_m.group(1).strip()


def parse_topics(env: dict[str, str], md_path: Path) -> list[str]:
    if env.get("TENCHAT_TOPICS"):
        return [t.strip() for t in env["TENCHAT_TOPICS"].split(",") if t.strip()]
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"\*\*Темы при публикации:\*\*\s*(.+)", text)
    if m:
        return [t.strip() for t in re.split(r"[·,]", m.group(1)) if t.strip()]
    return ["Саморазвитие"]


def main() -> None:
    parser = argparse.ArgumentParser(description="TenChat — заполнить редактор")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--dry-run", action="store_true", help="Только prep JSON, без браузера")
    parser.add_argument(
        "--submit",
        action="store_true",
        help="После заполнения нажать «Опубликовать» (требует открытый Undetectable)",
    )
    args = parser.parse_args()

    topic_dir = PROJECT_ROOT / "posts-emdr-memory" / "output" / args.topic
    md_path = topic_dir / "tenchat-post.md"
    if not md_path.exists():
        raise SystemExit(f"Missing {md_path}")

    title, body = extract_title_and_paste_body(md_path)
    cover = topic_dir / "cover.png"
    env = load_env_file(ENV_FILE)
    topics = parse_topics(env, md_path)

    prep = {
        "topic": args.topic,
        "platform": "tenchat",
        "title": title,
        "title_chars": len(title),
        "body": body,
        "body_chars": len(body),
        "cover_local": str(cover) if cover.exists() else None,
        "utm_source": "tenchat",
        "topics": topics,
    }

    prep_path = topic_dir / "tenchat-publish-prep.json"
    prep_path.write_text(json.dumps(prep, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.dry_run:
        print(json.dumps({**prep, "status": "prep_only", "prep_path": str(prep_path)}, ensure_ascii=False, indent=2))
        return

    profile_id = env.get("UNDETECTABLE_PROFILE_ID", "")
    if not profile_id:
        raise SystemExit(f"Set UNDETECTABLE_PROFILE_ID in {ENV_FILE} (see {ENV_EXAMPLE.name})")

    browser_result = fill_tenchat_compose(
        base_url=env.get("UNDETECTABLE_BASE_URL", "http://127.0.0.1:25325"),
        profile_id=profile_id,
        compose_url=env.get("TENCHAT_COMPOSE_URL", TENCHAT_COMPOSE_URL_DEFAULT),
        title=title,
        body=body,
        topics=topics,
        use_code_block=env.get("TENCHAT_USE_CODE_BLOCK", "1") not in {"0", "false", "no"},
        cover_path=cover if cover.exists() else None,
        auto_submit=args.submit,
    )

    log = {**prep, **browser_result}
    log_path = topic_dir / "tenchat-publish-log.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
