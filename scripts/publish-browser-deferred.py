#!/usr/bin/env python3
"""VPS worker: publish b17 + TenChat for topics deferred from cloud.

Linux VPS (Playwright) — cron:

  scripts/run-linux-browser-worker.sh

Или вручную:

  python3 scripts/fetch-topic-cover.py --all-pending
  python3 scripts/publish-browser-deferred.py --submit --finish
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_backend import browser_ready
from browser_worker_finish import finish_topic
from posts_emdr_env import MEMORY, PROJECT_ROOT, load_env

SCRIPTS = PROJECT_ROOT / "scripts"


def _log_status(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("status")
    except (json.JSONDecodeError, OSError):
        return None


def pending_topics(*, topic: str | None = None) -> list[str]:
    output = MEMORY / "output"
    if not output.is_dir():
        return []
    topics: list[str] = []
    for topic_dir in sorted(output.iterdir()):
        if not topic_dir.is_dir():
            continue
        tid = topic_dir.name
        if topic and tid != topic:
            continue
        handoff = topic_dir / "browser-local-handoff.md"
        done = topic_dir / "browser-local-handoff.done.md"
        if not handoff.is_file() and not done.is_file():
            continue
        if done.is_file() and _log_status(topic_dir / "b17-publish-log.json") == "published":
            if _log_status(topic_dir / "tenchat-publish-log.json") == "published":
                continue
        b17 = _log_status(topic_dir / "b17-publish-log.json")
        ten = _log_status(topic_dir / "tenchat-publish-log.json")
        if b17 == "published" and ten == "published" and done.is_file():
            continue
        topics.append(tid)
    return topics


def run_publish(topic: str, *, submit: bool) -> dict:
    submit_args = ["--submit"] if submit else []
    result: dict = {"topic": topic, "steps": {}}
    for script, key in (
        ("publish-b17-blog.py", "b17"),
        ("publish-tenchat-post.py", "tenchat"),
    ):
        log_path = MEMORY / "output" / topic / f"{key}-publish-log.json"
        if _log_status(log_path) == "published":
            result["steps"][key] = {"skipped": True, "reason": "already_published"}
            continue
        if key == "b17":
            b17_check = subprocess.run(
                [sys.executable, str(SCRIPTS / "check-b17-ip-access.py")],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            if b17_check.returncode != 0:
                result["steps"][key] = {
                    "skipped": True,
                    "reason": "b17_ip_blocked_on_host",
                    "detail": (b17_check.stdout or b17_check.stderr)[-500:],
                }
                continue
        proc = subprocess.run(
            [sys.executable, str(SCRIPTS / script), "--topic", topic, *submit_args],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        result["steps"][key] = {
            "exit_code": proc.returncode,
            "stdout_tail": proc.stdout[-2000:] if proc.stdout else "",
            "stderr_tail": proc.stderr[-1000:] if proc.stderr else "",
        }
        if proc.returncode != 0:
            result["status"] = "failed"
            return result
    result["status"] = "ok"
    return result


def git_push_changes(topic: str) -> dict:
    paths = [
        f"posts-emdr-memory/output/{topic}/",
        "posts-emdr-memory/profile/b17-posts-registry.md",
        "posts-emdr-memory/profile/tenchat-posts-registry.md",
        "posts-emdr-memory/topics/short-blog-queue.md",
        "posts-emdr-memory/topics/short-blog-published.md",
    ]
    subprocess.run(["git", "add", *paths], cwd=PROJECT_ROOT, check=False)
    msg = f"browser-worker: published {topic} (b17+tenchat)"
    commit = subprocess.run(
        ["git", "commit", "-m", msg],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if commit.returncode != 0 and "nothing to commit" not in (commit.stdout + commit.stderr):
        return {"committed": False, "stderr": commit.stderr}
    push = subprocess.run(
        ["git", "push", "origin", "HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return {
        "committed": commit.returncode == 0,
        "pushed": push.returncode == 0,
        "push_stderr": push.stderr[-500:] if push.stderr else "",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Publish deferred b17/TenChat from VPS")
    parser.add_argument("--topic", help="Single topic id (default: all pending)")
    parser.add_argument("--submit", action="store_true", help="Auto-click Save/Publish")
    parser.add_argument("--finish", action="store_true", help="Registries + queue after publish")
    parser.add_argument("--git-push", action="store_true", help="git commit+push after --finish")
    parser.add_argument("--list", action="store_true", help="List pending topics only")
    parser.add_argument("--dry-run", action="store_true", help="Do not call publish scripts")
    args = parser.parse_args()

    try:
        load_env("browser.env.local")
    except SystemExit:
        pass

    if not browser_ready():
        raise SystemExit(
            "Browser backend недоступен. Linux: BROWSER_BACKEND=playwright + storage state. "
            "См. posts-emdr-memory/profile/browser-linux-vps-setup.md"
        )

    pending = pending_topics(topic=args.topic)
    if args.list:
        print(json.dumps({"pending": pending}, ensure_ascii=False, indent=2))
        return

    if not pending:
        print(json.dumps({"pending": [], "status": "nothing_to_do"}, ensure_ascii=False, indent=2))
        return

    reports = []
    for tid in pending:
        if args.dry_run:
            reports.append({"topic": tid, "status": "dry_run"})
            continue
        report = run_publish(tid, submit=args.submit)
        if report.get("status") == "ok" and args.finish:
            try:
                report["finish"] = finish_topic(tid)
            except SystemExit as exc:
                report["finish"] = {"error": str(exc)}
                report["status"] = "finish_failed"
            if args.git_push and report.get("status") == "ok":
                report["git"] = git_push_changes(tid)
        reports.append(report)

    print(json.dumps({"pending_count": len(pending), "results": reports}, ensure_ascii=False, indent=2))
    failed = [r for r in reports if r.get("status") in {"failed", "finish_failed"}]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
