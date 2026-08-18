#!/usr/bin/env python3
"""Ручной repair для b17 и TenChat.

Эта автоматизация не запускается по cron — только по вашему ОК,
чтобы не долбить площадки и не получить бан аккаунта.

Usage:
  python3 scripts/repair-b17-tenchat.py --topic sb-18-water-in-stone
  python3 scripts/repair-b17-tenchat.py --limit 1
  python3 scripts/repair-b17-tenchat.py --list
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, PROJECT_ROOT

SCRIPTS = PROJECT_ROOT / "scripts"
PROFILE = MEMORY / "profile"
QUEUE = MEMORY / "b17-tenchat-pending-queue.md"
REPAIR_LOG = MEMORY / "b17-tenchat-repair-log.json"


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _log_status(topic_dir: Path, name: str) -> str | None:
    path = topic_dir / f"{name}-publish-log.json"
    log = _read_json(path)
    return log.get("status") if log else None


def _parse_queue() -> list[dict]:
    if not QUEUE.is_file():
        return []
    rows = []
    header_seen = False
    for line in QUEUE.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        if "topic_id" in line:
            header_seen = True
            continue
        if not header_seen or line.strip().startswith("|----------|"):
            continue
        parts = [p.strip() for p in line.split("|")][1:-1]
        if len(parts) < 4:
            continue
        rows.append(
            {
                "topic_id": parts[0].strip("`"),
                "platform": parts[1].strip("`"),
                "status": parts[2].strip("`"),
                "created_at": parts[3],
                "last_retry": parts[4] if len(parts) > 4 else "-",
            }
        )
    return [r for r in rows if r["status"] == "pending"]


def _update_queue(topic_id: str, platform: str, status: str) -> None:
    if not QUEUE.is_file():
        return
    lines = QUEUE.read_text(encoding="utf-8").splitlines()
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    new_lines = []
    for line in lines:
        if line.startswith("|") and f"`{topic_id}`" in line and f"`{platform}`" in line:
            parts = [p.strip() for p in line.split("|")][1:-1]
            if len(parts) >= 4:
                parts[2] = f"`{status}`"
                parts[4] = now
                line = "| " + " | ".join(parts) + " |"
        new_lines.append(line)
    QUEUE.write_text("\n".join(new_lines) + "\n", encoding="utf-8")


def _notify_max(text: str) -> None:
    """Send a short notification to Max DM via the same helper as publish reports."""
    import importlib.util

    try:
        spec = importlib.util.spec_from_file_location(
            "send_max_publish_report", PROJECT_ROOT / "scripts" / "send-max-publish-report.py"
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)  # type: ignore
        saved_argv = sys.argv[:]
        sys.argv = [str(PROJECT_ROOT / "scripts" / "send-max-publish-report.py"), "--text", text]
        mod.main()
        sys.argv = saved_argv
    except Exception as exc:
        print(f"[repair] Max notify failed: {exc}", file=sys.stderr)


def run_repair(topic_id: str, platform: str, submit: bool) -> dict:
    topic_dir = MEMORY / "output" / topic_id
    result = {"topic_id": topic_id, "platform": platform, "status": None}

    if platform == "b17":
        if _log_status(topic_dir, "b17") == "published":
            result["status"] = "already_published"
            return result
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "publish-b17-blog.py"), "--topic", topic_id]
            + (["--submit"] if submit else []),
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        result["exit_code"] = proc.returncode
        result["stderr_tail"] = (proc.stderr or "")[-400:]
        result["stdout_tail"] = (proc.stdout or "")[-400:]
        result["status"] = _log_status(topic_dir, "b17")
    elif platform == "tenchat":
        if _log_status(topic_dir, "tenchat") == "published":
            result["status"] = "already_published"
            return result
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "publish-tenchat-post.py"), "--topic", topic_id]
            + (["--submit"] if submit else []),
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        result["exit_code"] = proc.returncode
        result["stderr_tail"] = (proc.stderr or "")[-400:]
        result["stdout_tail"] = (proc.stdout or "")[-400:]
        result["status"] = _log_status(topic_dir, "tenchat")
    else:
        result["status"] = "unknown_platform"

    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Ручной repair b17 + TenChat")
    parser.add_argument("--topic", help="Конкретная тема")
    parser.add_argument("--platform", choices=["b17", "tenchat", "all"], default="all")
    parser.add_argument("--limit", type=int, default=1, help="Сколько тем обработать (default 1)")
    parser.add_argument("--submit", action="store_true", help="Автоклик Save/Publish")
    parser.add_argument("--sleep-sec", type=int, default=90, help="Пауза перед submit")
    parser.add_argument("--list", action="store_true", help="Показать очередь")
    args = parser.parse_args()

    if args.list:
        print(json.dumps({"pending": _parse_queue()}, ensure_ascii=False, indent=2))
        return

    pending = _parse_queue()
    if args.topic:
        pending = [r for r in pending if r["topic_id"] == args.topic]
    if not pending:
        print(json.dumps({"status": "ok", "note": "no pending topics"}, ensure_ascii=False, indent=2))
        return

    if args.platform != "all":
        pending = [r for r in pending if r["platform"] == args.platform]

    results = []
    for idx, row in enumerate(pending[: max(args.limit, 1)]):
        if idx > 0 and args.sleep_sec > 0:
            time.sleep(args.sleep_sec)
        elif idx == 0 and args.sleep_sec > 0:
            time.sleep(args.sleep_sec)

        result = run_repair(row["topic_id"], row["platform"], submit=args.submit)
        results.append(result)

        if result["status"] == "published":
            _update_queue(row["topic_id"], row["platform"], "done")
        else:
            _update_queue(row["topic_id"], row["platform"], "pending")

    failed = [r for r in results if r.get("status") != "published" and r.get("status") != "already_published"]
    summary = {
        "status": "ok" if not failed else "partial",
        "processed": len(results),
        "failed": len(failed),
        "results": results,
    }
    REPAIR_LOG.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if failed:
        topics = ", ".join(r["topic_id"] for r in failed)
        platforms = ", ".join(set(r["platform"] for r in failed))
        _notify_max(
            f"Repair b17/TenChat не удался:\n"
            f"Темы: {topics}\n"
            f"Платформы: {platforms}\n"
            f"Проверь вручную и запусти repair позже."
        )

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    sys.exit(0 if not failed else 1)


if __name__ == "__main__":
    main()
