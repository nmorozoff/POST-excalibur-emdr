#!/usr/bin/env python3
"""Проверить, опубликована ли тема уже end-to-end.

Usage:
  python3 scripts/is-topic-published.py --topic sb-05-tolerate-uncertainty
  python3 scripts/is-topic-published.py --topic sb-05 --json

Exit codes:
  0 — тема опубликована (5 платформ + Telegram + закрыта в очереди)
  1 — тема не найдена или не полностью опубликована
  2 — cloud готов, но тема ещё не закрыта (нужен close-cloud-publish.py)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, telegram_channel_slug


PROFILE = MEMORY / "profile"


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _registry_has_topic(topic: str, registry: Path) -> bool:
    if not registry.is_file():
        return False
    text = registry.read_text(encoding="utf-8")
    return f"| {topic} " in text or f"| `{topic}`" in text


def _queue_published(topic: str) -> bool:
    published = MEMORY / "topics" / "short-blog-published.md"
    return published.is_file() and f"`{topic}`" in published.read_text(encoding="utf-8")


def _telegram_sent(topic_dir: Path) -> bool:
    tg_log = _read_json(topic_dir / "telegram-publish-log.json")
    if not tg_log or tg_log.get("status") != "sent":
        return False
    channels = tg_log.get("channels") or []
    if not channels:
        return bool(tg_log.get("message_id"))
    slugs = {
        telegram_channel_slug(str(c.get("chat_id", "")), post_url=str(c.get("post_url") or ""))
        for c in channels
    }
    slugs.discard("")
    return "nmorozova_emdr" in slugs


def check_topic(topic: str) -> dict:
    topic_dir = MEMORY / "output" / topic
    result = {
        "topic": topic,
        "published": False,
        "partial": False,
        "reasons": [],
        "cloud_ok": False,
        "closed": False,
    }

    if not topic_dir.is_dir():
        result["reasons"].append(f"Нет папки output/{topic}")
        return result

    max_log = _read_json(topic_dir / "max-publish-log.json")
    max_ok = bool(max_log and max_log.get("status") in {"sent", "ok"})
    vk_prof = _registry_has_topic(topic, PROFILE / "vk-profile-posts-registry.md")
    vk_group = _registry_has_topic(topic, PROFILE / "vk-group-posts-registry.md")
    fb_log = _read_json(topic_dir / "zernio-publish-log.json")
    fb_ok = bool(fb_log and fb_log.get("status") in {"published", "ok", "sent"})
    fb_reg = _registry_has_topic(topic, PROFILE / "facebook-posts-registry.md")
    ok_required = (topic_dir / "ok-post.md").is_file()
    ok_log = _read_json(topic_dir / "ok-publish-log.json")
    ok_ok = bool(ok_log and ok_log.get("status") in {"published", "ok", "sent"})
    ok_reg = _registry_has_topic(topic, PROFILE / "ok-posts-registry.md")

    cloud_ok = max_ok and vk_prof and vk_group and (fb_ok or fb_reg)
    if ok_required:
        cloud_ok = cloud_ok and (ok_ok or ok_reg)
    result["cloud_ok"] = cloud_ok
    if not cloud_ok:
        if not max_ok:
            result["reasons"].append("Макс не опубликован")
        if not vk_prof:
            result["reasons"].append("VK профиль не в реестре")
        if not vk_group:
            result["reasons"].append("VK группа не в реестре")
        if not (fb_ok or fb_reg):
            result["reasons"].append("Facebook не опубликован")
        if ok_required and not (ok_ok or ok_reg):
            result["reasons"].append("OK не опубликован")

    tg_ok = _telegram_sent(topic_dir)
    if not tg_ok:
        result["reasons"].append("Telegram не опубликован")

    queue_published = _queue_published(topic)
    finish_json = (topic_dir / "browser-worker-finish.json").is_file() or (
        topic_dir / "cloud-publish-finish.json"
    ).is_file()
    closed = queue_published or finish_json
    result["closed"] = closed

    if cloud_ok and tg_ok and closed:
        result["published"] = True
    elif cloud_ok and tg_ok and not closed:
        result["partial"] = True
        result["reasons"].append("Cloud готов — запустите close-cloud-publish.py")

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Check if topic is already published")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    result = check_topic(args.topic)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        if result["published"]:
            print(f"✅ {args.topic} — уже опубликована end-to-end")
        elif result["partial"]:
            print(f"⏳ {args.topic} — cloud ok, нужен close-cloud-publish")
            for r in result["reasons"]:
                print(f"  {r}")
        else:
            print(f"❌ {args.topic} — не опубликована")
            for r in result["reasons"]:
                print(f"  {r}")

    if result["published"]:
        sys.exit(0)
    if result["partial"]:
        sys.exit(2)
    sys.exit(1)


if __name__ == "__main__":
    main()
