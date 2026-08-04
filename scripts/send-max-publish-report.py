#!/usr/bin/env python3
"""Отправить отчёт о публикации в ЛС Макс-бота (MAX_PREVIEW_CHAT_ID).

Usage:
  python3 scripts/verify-publish-run.py --topic sb-05 --write
  python3 scripts/send-max-publish-report.py --topic sb-05

  python3 scripts/send-max-publish-report.py --text "✅ Тест отчёта"
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from posts_emdr_env import MEMORY, PROJECT_ROOT


def _load_verify():
    spec = importlib.util.spec_from_file_location(
        "verify_publish_run", PROJECT_ROOT / "scripts" / "verify-publish-run.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def _load_send_max():
    spec = importlib.util.spec_from_file_location(
        "send_max_draft", PROJECT_ROOT / "scripts" / "send-max-draft.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def main() -> None:
    parser = argparse.ArgumentParser(description="Send publish report to Max DM")
    parser.add_argument("--topic")
    parser.add_argument("--text", help="Custom report text (overrides --topic)")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.text and not args.topic:
        raise SystemExit("Укажите --topic или --text")

    smd = _load_send_max()
    vpr = _load_verify()
    env = smd.load_env()
    token = env.get("MAX_BOT_TOKEN", "")
    if not token:
        raise SystemExit("MAX_BOT_TOKEN empty")

    chat_raw = env.get("MAX_PREVIEW_CHAT_ID") or env.get("MAX_DM_CHAT_ID") or ""
    if not chat_raw:
        raise SystemExit(
            "MAX_PREVIEW_CHAT_ID не задан. Напишите боту в ЛС и:\n"
            "  python3 scripts/send-max-draft.py --resolve-chat-id"
        )
    chat_id = smd.parse_chat_id(chat_raw)
    insecure = env.get("MAX_API_INSECURE_TLS", "true").lower() == "true"

    report = None
    if args.text:
        body = args.text
    else:
        report_path = MEMORY / "output" / args.topic / "publish-run-report.json"
        if report_path.is_file():
            report = json.loads(report_path.read_text(encoding="utf-8"))
        else:
            report = vpr.verify_topic(args.topic)
            report_path.write_text(
                json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        body = vpr.format_report_md(report)

    if args.dry_run:
        print(json.dumps({"chars": len(body), "preview": body[:500]}, ensure_ascii=False, indent=2))
        return

    result = smd.send_message(
        token,
        body,
        chat_id=chat_id,
        insecure_tls=insecure,
    )
    log = {
        "status": "sent",
        "topic": args.topic,
        "chat_id": chat_id,
        "overall": (report or {}).get("overall"),
        "result": result,
    }
    if args.topic:
        log_path = MEMORY / "output" / args.topic / "max-report-log.json"
        log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "sent", "topic": args.topic, "chars": len(body)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
