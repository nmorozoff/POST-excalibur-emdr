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
from posts_emdr_env import load_env, validate_telegram_channels


def main() -> None:
    try:
        env = load_env("telegram.env.local", required=["TELEGRAM_BOT_TOKEN"])
    except SystemExit as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        sys.exit(2)

    result = validate_telegram_channels(env, require_two=False)
    report = {
        **result,
        "utm_sources": env.get("TELEGRAM_CHANNEL_UTM_SOURCES", "tg1"),
        "has_bot_token": bool(env.get("TELEGRAM_BOT_TOKEN")),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("ok") else 2)


if __name__ == "__main__":
    main()
