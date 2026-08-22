#!/usr/bin/env python3
"""Smoke-тест gate ссылки ЛС в постах Макс. Запуск: python3 scripts/test_max_ls_gate.py"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import (
    MEMORY,
    fix_max_markdown_links,
    get_max_ls_url,
    validate_max_ls_cta,
)

LS = get_max_ls_url()


def _assert(cond: bool, msg: str) -> None:
    if not cond:
        raise AssertionError(msg)


def test_correct_cta_passes() -> None:
    text = (
        f"Если хотите обсудить это лично, напишите мне "
        f"[в личных сообщениях]({LS})."
    )
    fixed = fix_max_markdown_links(text)
    _assert(not validate_max_ls_cta(fixed), f"unexpected: {validate_max_ls_cta(fixed)}")


def test_bot_url_blocked() -> None:
    bad = (
        "Если хотите обсудить это лично, напишите мне "
        "[в личных сообщениях](https://max.ru/id771605638595_bot)."
    )
    fixed = fix_max_markdown_links(bad)
    _assert(validate_max_ls_cta(fixed) == [], "fix should replace bot URL")
    issues = validate_max_ls_cta(bad)
    _assert(issues, "raw bot URL must fail gate")


def test_channel_post_blocked() -> None:
    bad = (
        "Если хотите обсудить это лично, напишите мне "
        "[в личных сообщениях](https://max.ru/se13417616_biz/AZ9H9rFePFc)."
    )
    fixed = fix_max_markdown_links(bad)
    _assert(validate_max_ls_cta(fixed) == [], "fix should replace channel post URL")
    _assert(validate_max_ls_cta(bad), "raw channel post must fail gate")


def test_published_max_posts() -> None:
    failures: list[str] = []
    for path in sorted(MEMORY.glob("output/*/max-post.md")):
        raw = path.read_text(encoding="utf-8")
        try:
            from posts_emdr_env import extract_post_body_from_md

            body = fix_max_markdown_links(extract_post_body_from_md(raw))
        except ValueError:
            continue
        issues = validate_max_ls_cta(body)
        if issues:
            failures.append(f"{path.parent.name}: {issues}")
    _assert(not failures, "\n".join(failures))


def main() -> None:
    test_correct_cta_passes()
    test_bot_url_blocked()
    test_channel_post_blocked()
    test_published_max_posts()
    print("test_max_ls_gate: OK")


if __name__ == "__main__":
    main()
