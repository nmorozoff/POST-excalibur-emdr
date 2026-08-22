#!/usr/bin/env python3
"""Generate MSP short-blog texts via Grsai Chat API (gemini-3.1-pro).

Usage:
  python3 scripts/grsai-generate-topic.py --topic sb-10-phrase-when-anxiety
  python3 scripts/grsai-generate-topic.py --topic sb-10-phrase-when-anxiety --platform max
  python3 scripts/grsai-generate-topic.py --topic sb-10-phrase-when-anxiety --dry-run

Key: posts-emdr-memory/grsai.env.local (GRSAI_API_KEY — тот же, что для обложек).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grsai_chat import DEFAULT_TIMEOUT_SEC, chat_completion
from posts_emdr_env import (
    MEMORY,
    ensure_client_story_disclaimer,
    load_env,
    post_number_from_topic,
    remove_znakomo,
    strip_cover_meta_block,
    fix_disclaimer_typo,
)

PROFILE = MEMORY / "profile"
SCRIPTS = Path(__file__).resolve().parent

QUEUE_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*(.+?)\s*\|\s*$"
)

PLATFORM_SPECS: dict[str, dict[str, str]] = {
    "max": {
        "output": "max-post.md",
        "prompt": "max-post-prompt.md",
        "registry": "max-posts-registry.md",
        "kind": "source",
    },
    "telegram": {
        "output": "telegram-post.md",
        "prompt": "telegram-post-prompt.md",
        "registry": "telegram-posts-registry.md",
        "kind": "rewrite",
    },
    "vk-profile": {
        "output": "vk-profile-post.md",
        "prompt": "vk-post-prompt.md",
        "registry": "vk-profile-posts-registry.md",
        "kind": "rewrite",
        "note": "Режим VK профиль: utm_source=vk, перелинковка только vk-profile-posts-registry.md. "
        "В ## Текст поста не оставляй видимые ** вокруг заголовка — VK wall не рендерит markdown "
        "(пайплайн format_vk_publish_text снимет **, но лучше сразу plain).",
    },
    "vk-group": {
        "output": "vk-group-post.md",
        "prompt": "vk-post-prompt.md",
        "registry": "vk-group-posts-registry.md",
        "kind": "rewrite",
        "note": "Режим VK группа: utm_source=vk_group, перелинковка только vk-group-posts-registry.md. "
        "Заголовок без **markdown** — VK показывает звёздочки как текст.",
    },
    "facebook": {
        "output": "facebook-post.md",
        "prompt": "facebook-post-prompt.md",
        "registry": "facebook-posts-registry.md",
        "kind": "rewrite",
    },
    "ok": {
        "output": "ok-post.md",
        "prompt": "ok-post-prompt.md",
        "registry": "ok-posts-registry.md",
        "kind": "rewrite",
    },
    "b17": {
        "output": "b17-blog-post.md",
        "prompt": "b17-blog-post-prompt.md",
        "registry": "b17-posts-registry.md",
        "kind": "rewrite",
    },
}

GENERATION_ORDER = [
    "max",
    "telegram",
    "vk-profile",
    "vk-group",
    "facebook",
    "ok",
    "b17",
]

SYSTEM_PROMPT = """Ты — профессиональный русскоязычный копирайтер для психолога Натальи Морозовой (EMDR).
Строго следуй контракту платформы. Пиши живо, без эзотерики, без слова «Знакомо».
Не используй длинное тире «—» (заменяй на запятую).
Выводи ТОЛЬКО содержимое целевого markdown-файла, без пояснений до или после."""


def read_text(path: Path, *, max_chars: int = 14000) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[... обрезано для лимита контекста ...]"
    return text


def load_topic_brief(topic_id: str) -> dict[str, str]:
    for rel in ("topics/short-blog-queue.md", "topics/short-blog-published.md"):
        path = MEMORY / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if f"`{topic_id}`" not in line:
                continue
            m = QUEUE_ROW_RE.match(line.strip())
            if not m:
                continue
            site_path = m.group(4).strip()
            if site_path.startswith("http"):
                site_url = site_path
            else:
                site_url = f"https://morozovanatalia.ru{site_path if site_path.startswith('/') else '/' + site_path}"
            return {
                "topic_id": m.group(1),
                "post_number": m.group(2),
                "format": m.group(3).strip(),
                "site_path": site_path,
                "site_url": site_url,
                "title": m.group(5).strip(),
            }
    raise SystemExit(f"topic_id not found in queue/published: {topic_id}")


def registry_excerpt(registry_name: str, *, max_rows: int = 10) -> str:
    path = PROFILE / registry_name
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[str] = []
    in_published = False
    for line in lines:
        if line.strip() == "## Опубликованные":
            in_published = True
            continue
        if in_published and line.startswith("## "):
            break
        if in_published and line.startswith("|") and "topic_id" not in line and "---" not in line:
            rows.append(line)
    return "\n".join(rows[:max_rows])


def cta_context(post_number: int) -> str:
    soft_slot = post_number % 3
    full_session = post_number % 4 == 0
    return (
        f"Номер поста MSP: {post_number}\n"
        f"Мягкий контакт (short-blog-cta-rules): слот {soft_slot} (sb-NN % 3)\n"
        f"Полный CTA пробной сессии: {'да (#NN % 4 == 0)' if full_session else 'нет'}\n"
        "ЛС Макс: https://max.ru/u/f9LHodD0cOLMWn4dwsfNLXttuTDjJTF4cCK2MJPjCfNpeKrbfQ6RlQy3dLk\n"
        "ЛС TG/VK/FB/OK: https://t.me/natalyamorozovaa\n"
    )


def shared_context() -> str:
    parts = [
        read_text(PROFILE / "tone-of-voice.md", max_chars=8000),
        read_text(PROFILE / "author-profile.md", max_chars=6000),
        read_text(PROFILE / "emdr-evidence.md", max_chars=6000),
        read_text(PROFILE / "crosslink-rules.md", max_chars=5000),
        read_text(PROFILE / "short-blog-cta-rules.md", max_chars=5000),
        read_text(PROFILE / "client-story-disclaimer.md", max_chars=2000),
        read_text(MEMORY / "shared/agent-pipeline-pitfalls.md", max_chars=4000),
    ]
    return "\n\n---\n\n".join(p for p in parts if p.strip())


def strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def postprocess_platform(platform: str, text: str) -> str:
    text = strip_code_fence(text)
    text = remove_znakomo(text)
    text = fix_disclaimer_typo(text)
    if platform == "telegram":
        if "## Текст поста" not in text:
            topic_line = ""
            if "**topic" not in text.lower() and not text.startswith("# Пост Telegram"):
                topic_line = "# Пост Telegram\n\n**Delivery:** `link_preview`\n\n---\n\n"
            text = (
                f"{topic_line}## Текст поста (HTML для Telegram)\n\n"
                f"{text.rstrip()}\n"
            )
        if "## Текст поста (HTML" not in text and "## Текст поста\n" in text:
            text = text.replace("## Текст поста\n", "## Текст поста (HTML для Telegram)\n", 1)
        if "<!-- END_POST -->" not in text:
            if "\n---\n" in text:
                head, tail = text.split("\n---\n", 1)
                if "## Мета" in tail or "## Meta" in tail:
                    text = head.rstrip() + "\n\n<!-- END_POST -->\n\n---\n" + tail
                else:
                    text = head.rstrip() + "\n\n<!-- END_POST -->"
            else:
                text = text.rstrip() + "\n\n<!-- END_POST -->"
    text = ensure_client_story_disclaimer(text, platform)
    if platform == "max":
        from posts_emdr_env import fix_max_markdown_links

        text = fix_max_markdown_links(text)
    return text


SECTION_TEXT_POSTA_RE = re.compile(r"^## Текст поста", re.M)
TELEGRAM_HTML_SECTION_RE = re.compile(r"^## Текст поста \(HTML", re.M)

MAX_BODY_MIN = 3000
MAX_BODY_TARGET_MIN = 3500
MAX_BODY_TARGET_MAX = 3800
MAX_BODY_HARD_MAX = 4000
TELEGRAM_HTML_HARD_MAX = 4096


def has_text_posta_section(text: str) -> bool:
    return bool(SECTION_TEXT_POSTA_RE.search(text))


def _has_cover_block(text: str) -> bool:
    return bool(re.search(r"Line 1:", text))


def _plain_body_from_raw(text: str) -> str:
    """Extract main body when Grsai omitted ## Текст поста."""
    text = text.strip()
    if "<!-- END_POST -->" in text:
        body, _, _ = text.partition("<!-- END_POST -->")
        return body.strip()
    if has_text_posta_section(text):
        m = re.search(
            r"## Текст поста[^\n]*\n\n(.*?)(?:\n\n---\n|\Z)",
            text,
            re.S,
        )
        if m:
            return m.group(1).strip()
    if "\n---\n" in text:
        parts = [part.strip() for part in text.split("\n---\n") if part.strip()]
        for part in reversed(parts):
            if part.startswith("#") or part.startswith("**") or part.startswith("## Мета"):
                continue
            if part.startswith("## ") and "Текст поста" not in part:
                continue
            return part
    lines = text.splitlines()
    start = 0
    if lines and lines[0].startswith("# "):
        start = 1
        while start < len(lines) and (
            not lines[start].strip() or lines[start].startswith("**") or lines[start].startswith("- ")
        ):
            start += 1
        if start < len(lines) and lines[start].strip() == "---":
            start += 1
    return "\n".join(lines[start:]).strip()


def _ensure_meta_footer(text: str, body: str) -> str:
    if re.search(r"^## Мета\s*$", text, re.M):
        return text
    return (
        text.rstrip()
        + "\n\n---\n\n## Мета\n\n"
        + "| Поле | Значение |\n|------|----------|\n"
        + f"| chars | ~{len(body)} |\n"
        + "| auto_wrap | grsai-generate-topic |\n"
    )


def wrap_max_post(text: str, brief: dict[str, str]) -> str:
    body = ""
    header_part = ""
    if has_text_posta_section(text):
        try:
            from posts_emdr_env import extract_post_body_from_md

            body = strip_cover_meta_block(extract_post_body_from_md(text))
        except ValueError:
            body = strip_cover_meta_block(_plain_body_from_raw(text))
        if _has_cover_block(text):
            pre = text.split("\n---\n", 1)[0].rstrip()
            if _has_cover_block(pre) and "Line 1:" in pre:
                header_part = pre
            else:
                header_part = ""
    else:
        body = strip_cover_meta_block(_plain_body_from_raw(text))

    title = brief["title"]
    topic_id = brief["topic_id"]
    post_num = brief["post_number"]
    site_url = brief["site_url"]

    if not header_part or not _has_cover_block(header_part):
        if _has_cover_block(text):
            line1 = re.search(r"Line 1:\s*(.+)", text)
            line2 = re.search(r"Line 2:\s*(.+)", text)
            line3 = re.search(r"Line 3:\s*(.+)", text)
            yellow = re.search(r"жёлтый:\s*(.+?)\)", text)
            l1 = line1.group(1).strip() if line1 else title.split()[0]
            l2_raw = line2.group(1).strip() if line2 else " ".join(title.split()[1:3])
            l2 = re.sub(r"\s*\*\(жёлтый:.*", "", l2_raw).strip()
            l3 = line3.group(1).strip() if line3 else ""
            yel = yellow.group(1).strip() if yellow else (l2.split()[-1] if l2 else l1)
            header_part = (
                f"# Пост Макс — {topic_id}\n\n"
                f"**Заголовок:** {title}\n"
                f"**Обложка:**\n"
                f"- Line 1: {l1}\n"
                f"- Line 2: {l2} *(жёлтый: {yel})*\n"
                f"- Line 3: {l3 or '...'}\n"
                f"**Сайт:** {site_url}\n"
                f"**Формат:** {brief.get('format', 'короткий пост MSP')} · #{post_num}"
            )
        else:
            words = title.split()
            line1 = words[0] if words else title[:24]
            line2 = " ".join(words[1:3]) if len(words) > 1 else title[:36]
            yellow = line2.split()[-1] if line2 else line1
            line3 = " ".join(words[3:6]) if len(words) > 3 else ""
            header_part = (
                f"# Пост Макс — {topic_id}\n\n"
                f"**Заголовок:** {title}\n"
                f"**Обложка:**\n"
                f"- Line 1: {line1}\n"
                f"- Line 2: {line2} *(жёлтый: {yellow})*\n"
                f"- Line 3: {line3 or '...'}\n"
                f"**Сайт:** {site_url}\n"
                f"**Формат:** {brief.get('format', 'короткий пост MSP')} · #{post_num}"
            )

    body = strip_cover_meta_block(body)
    result = f"{header_part}\n\n---\n\n## Текст поста\n\n{body.strip()}\n"
    return _ensure_meta_footer(result, body)


def wrap_rewrite_post(platform: str, text: str, brief: dict[str, str]) -> str:
    if has_text_posta_section(text):
        return text

    body = _plain_body_from_raw(text)
    title = brief["title"]
    topic_id = brief["topic_id"]

    if platform == "b17":
        result = f"## Заголовок\n\n{title}\n\n## Текст поста\n\n{body.strip()}\n"
        return _ensure_meta_footer(result, body)

    headers = {
        "vk-profile": (
            f"# Пост VK — профиль\n\n**Тема:** {topic_id}\n**UTM:** `utm_source=vk`"
        ),
        "vk-group": (
            f"# Пост VK — группа\n\n**Тема:** {topic_id}\n**UTM:** `utm_source=vk_group`"
        ),
        "facebook": (
            f"# Пост Facebook — {topic_id}\n\n"
            f"**Заголовок:** {title}\n"
            f"**Формат:** рерайт\n"
            f"**UTM:** `utm_source=fb`\n"
            f"**Обложка:** `cover.png`"
        ),
        "ok": (
            f"# Пост OK — {topic_id}\n\n"
            f"**Заголовок:** {title}\n"
            f"**UTM:** `utm_source=ok`"
        ),
    }
    header = headers.get(platform, f"# Пост — {topic_id}")
    result = f"{header}\n\n---\n\n## Текст поста\n\n{body.strip()}\n"
    return _ensure_meta_footer(result, body)


def wrap_telegram_post(text: str, brief: dict[str, str]) -> str:
    if TELEGRAM_HTML_SECTION_RE.search(text):
        return text

    body = _plain_body_from_raw(text)
    topic_id = brief["topic_id"]
    result = (
        f"# Пост Telegram — {topic_id}\n\n"
        f"**UTM:** `utm_source=tg1`\n"
        f"**Обложка:** `cover.png` (из шага Макс, не генерировать)\n"
        f"**Delivery:** `link_preview`\n\n"
        f"---\n\n"
        f"## Текст поста (HTML для Telegram)\n\n"
        f"{body.strip()}\n\n"
        f"<!-- END_POST -->\n"
    )
    return _ensure_meta_footer(result, body)


def extract_telegram_html_body(text: str) -> str:
    """Extract HTML body from telegram-post.md (same contract as send-telegram-post.py)."""
    m = re.search(
        r"## Текст поста \(HTML[^\n]*\n\n"
        r"(.*?)"
        r"(?=<!-- END_POST -->|\n---\s*\n## |\Z)",
        text,
        flags=re.S,
    )
    if not m:
        m = re.search(
            r"## Текст поста\n\n(.*?)(?=<!-- END_POST -->|\n---\s*\n## |\Z)",
            text,
            flags=re.S,
        )
    return m.group(1).strip() if m else ""


def truncate_telegram_html(text: str, *, hard_max: int = TELEGRAM_HTML_HARD_MAX) -> tuple[str, bool]:
    body = extract_telegram_html_body(text)
    if not body or len(body) <= hard_max:
        return text, False

    truncated = body[:hard_max]
    cut = truncated.rfind("\n\n")
    if cut >= int(hard_max * 0.85):
        truncated = truncated[:cut].rstrip()
    else:
        truncated = truncated.rstrip()

    # Preserve <!-- END_POST --> and meta tail — regex replacement drops the lookahead match.
    tail = ""
    if "<!-- END_POST -->" in text:
        _, _, after_end = text.partition("<!-- END_POST -->")
        tail = "\n\n<!-- END_POST -->" + after_end

    for pattern in (
        r"(## Текст поста \(HTML[^\n]*\n\n)(.*?)(?=\n\n<!-- END_POST -->|\n<!-- END_POST -->|\n---\s*\n## |\Z)",
        r"(## Текст поста\n\n)(.*?)(?=\n\n<!-- END_POST -->|\n<!-- END_POST -->|\n---\s*\n## |\Z)",
    ):
        new_text, count = re.subn(
            pattern,
            lambda m: m.group(1) + truncated + "\n" + tail,
            text,
            count=1,
            flags=re.S,
        )
        if count:
            if "<!-- END_POST -->" not in new_text:
                new_text = new_text.rstrip() + "\n\n<!-- END_POST -->"
            return new_text, True
    return text, False


def ensure_b17_blank_lines(text: str) -> tuple[str, bool]:
    """b17 parsers require a blank line after ## Заголовок / ## Текст поста."""
    fixed = False
    for header in ("## Заголовок", "## Текст поста"):
        new_text, count = re.subn(
            rf"^({re.escape(header)})\n(?!\n)",
            r"\1\n\n",
            text,
            count=1,
            flags=re.M,
        )
        if count:
            text = new_text
            fixed = True
    return text, fixed


def ensure_b17_meta_separator(text: str) -> tuple[str, bool]:
    """Ensure --- before ## Мета when Grsai omitted the separator."""
    if re.search(r"^## Мета\s*$", text, re.M) and not re.search(
        r"\n---\n\n## Мета\s*$", text, re.M
    ):
        new_text, count = re.subn(
            r"\n(## Мета\s*$)",
            r"\n\n---\n\n\1",
            text.rstrip(),
            count=1,
            flags=re.M,
        )
        if count:
            return new_text + "\n", True
    return text, False


def truncate_max_body(text: str, *, hard_max: int = MAX_BODY_HARD_MAX) -> tuple[str, bool]:
    if not has_text_posta_section(text):
        return text, False
    try:
        from posts_emdr_env import extract_post_body_from_md

        body = extract_post_body_from_md(text)
    except ValueError:
        return text, False
    if len(body) <= hard_max:
        return text, False

    truncated = body[:hard_max]
    cut = truncated.rfind("\n\n")
    if cut >= MAX_BODY_TARGET_MIN:
        truncated = truncated[:cut].rstrip()
    else:
        truncated = truncated.rstrip()

    new_text, count = re.subn(
        r"(## Текст поста\n\n)(.*?)(?=\n\n---\n|\Z)",
        lambda m: m.group(1) + truncated + "\n",
        text,
        count=1,
        flags=re.S,
    )
    return (new_text if count else text), bool(count)


def validate_platform_output(platform: str, text: str) -> list[str]:
    warnings: list[str] = []
    if platform == "telegram":
        if not TELEGRAM_HTML_SECTION_RE.search(text):
            warnings.append("missing telegram HTML section")
        if "<!-- END_POST -->" not in text:
            warnings.append("missing END_POST marker")
        html_body = extract_telegram_html_body(text)
        if html_body and len(html_body) > TELEGRAM_HTML_HARD_MAX:
            warnings.append(
                f"telegram HTML too long: {len(html_body)}>{TELEGRAM_HTML_HARD_MAX}"
            )
        return warnings

    if not has_text_posta_section(text):
        warnings.append("missing ## Текст поста")
        return warnings

    try:
        from posts_emdr_env import extract_post_body_from_md

        body = extract_post_body_from_md(text)
    except ValueError as exc:
        warnings.append(str(exc))
        return warnings

    if platform == "max":
        blen = len(body)
        if blen > MAX_BODY_HARD_MAX:
            warnings.append(f"max body too long: {blen}>{MAX_BODY_HARD_MAX}")
        elif blen < MAX_BODY_MIN:
            warnings.append(f"max body short: {blen}<{MAX_BODY_MIN}")
        elif not (MAX_BODY_TARGET_MIN <= blen <= MAX_BODY_TARGET_MAX):
            warnings.append(
                f"max body outside target {MAX_BODY_TARGET_MIN}-{MAX_BODY_TARGET_MAX}: {blen}"
            )
        if not _has_cover_block(text):
            warnings.append("missing cover Line 1/2/3 in max header")
        if _cover_leaked_into_body(text):
            warnings.append("cover meta leaked into ## Текст поста body")
        from posts_emdr_env import validate_max_ls_cta

        warnings.extend(validate_max_ls_cta(body))
    if platform == "b17":
        if not re.search(r"^## Заголовок\s*$", text, re.M):
            warnings.append("missing ## Заголовок for b17")
        elif not re.search(r"^## Заголовок\s*\n\n", text, re.M):
            warnings.append("b17 missing blank line after ## Заголовок")
        if has_text_posta_section(text) and not re.search(
            r"^## Текст поста\s*\n\n", text, re.M
        ):
            warnings.append("b17 missing blank line after ## Текст поста")
    return warnings


def ensure_platform_contract(platform: str, text: str, brief: dict[str, str]) -> tuple[str, list[str]]:
    fixes: list[str] = []
    if platform == "max":
        # Always normalize: cover only in header, never inside ## Текст поста
        needs_wrap = (
            not has_text_posta_section(text)
            or not _has_cover_block(text)
            or _cover_leaked_into_body(text)
        )
        if needs_wrap:
            text = wrap_max_post(text, brief)
            fixes.append("auto-wrapped max-post sections")
        text, truncated = truncate_max_body(text)
        if truncated:
            fixes.append("truncated max body to hard max 4000")
    elif platform == "telegram":
        if not TELEGRAM_HTML_SECTION_RE.search(text):
            text = wrap_telegram_post(text, brief)
            fixes.append("auto-wrapped telegram HTML section")
        text = _strip_cover_from_telegram(text)
        text, truncated = truncate_telegram_html(text)
        if truncated:
            fixes.append(f"truncated telegram HTML to hard max {TELEGRAM_HTML_HARD_MAX}")
    elif platform == "b17":
        if not has_text_posta_section(text) or not re.search(r"^## Заголовок\s*$", text, re.M):
            text = wrap_rewrite_post(platform, text, brief)
            fixes.append("auto-wrapped b17 sections")
        text, blank_fixed = ensure_b17_blank_lines(text)
        if blank_fixed:
            fixes.append("fixed b17 blank lines after headers")
        text, meta_fixed = ensure_b17_meta_separator(text)
        if meta_fixed:
            fixes.append("inserted --- before ## Мета for b17")
    else:
        # facebook / ok / vk-profile / vk-group (+ any other rewrite)
        if not has_text_posta_section(text):
            text = wrap_rewrite_post(platform, text, brief)
            fixes.append(f"auto-wrapped {platform} sections")
        if _cover_leaked_into_body(text):
            text = _strip_cover_from_body_section(text)
            fixes.append(f"stripped cover meta from {platform} body")

    remaining = validate_platform_output(platform, text)
    if remaining:
        fixes.extend(f"validation: {item}" for item in remaining)
        blocking = [item for item in remaining if item.startswith("missing")]
        if blocking:
            raise SystemExit(
                f"Grsai output contract failed for {platform} after auto-wrap: {blocking}"
            )
    return text, fixes


def _cover_leaked_into_body(text: str) -> bool:
    if not has_text_posta_section(text):
        return False
    try:
        from posts_emdr_env import extract_post_body_from_md

        # Extract without sanitize would be better — check raw body for Line 1
        m = re.search(
            r"## Текст поста[^\n]*\n\n(.*?)(?:\n\n---\n\n## |\Z)",
            text,
            re.S,
        )
        if not m:
            return False
        return bool(re.search(r"Line 1:", m.group(1))) or "OUTFIT:" in m.group(1)
    except Exception:
        return "Line 1:" in text and has_text_posta_section(text)


def _strip_cover_from_body_section(text: str) -> str:
    from posts_emdr_env import strip_cover_meta_block

    m = re.search(r"(## Текст поста[^\n]*\n\n)(.*?)(\n\n---\n|\Z)", text, re.S)
    if not m:
        return strip_cover_meta_block(text)
    body = strip_cover_meta_block(m.group(2))
    return text[: m.start(2)] + body + text[m.end(2) :]


def _strip_cover_from_telegram(text: str) -> str:
    from posts_emdr_env import strip_cover_meta_block

    # Cover must not sit above HTML section either in published extract paths
    if not TELEGRAM_HTML_SECTION_RE.search(text):
        return text
    head, sep, rest = text.partition("## Текст поста (HTML")
    if not sep:
        return text
    head = strip_cover_meta_block(head) if "Line 1:" in head else head
    # Also strip from HTML body
    m = re.search(
        r"(## Текст поста \(HTML[^\n]*\n\n)(.*?)((?:<!-- END_POST -->|\n---\s*\n## ).*)",
        sep + rest,
        re.S,
    )
    if not m:
        return head + sep + rest if head else text
    body = strip_cover_meta_block(m.group(2))
    return (head.rstrip() + "\n\n" if head.strip() else "") + m.group(1) + body + m.group(3)


def parse_cover_meta(max_post: str) -> dict[str, str]:
    header = max_post.split("\n---\n", 1)[0]
    line1 = re.search(r"Line 1:\s*(.+)", header)
    line2 = re.search(r"Line 2:\s*(.+)", header)
    line3 = re.search(r"Line 3:\s*(.+)", header)
    yellow = re.search(r"жёлтый:\s*(.+?)\)", header)
    if not (line1 and line2 and line3):
        raise SystemExit("Cannot parse cover lines from max-post.md (need Line 1/2/3 in header)")
    line2_text = re.sub(r"\s*\*\(жёлтый:.*", "", line2.group(1)).strip()
    yellow_word = yellow.group(1).strip() if yellow else ""
    if not yellow_word:
        yellow_word = line2_text.split()[-1] if line2_text else ""
    return {
        "line1": line1.group(1).strip(),
        "line2": line2_text,
        "line3": line3.group(1).strip(),
        "yellow": yellow_word,
    }


def outfit_block(topic_id: str) -> str:
    n = post_number_from_topic(topic_id) or 1
    slot = ((n - 1) % 12) + 1
    text = read_text(PROFILE / "cover-outfit-rotation.md", max_chars=20000)
    for line in text.splitlines():
        if line.startswith(f"| **{slot}** |") or line.startswith(f"| {slot} |"):
            m = re.search(r"`(OUTFIT:.*?)`", line)
            if m:
                return m.group(1)
    raise SystemExit(f"OUTFIT slot {slot} not found in cover-outfit-rotation.md")


def build_cover_prompt(topic_id: str, cover_meta: dict[str, str]) -> str:
    template_path = PROFILE / "social-cover-prompt-template.md"
    template = read_text(template_path, max_chars=20000)
    m = re.search(r"```\n(YouTube thumbnail[\s\S]+?)```", template)
    if not m:
        raise SystemExit("Cannot extract cover template from social-cover-prompt-template.md")
    block = m.group(1)
    block = block.replace("{OUTFIT_BLOCK}", outfit_block(topic_id))
    block = block.replace("{LINE1}", cover_meta["line1"])
    block = block.replace("{LINE2}", cover_meta["line2"])
    block = block.replace("{LINE3}", cover_meta["line3"])
    block = block.replace("{YELLOW_WORD}", cover_meta["yellow"] or cover_meta["line2"].split()[-1])
    return block.strip() + "\n"


def build_max_user_prompt(brief: dict[str, str]) -> str:
    post_num = int(brief["post_number"])
    contract = read_text(PROFILE / PLATFORM_SPECS["max"]["prompt"])
    registry = registry_excerpt(PLATFORM_SPECS["max"]["registry"])
    return f"""Создай файл max-post.md для темы MSP short-blog.

topic_id: {brief['topic_id']}
Заголовок темы: {brief['title']}
Формат: {brief['format']}
Номер MSP: #{brief['post_number']}
Сайт (для финальной ссылки): {brief['site_url']}?utm_source=max
EMDR-лендинг: https://morozovanatalia.ru/emdr-therapy?utm_source=max

{cta_context(post_num)}

Контракт max-post:
{contract}

Реестр для перелинковки (max → max, последние посты):
{registry}

Общий контекст:
{shared_context()}

В шапке файла (ДО `---` и `## Текст поста`) обязательно блок **Обложка:** с Line 1/2/3 и *(жёлтый: слово)*.
**Запрещено** дублировать блок Обложка / Line 1/2/3 / OUTFIT внутри `## Текст поста` — туда только читаемый текст поста.
Целевой объём ## Текст поста: 3500–3800 символов.
"""


def build_rewrite_user_prompt(
    platform: str,
    brief: dict[str, str],
    spec: dict[str, str],
    max_post: str,
) -> str:
    post_num = int(brief["post_number"])
    contract = read_text(PROFILE / spec["prompt"])
    registry = registry_excerpt(spec["registry"])
    utm_map = {
        "telegram": "tg1",
        "vk-profile": "vk",
        "vk-group": "vk_group",
        "facebook": "fb",
        "ok": "ok",
        "b17": "b17",
    }
    utm = utm_map.get(platform, "max")
    extra = spec.get("note", "")
    return f"""Создай файл {spec['output']} — рерайт (НЕ копипаст) max-post.md.

topic_id: {brief['topic_id']}
Заголовок: {brief['title']}
Сайт для финальной ссылки: {brief['site_url']}?utm_source={utm}

{cta_context(post_num)}
{extra}

Контракт платформы:
{contract}

Реестр перелинковки ({platform}):
{registry}

Исходник max-post.md:
---
{max_post}
---

Общий контекст:
{shared_context()}
"""


def generate_platform(
    platform: str,
    *,
    api_key: str,
    base_url: str,
    model: str,
    brief: dict[str, str],
    max_post: str | None,
    temperature: float,
    timeout_sec: int,
) -> tuple[str, dict[str, Any]]:
    spec = PLATFORM_SPECS[platform]
    if spec["kind"] == "source":
        user_prompt = build_max_user_prompt(brief)
    else:
        if not max_post:
            raise SystemExit(f"max-post.md required before generating {platform}")
        user_prompt = build_rewrite_user_prompt(platform, brief, spec, max_post)

    result = chat_completion(
        api_key=api_key,
        base_url=base_url,
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        timeout_sec=timeout_sec,
    )
    text = postprocess_platform(platform, result.content)
    text, contract_fixes = ensure_platform_contract(platform, text, brief)
    meta = {
        "model": result.model,
        "usage": result.usage,
        "chars": len(text),
        "contract_fixes": contract_fixes,
    }
    return text, meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Grsai text generation for Posts EMDR")
    parser.add_argument("--topic", required=True, help="topic_id e.g. sb-10-phrase-when-anxiety")
    parser.add_argument(
        "--platform",
        choices=list(PLATFORM_SPECS.keys()) + ["all"],
        default="all",
        help="Generate one platform or all (default: all)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan only, no API calls")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if output file already exists (default: skip existing)",
    )
    parser.add_argument("--temperature", type=float, default=0.7)
    args = parser.parse_args()

    brief = load_topic_brief(args.topic)
    out_dir = MEMORY / "output" / args.topic
    out_dir.mkdir(parents=True, exist_ok=True)

    platforms = GENERATION_ORDER if args.platform == "all" else [args.platform]
    if args.platform != "all" and args.platform != "max":
        if "max" not in platforms and not (out_dir / "max-post.md").is_file():
            raise SystemExit("max-post.md missing — generate max first")

    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "topic": brief,
                    "platforms": platforms,
                    "output_dir": str(out_dir),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    env = load_env("grsai.env.local", required=["GRSAI_API_KEY"])
    api_key = env["GRSAI_API_KEY"]
    base_url = env.get("GRSAI_API_BASE", "https://grsaiapi.com")
    model = env.get("GRSAI_CHAT_MODEL", "gemini-3.1-pro")

    model = env.get("GRSAI_CHAT_MODEL", "gemini-3.1-pro")
    timeout_raw = env.get("GRSAI_CHAT_TIMEOUT_SEC", str(DEFAULT_TIMEOUT_SEC)).strip()
    try:
        timeout_sec = max(120, int(timeout_raw))
    except ValueError:
        timeout_sec = DEFAULT_TIMEOUT_SEC

    log_path = out_dir / "grsai-content-log.json"
    log: dict[str, Any] = {}
    if log_path.is_file():
        try:
            log = json.loads(log_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log = {}
    log.update(
        {
            "topic": args.topic,
            "backend": "grsai",
            "model": model,
            "base_url": base_url,
            "timeout_sec": timeout_sec,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    log.setdefault("platforms", {})

    max_post: str | None = None
    max_path = out_dir / "max-post.md"
    if max_path.is_file():
        max_post = max_path.read_text(encoding="utf-8")

    for platform in platforms:
        out_name = PLATFORM_SPECS[platform]["output"]
        out_path = out_dir / out_name
        if out_path.is_file() and not args.force:
            print(f"Skip {platform} (exists): {out_name}", file=sys.stderr)
            log["platforms"].setdefault(
                platform,
                {"file": out_name, "skipped": True, "chars": len(out_path.read_text(encoding="utf-8"))},
            )
            if platform == "max":
                max_post = out_path.read_text(encoding="utf-8")
            continue

        if platform != "max" and not max_post:
            raise SystemExit("max-post.md missing — generate max first")

        print(f"Generating {platform} (timeout {timeout_sec}s)...", file=sys.stderr)
        text, meta = generate_platform(
            platform,
            api_key=api_key,
            base_url=base_url,
            model=model,
            brief=brief,
            max_post=max_post,
            temperature=args.temperature,
            timeout_sec=timeout_sec,
        )
        out_path.write_text(text + "\n", encoding="utf-8")
        log["platforms"][platform] = {"file": out_name, **meta}
        print(f"  → {out_name} ({meta['chars']} chars)", file=sys.stderr)

        if platform == "max":
            max_post = text
            cover_meta = parse_cover_meta(text)
            cover_prompt = build_cover_prompt(args.topic, cover_meta)
            cover_path = out_dir / "cover-prompt.txt"
            if not cover_path.is_file() or args.force:
                cover_path.write_text(cover_prompt, encoding="utf-8")
                log["cover_prompt"] = {"chars": len(cover_prompt), "cover_meta": cover_meta}
                print("  → cover-prompt.txt", file=sys.stderr)
            else:
                print("  → cover-prompt.txt (exists, skip)", file=sys.stderr)

    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "topic": args.topic, "log": str(log_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
