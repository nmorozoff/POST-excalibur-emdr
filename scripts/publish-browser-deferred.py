#!/usr/bin/env python3
"""VPS worker: Telegram + b17 + TenChat for topics deferred from cloud.

Linux VPS (Playwright) — cron:

  scripts/run-linux-browser-worker.sh

Или вручную / webhook:

  python3 scripts/fetch-topic-cover.py --all-pending
  python3 scripts/publish-browser-deferred.py --submit --finish --git-push
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


def _telegram_done(topic_dir: Path) -> bool:
    status = _log_status(topic_dir / "telegram-publish-log.json")
    return status in {"sent", "published"}


def _platform_done(topic_dir: Path, key: str) -> bool:
    if key == "telegram":
        return _telegram_done(topic_dir)
    return _log_status(topic_dir / f"{key}-publish-log.json") == "published"


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
        # Need handoff OR explicit --topic, plus drafts
        has_drafts = (topic_dir / "telegram-post.md").is_file() or (
            topic_dir / "b17-blog-post.md"
        ).is_file()
        if topic:
            if has_drafts and not (
                _platform_done(topic_dir, "telegram")
                and _platform_done(topic_dir, "b17")
                and _platform_done(topic_dir, "tenchat")
                and done.is_file()
            ):
                topics.append(tid)
            continue
        if not handoff.is_file() and not done.is_file():
            continue
        if (
            done.is_file()
            and _platform_done(topic_dir, "telegram")
            and _platform_done(topic_dir, "b17")
            and _platform_done(topic_dir, "tenchat")
        ):
            continue
        if not has_drafts:
            continue
        topics.append(tid)
    return topics


def sync_telegram_proxy() -> dict:
    """ASocks KZ → TELEGRAM_PROXY_* перед Bot API."""
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "asocks_sync_proxy.py"), "--target", "telegram"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    out: dict = {
        "exit_code": proc.returncode,
        "stdout_tail": (proc.stdout or "")[-800:],
        "stderr_tail": (proc.stderr or "")[-400:],
    }
    if proc.returncode != 0:
        # Не блокируем, если TELEGRAM_PROXY_* уже в browser.env.local
        try:
            env = load_env("browser.env.local")
            if env.get("TELEGRAM_PROXY_SERVER"):
                out["fallback"] = "existing_TELEGRAM_PROXY_SERVER"
                out["ok"] = True
                return out
        except SystemExit:
            pass
        out["ok"] = False
        return out
    out["ok"] = True
    return out


def run_publish(topic: str, *, submit: bool) -> dict:
    submit_args = ["--submit"] if submit else []
    result: dict = {"topic": topic, "steps": {}}
    topic_dir = MEMORY / "output" / topic

    # 1) Telegram via ASocks KZ
    if not _telegram_done(topic_dir):
        if not (topic_dir / "telegram-post.md").is_file():
            result["steps"]["telegram"] = {"skipped": True, "reason": "no_telegram-post.md"}
        else:
            result["steps"]["telegram_proxy"] = sync_telegram_proxy()
            if not result["steps"]["telegram_proxy"].get("ok"):
                result["steps"]["telegram"] = {
                    "skipped": True,
                    "reason": "telegram_proxy_sync_failed",
                    "detail": result["steps"]["telegram_proxy"],
                }
                result["status"] = "failed"
                return result
            proc = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "send-telegram-post.py"),
                    "--topic",
                    topic,
                    "--publish",
                ],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            result["steps"]["telegram"] = {
                "exit_code": proc.returncode,
                "stdout_tail": proc.stdout[-2000:] if proc.stdout else "",
                "stderr_tail": proc.stderr[-1000:] if proc.stderr else "",
            }
            if proc.returncode != 0:
                result["status"] = "failed"
                return result
    else:
        result["steps"]["telegram"] = {"skipped": True, "reason": "already_published"}

    # 2–3) b17 + TenChat
    for script, key in (
        ("publish-b17-blog.py", "b17"),
        ("publish-tenchat-post.py", "tenchat"),
    ):
        if _platform_done(topic_dir, key):
            result["steps"][key] = {"skipped": True, "reason": "already_published"}
            continue
        md_name = "b17-blog-post.md" if key == "b17" else "tenchat-post.md"
        if not (topic_dir / md_name).is_file():
            result["steps"][key] = {"skipped": True, "reason": f"no_{md_name}"}
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
                    "reason": "b17_not_accessible",
                    "detail": (b17_check.stdout or b17_check.stderr)[-800:],
                }
                result["status"] = "failed"
                return result
        if key == "tenchat":
            ten_check = subprocess.run(
                [sys.executable, str(SCRIPTS / "check-tenchat-access.py")],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            if ten_check.returncode != 0:
                result["steps"][key] = {
                    "skipped": True,
                    "reason": "tenchat_not_ready",
                    "detail": (ten_check.stdout or ten_check.stderr)[-800:],
                }
                result["status"] = "failed"
                return result
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
        "posts-emdr-memory/profile/telegram-posts-registry.md",
        "posts-emdr-memory/topics/short-blog-queue.md",
        "posts-emdr-memory/topics/short-blog-published.md",
    ]
    subprocess.run(["git", "add", *paths], cwd=PROJECT_ROOT, check=False)
    msg = f"browser-worker: published {topic} (tg+b17+tenchat)"
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
    parser = argparse.ArgumentParser(description="Publish deferred Telegram/b17/TenChat from VPS")
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
            "См. posts-emdr-memory/profile/browser-autonomous-vps.md"
        )

    if not args.list and not args.dry_run:
        session_proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "browser_ensure_sessions.py"), "--refresh"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if session_proc.returncode != 0:
            raise SystemExit(
                "Session check failed before publish:\n"
                f"{session_proc.stdout}\n{session_proc.stderr}"
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
