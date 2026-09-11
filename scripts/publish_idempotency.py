#!/usr/bin/env python3
"""Идемпотентность публикаций — не слать повторно Max/TG/VK и т.д."""

from __future__ import annotations

import json
from pathlib import Path

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY
from vps_publish_guard import read_platform_marker, restore_telegram_log_from_marker


def topic_dir(topic: str) -> Path:
    return MEMORY / "output" / topic


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (json.JSONDecodeError, OSError):
        return None


def max_already_published(topic: str) -> bool:
    log = _read_json(topic_dir(topic) / "max-publish-log.json")
    return bool(log and log.get("status") in {"ok", "sent"})


def telegram_already_published(topic: str) -> bool:
    td = topic_dir(topic)
    restore_telegram_log_from_marker(td, topic)
    marker = read_platform_marker(topic, "telegram")
    if marker and marker.get("status") in {"sent", "published"}:
        return True
    log = _read_json(td / "telegram-publish-log.json")
    return bool(log and log.get("status") == "sent")


def telegram_cover_ok(topic: str) -> bool:
    """Только для repair: --refresh-cover-url --force. Автопрогон не переотправляет TG."""
    log = _read_json(topic_dir(topic) / "telegram-publish-log.json")
    if not log or log.get("status") != "sent":
        return False
    src = (log.get("cover_source") or "").lower()
    if not src or "oneme" in src:
        return False
    return True


def core_social_already_published(topic: str) -> bool:
    """Макс + Telegram уже ушли — больше не трогать в cron (даже если VK не закрыт)."""
    return max_already_published(topic) and telegram_already_published(topic)


def vk_location_published(topic: str, location: str) -> bool:
    log_path = topic_dir(topic) / "vk-publish-log.json"
    if not log_path.is_file():
        return False
    try:
        raw = json.loads(log_path.read_text(encoding="utf-8"))
        rows = raw if isinstance(raw, list) else [raw]
    except json.JSONDecodeError:
        return False
    return any(
        r.get("location") == location and r.get("status") in {"published", "ok", "sent"}
        for r in rows
    )


def facebook_already_published(topic: str) -> bool:
    log = _read_json(topic_dir(topic) / "zernio-publish-log.json")
    return bool(log and log.get("status") in {"published", "ok", "sent"})


def ok_already_published(topic: str) -> bool:
    log = _read_json(topic_dir(topic) / "ok-publish-log.json")
    return bool(log and log.get("status") in {"published", "ok", "sent"})


def b17_already_saved(topic: str) -> bool:
    log = _read_json(topic_dir(topic) / "b17-publish-log.json")
    return bool(log and log.get("status") in {"draft_saved", "published", "ok"})


def tenchat_already_published(topic: str) -> bool:
    log = _read_json(topic_dir(topic) / "tenchat-publish-log.json")
    return bool(log and log.get("status") in {"published", "ready_for_publish", "ok"})
