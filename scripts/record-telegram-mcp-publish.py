#!/usr/bin/env python3
"""Записать результат Telegram MCP после telegram_send_message × N."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, normalize_telegram_chat_id, load_env
from vps_publish_guard import mark_telegram_sent

SCRIPTS = Path(__file__).resolve().parent


def _channel_slug(chat_id: str) -> str:
    return chat_id.strip().lstrip("@").lower()


def _post_url(chat_id: str, message_id: int | str) -> str:
    slug = _channel_slug(chat_id)
    if slug.startswith("-") or slug.isdigit():
        return f"https://t.me/c/{slug.lstrip('-')}/{message_id}"
    return f"https://t.me/{slug}/{message_id}"


def main() -> None:
    parser = argparse.ArgumentParser(description="Record Telegram MCP publish")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--chat-id", required=True)
    parser.add_argument("--message-id", required=True, type=int)
    parser.add_argument("--utm-source", default="")
    parser.add_argument("--merge", action="store_true", help="Merge into existing telegram-publish-log.json")
    args = parser.parse_args()

    topic_dir = MEMORY / "output" / args.topic
    if not topic_dir.is_dir():
        raise SystemExit(f"Missing output/{args.topic}")

    log_path = topic_dir / "telegram-publish-log.json"
    channels: list[dict] = []
    if args.merge and log_path.is_file():
        try:
            existing = json.loads(log_path.read_text(encoding="utf-8"))
            channels = list(existing.get("channels") or [])
        except json.JSONDecodeError:
            channels = []

    env = load_env("telegram.env.local")
    chat_id = normalize_telegram_chat_id(args.chat_id, env)

    entry = {
        "chat_id": chat_id,
        "message_id": args.message_id,
        "post_url": _post_url(chat_id, args.message_id),
        "utm_source": args.utm_source or None,
        "via": "mcp-kv",
    }
    channels = [c for c in channels if str(c.get("chat_id")) != str(args.chat_id) and str(c.get("chat_id")) != chat_id]
    channels.append(entry)

    log = {
        "status": "sent",
        "mode": "publish",
        "delivery": "link_preview_single_message",
        "via": "mcp-kv",
        "channels": channels,
    }
    if len(channels) == 1:
        log["chat_id"] = channels[0]["chat_id"]
        log["message_id"] = channels[0]["message_id"]

    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mark_telegram_sent(args.topic, log)

    handoff = topic_dir / "telegram-mcp-handoff.json"
    title = args.topic
    site_url = ""
    if handoff.is_file():
        try:
            data = json.loads(handoff.read_text(encoding="utf-8"))
            site_url = data.get("site_url") or ""
        except json.JSONDecodeError:
            pass

    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "update-post-registry.py"),
            "--platform",
            "telegram",
            "--topic-id",
            args.topic,
            "--title",
            title,
            "--url",
            entry["post_url"],
            "--site-url",
            site_url or "https://morozovanatalia.ru/anxiety",
            "--channel",
            chat_id,
        ],
        cwd=SCRIPTS.parent,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        raise SystemExit(proc.stderr or proc.stdout)

    print(json.dumps({"ok": True, "log": str(log_path), "entry": entry}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
