#!/usr/bin/env python3
"""Validate Telegram env before VPS webhook (cloud step 5 gate).

Usage:
  python3 scripts/verify-telegram-env.py
  python3 scripts/materialize_cloud_env.py && python3 scripts/verify-telegram-env.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import load_env

ALLOWED = ("nmorozova_emdr", "natalia_morozova_psy")
BANNED = ("morozova_emdr",)


def main() -> None:
    try:
        env = load_env("telegram.env.local", required=["TELEGRAM_BOT_TOKEN"])
    except SystemExit as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        sys.exit(2)

    raw = env.get("TELEGRAM_CHANNEL_CHAT_IDS", "").strip()
    if not raw:
        single = env.get("TELEGRAM_CHANNEL_CHAT_ID") or env.get("TELEGRAM_CHAT_ID", "")
        channels = [single.strip()] if single.strip() else []
    else:
        channels = [c.strip() for c in raw.split(",") if c.strip()]

    names = [c.lstrip("@") for c in channels]
    banned = [c for c in names if c in BANNED]
    wrong = [c for c in names if c not in ALLOWED]
    ok = len(channels) == 2 and not banned and not wrong

    report = {
        "ok": ok,
        "channels": channels,
        "expected": [f"@{n}" for n in ALLOWED],
        "utm_sources": env.get("TELEGRAM_CHANNEL_UTM_SOURCES", "tg1,tg2"),
        "has_bot_token": bool(env.get("TELEGRAM_BOT_TOKEN")),
    }
    if banned:
        report["error"] = f"BANNED channel @morozova_emdr in list: {channels}"
    elif wrong or len(channels) != 2:
        report["error"] = f"Expected @nmorozova_emdr,@natalia_morozova_psy got {channels}"

    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
