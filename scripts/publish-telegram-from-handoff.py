#!/usr/bin/env python3
"""Публикует Telegram из telegram-mcp-handoff.json через Bot API (без VPS proxy).

На Cloud Agent: предпочтительно MCP telegram_send_message (mcp-kv).
Локальный fallback: прямой Bot API если api.telegram.org доступен (Mac).

Usage:
  python3 scripts/publish-telegram-from-handoff.py --topic sb-23-grounding-exercise
  python3 scripts/publish-telegram-from-handoff.py --topic sb-23 --dry-run
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, load_env

SCRIPTS = Path(__file__).resolve().parent


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--direct", action="store_true", help="Без proxy (только если api.telegram.org доступен)")
    args = parser.parse_args()

    topic_dir = MEMORY / "output" / args.topic
    handoff_path = topic_dir / "telegram-mcp-handoff.json"
    if not handoff_path.is_file():
        raise SystemExit(f"Missing {handoff_path} — run publish-topic first")

    handoff = json.loads(handoff_path.read_text(encoding="utf-8"))
    calls = handoff.get("calls") or []
    if not calls:
        raise SystemExit("handoff calls empty")

    env = load_env("telegram.env.local")
    token = env.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN missing")

    if args.direct:
        os.environ["TELEGRAM_SKIP_PROXY"] = "1"
    else:
        os.environ.pop("TELEGRAM_SKIP_PROXY", None)
        from asocks_sync_proxy import sync_telegram_with_preflight

        sync_telegram_with_preflight(write=True)

    spec = importlib.util.spec_from_file_location("send_telegram_post", SCRIPTS / "send-telegram-post.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    send_post_with_cover_preview = mod.send_post_with_cover_preview

    results: list[dict] = []
    for call in calls:
        chat_id = call["chat_id"]
        text = call["text"]
        cover_url = handoff.get("cover_public_url") or ""
        if args.dry_run:
            results.append({"chat_id": chat_id, "chars": len(text), "dry_run": True})
            continue
        # Прямой API: link_preview как в send-telegram-post (если сеть позволяет).
        res = send_post_with_cover_preview(token, chat_id, text, cover_url)
        mid = res.get("result", {}).get("message_id")
        if not mid:
            raise SystemExit(f"send failed for {chat_id}: {res}")
        proc = __import__("subprocess").run(
            [
                sys.executable,
                str(SCRIPTS / "record-telegram-mcp-publish.py"),
                "--topic",
                args.topic,
                "--chat-id",
                chat_id,
                "--message-id",
                str(mid),
                "--utm-source",
                call.get("utm_source") or "",
                "--merge",
            ],
            cwd=SCRIPTS.parent,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            raise SystemExit(proc.stderr or proc.stdout)
        results.append({"chat_id": chat_id, "message_id": mid, "ok": True})

    print(json.dumps({"topic": args.topic, "via": "direct_bot_api", "results": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
