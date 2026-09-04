#!/usr/bin/env python3
"""Закрыть тему MSP short-blog в Cloud без VPS.

После 5 основных платформ + Telegram:
  - mark-short-blog-published (очередь)
  - browser-worker-finish.json (--force-b17-optional)
  - b17 → repair-пул, если не published

Usage:
  python3 scripts/close-cloud-publish.py --topic sb-25-before-saying-yes
  python3 scripts/close-cloud-publish.py --topic sb-25 --dry-run
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_worker_finish import finish_topic
from posts_emdr_env import MEMORY

SCRIPTS = Path(__file__).resolve().parent


def _verify_topic(topic: str) -> dict:
    spec = importlib.util.spec_from_file_location("verify_publish_run", SCRIPTS / "verify-publish-run.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod.verify_topic(topic)

B17_QUEUE = MEMORY / "b17-tenchat-pending-queue.md"


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def ensure_b17_repair_pending(topic_id: str) -> dict:
    topic_dir = MEMORY / "output" / topic_id
    b17_log = _read_json(topic_dir / "b17-publish-log.json")
    status = (b17_log or {}).get("status")
    if status == "published":
        return {"skipped": True, "reason": "b17_published"}
    if not (topic_dir / "b17-blog-post.md").is_file():
        return {"skipped": True, "reason": "no_b17-blog-post.md"}

    if not B17_QUEUE.is_file():
        return {"skipped": True, "reason": "missing_b17_queue_file"}

    text = B17_QUEUE.read_text(encoding="utf-8")
    if f"`{topic_id}`" in text and "| `b17` |" in text:
        return {"skipped": True, "reason": "already_in_queue"}

    row_status = "draft_saved" if status == "draft_saved" else "pending"
    row = f"| `{topic_id}` | `b17` | `{row_status}` | {date.today().isoformat()} | — |"
    lines = text.splitlines()
    insert_at = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|----------|") and i > 0 and "topic_id" in lines[i - 1]:
            insert_at = i + 1
            break
    if insert_at is None:
        raise SystemExit(f"Cannot find table in {B17_QUEUE}")
    lines.insert(insert_at, row)
    B17_QUEUE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {"added": True, "status": row_status, "path": str(B17_QUEUE)}


def close_topic(topic_id: str, *, dry_run: bool = False) -> dict:
    report = _verify_topic(topic_id)
    overall = report.get("overall")
    if overall not in {"pass", "pass_b17_pending"}:
        raise SystemExit(
            f"BLOCKER close-cloud-publish: verify={overall}\n"
            + "\n".join(f"  - {i}" for i in report.get("issues") or [])
        )

    out = {
        "topic": topic_id,
        "verify": overall,
        "dry_run": dry_run,
        "b17_repair": None,
        "finish": None,
    }
    if dry_run:
        out["b17_repair"] = {"dry_run": True}
        out["finish"] = {"dry_run": True}
        return out

    out["b17_repair"] = ensure_b17_repair_pending(topic_id)
    finish = finish_topic(topic_id, force_b17_optional=True)
    finish["mode"] = "cloud_no_vps"
    topic_dir = MEMORY / "output" / topic_id
    (topic_dir / "browser-worker-finish.json").write_text(
        json.dumps(finish, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    cloud_finish = {
        "topic": topic_id,
        "status": "cloud_publish_closed",
        "date": date.today().isoformat(),
        "mode": "cloud_no_vps",
        "verify": overall,
        "b17_repair": out["b17_repair"],
    }
    (topic_dir / "cloud-publish-finish.json").write_text(
        json.dumps(cloud_finish, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    from posts_emdr_handoff import write_handoff_done

    write_handoff_done(topic_id, verify=overall)
    out["finish"] = finish
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Close MSP topic in Cloud without VPS")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    result = close_topic(args.topic, dry_run=args.dry_run)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
