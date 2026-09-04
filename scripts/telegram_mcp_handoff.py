#!/usr/bin/env python3
"""Telegram publish via MCP mcp-kv (Bot API с серверов mcp-kv, без VPS/ASocks)."""

from __future__ import annotations

import json
import re
from pathlib import Path

from posts_emdr_env import (
    MEMORY,
    ensure_client_story_disclaimer,
    rewrite_telegram_interlinks,
    sanitize_post_text,
    telegram_interlink_issues,
)

TELEGRAM_HTML_SECTION_RE = re.compile(r"^## Текст поста \(HTML[^\n]*\n+", re.M)


def extract_telegram_html(md_text: str) -> str:
    text = md_text.strip()
    if "<!-- END_POST -->" in text:
        body, _, _ = text.partition("<!-- END_POST -->")
        text = body.strip()
    m = TELEGRAM_HTML_SECTION_RE.search(text)
    if m:
        tail = text[m.end() :].lstrip("\n")
        if "\n---\n" in tail:
            tail = tail.split("\n---\n", 1)[0]
        return tail.strip()
    m2 = re.search(r"^## Текст поста\n\n(.*?)(?:\n\n---\n|\Z)", text, re.S | re.M)
    if m2:
        return m2.group(1).strip()
    raise ValueError("telegram-post.md: нет секции ## Текст поста (HTML)")


def format_mcp_message(html: str, cover_url: str) -> str:
    """MCP telegram_send_message: bare URL в начале (нет link_preview_options в MCP)."""
    html = sanitize_post_text(html)
    html = re.sub(r"<i>\s*<i>", "<i>", html)
    html = re.sub(r"</i>\s*</i>", "</i>", html)
    cover = cover_url.strip()
    if cover and cover not in html:
        text = f"{cover}\n\n{html}"
    else:
        text = html
    if len(text) > 4096:
        raise SystemExit(
            f"Telegram MCP: текст {len(text)} > 4096. Укоротите telegram-post.md на {len(text) - 4096} символов."
        )
    return text


def strip_cover_preview_prefix(text: str, cover_url: str) -> str:
    """Убрать hack-обложку из handoff перед sendMessage + link_preview_options."""
    body = text.strip()
    cover = (cover_url or "").strip()
    if not cover:
        return body
    anchor = f'<a href="{cover}"></a>'
    if body.startswith(anchor):
        return body[len(anchor) :].lstrip("\n")
    if body.startswith(cover):
        return body[len(cover) :].lstrip("\n")
    return body


def parse_channel_ids(env: dict[str, str]) -> list[str]:
    raw = env.get("TELEGRAM_CHANNEL_CHAT_IDS", "").strip()
    if raw:
        ids = [item.strip() for item in raw.split(",") if item.strip()]
        if ids:
            return ids
    single = env.get("TELEGRAM_CHANNEL_CHAT_ID") or env.get("TELEGRAM_CHAT_ID", "")
    return [single] if single else []


def parse_channel_utm_sources(env: dict[str, str], channel_count: int) -> list[str]:
    raw = env.get("TELEGRAM_CHANNEL_UTM_SOURCES", "").strip()
    if raw:
        sources = [item.strip() for item in raw.split(",") if item.strip()]
        if len(sources) == channel_count:
            return sources
    return [f"tg{index}" for index in range(1, channel_count + 1)]


def apply_utm_source(html: str, utm_source: str) -> str:
    return re.sub(r"utm_source=(?:tg\d*|tg)\b", f"utm_source={utm_source}", html)


def build_channel_calls(topic: str, cover_url: str) -> list[dict]:
    from posts_emdr_env import assert_telegram_channels, load_env

    topic_dir = MEMORY / "output" / topic
    post_file = topic_dir / "telegram-post.md"
    if not post_file.is_file():
        raise SystemExit(f"Missing {post_file}")

    env = load_env("telegram.env.local")
    assert_telegram_channels(env, context="telegram MCP handoff", require_two=False)
    chat_ids = parse_channel_ids(env)
    utm_sources = parse_channel_utm_sources(env, len(chat_ids))

    base_html = ensure_client_story_disclaimer(extract_telegram_html(post_file.read_text(encoding="utf-8")), "telegram")
    calls: list[dict] = []
    for chat_id, utm_source in zip(chat_ids, utm_sources):
        channel_html = rewrite_telegram_interlinks(base_html, chat_id)
        channel_html = apply_utm_source(channel_html, utm_source)
        for issue in telegram_interlink_issues(channel_html, chat_id):
            raise SystemExit(f"BLOCKER telegram MCP: {issue}")
        calls.append(
            {
                "chat_id": chat_id,
                "utm_source": utm_source,
                "parse_mode": "HTML",
                "text": format_mcp_message(channel_html, cover_url),
                "text_chars": len(channel_html),
            }
        )
    return calls


def write_telegram_mcp_handoff(topic: str, cover_url: str) -> Path:
    topic_dir = MEMORY / "output" / topic
    calls = build_channel_calls(topic, cover_url)
    handoff = {
        "topic": topic,
        "method": "mcp-kv",
        "tool": "telegram_send_message",
        "delivery": "link_preview_single_message",
        "cover_public_url": cover_url,
        "instructions": "posts-emdr-memory/profile/cloud-publish-phases.md",
        "calls": calls,
        "record_after_publish": (
            f"python3 scripts/record-telegram-mcp-publish.py --topic {topic} "
            "--chat-id <chat_id> --message-id <id> --utm-source <utm>"
        ),
    }
    path = topic_dir / "telegram-mcp-handoff.json"
    path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def resolve_cover_url(topic: str) -> str:
    from cover_upload import load_upload_env, prepare_jpeg, public_cover_url, upload_cover, verify_cover_url

    topic_dir = MEMORY / "output" / topic
    remote_name = f"{topic}.jpg"
    site_url = public_cover_url(remote_name)
    probe = verify_cover_url(site_url)
    if probe.get("ok") and "oneme.ru" not in site_url.lower():
        return site_url

    cover = topic_dir / "cover.png"
    if cover.is_file():
        try:
            uploaded = upload_cover(prepare_jpeg(cover), remote_name, load_upload_env())
            candidate = uploaded["url"]
            if verify_cover_url(candidate).get("ok"):
                return candidate
        except SystemExit:
            pass

    for path in (topic_dir / "vk-publish-prep.json", topic_dir / "vk-mcp-handoff.json"):
        if not path.is_file():
            continue
        try:
            url = (json.loads(path.read_text(encoding="utf-8")).get("cover_public_url") or "").strip()
            if url and "oneme.ru" not in url.lower() and verify_cover_url(url).get("ok"):
                return url
        except json.JSONDecodeError:
            continue
    raise SystemExit(f"No image/jpeg cover_public_url for {topic} (run send-vk-post --upload-cover first)")
