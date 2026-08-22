#!/usr/bin/env python3
"""VPS worker: Telegram + b17 for MSP short-blog topics deferred from cloud.

TenChat вне scope MSP short-blog — worker и --finish не блокируются на TenChat.

Linux VPS (Playwright) — cron:

  scripts/run-linux-browser-worker.sh

Или вручную / webhook:

  python3 scripts/fetch-topic-cover.py --all-pending
  python3 scripts/publish-browser-deferred.py --submit --finish --git-push
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_backend import browser_ready
from browser_worker_finish import finish_topic
from posts_emdr_env import MEMORY, PROJECT_ROOT, load_env, materialize_vps_runtime_env
from vps_publish_guard import (
    mark_telegram_sent,
    restore_telegram_log_from_marker,
    telegram_marker_done,
)

SCRIPTS = PROJECT_ROOT / "scripts"


def _msp_deferred_complete(topic_dir: Path) -> bool:
    # Main short-blog completion only requires Telegram. b17/TenChat are handled
    # by the manual repair queue: b17-tenchat-pending-queue.md
    return _platform_done(topic_dir, "telegram")


def _log_status(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data.get("status")
    except (json.JSONDecodeError, OSError):
        return None


def _telegram_done(topic_dir: Path) -> bool:
    topic = topic_dir.name
    # Durable marker survives git reset --hard that wiped the repo log.
    if telegram_marker_done(topic):
        restore_telegram_log_from_marker(topic_dir, topic)
        return True
    status = _log_status(topic_dir / "telegram-publish-log.json")
    return status in {"sent", "published"}


def _platform_done(topic_dir: Path, key: str) -> bool:
    if key == "telegram":
        return _telegram_done(topic_dir)
    return _log_status(topic_dir / f"{key}-publish-log.json") == "published"


def _worker_finished(topic_dir: Path) -> bool:
    finish_path = topic_dir / "browser-worker-finish.json"
    if not finish_path.is_file():
        return False
    try:
        data = json.loads(finish_path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return False
    return data.get("status") == "browser_worker_finished"


def _close_stale_handoff(topic_dir: Path) -> None:
    """Если finish уже был, но handoff не переименован — закрыть, чтобы cron не крутил тему."""
    handoff = topic_dir / "browser-local-handoff.md"
    done = topic_dir / "browser-local-handoff.done.md"
    if not handoff.is_file() or done.is_file():
        return
    if _worker_finished(topic_dir) or _msp_deferred_complete(topic_dir):
        handoff.rename(done)


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
        _close_stale_handoff(topic_dir)
        handoff = topic_dir / "browser-local-handoff.md"
        done = topic_dir / "browser-local-handoff.done.md"
        # Need handoff OR explicit --topic, plus drafts
        has_drafts = (topic_dir / "telegram-post.md").is_file() or (
            topic_dir / "b17-blog-post.md"
        ).is_file()
        if _worker_finished(topic_dir) and _msp_deferred_complete(topic_dir):
            continue
        if topic:
            if has_drafts and not (_msp_deferred_complete(topic_dir) and done.is_file()):
                topics.append(tid)
            continue
        if not handoff.is_file() and not done.is_file():
            continue
        if done.is_file() and _msp_deferred_complete(topic_dir):
            continue
        if not has_drafts:
            continue
        topics.append(tid)
    return topics


def needs_browser_for_topics(topics: list[str]) -> bool:
    """Telegram Bot API does not need Playwright — only b17 does."""
    for tid in topics:
        topic_dir = MEMORY / "output" / tid
        if (topic_dir / "b17-blog-post.md").is_file() and not _platform_done(topic_dir, "b17"):
            return True
    return False


def write_worker_run_summary(topic: str, report: dict) -> None:
    path = MEMORY / "output" / topic / "vps-worker-last-run.json"
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def sync_telegram_proxy(*, exclude_port_ids: set[str] | None = None) -> dict:
    """ASocks KZ → TELEGRAM_PROXY_* перед Bot API, с curl preflight и ротацией KZ."""
    try:
        from asocks_sync_proxy import sync_telegram_with_preflight

        data = sync_telegram_with_preflight(write=True, exclude_port_ids=exclude_port_ids)
        return {
            "exit_code": 0,
            "stdout_tail": json.dumps(data, ensure_ascii=False)[-800:],
            "stderr_tail": "",
            "ok": bool(data.get("preflight_ok")),
            "preflight_ok": bool(data.get("preflight_ok")),
            "asocks_port_name": data.get("asocks_port_name"),
            "attempts": data.get("attempts"),
        }
    except SystemExit as exc:
        out = {
            "exit_code": 1,
            "stderr_tail": str(exc),
            "ok": False,
        }
        try:
            env = load_env("browser.env.local")
            if env.get("TELEGRAM_PROXY_SERVER"):
                out["fallback"] = "existing_TELEGRAM_PROXY_SERVER"
                out["ok"] = True
                out["preflight_ok"] = False
                out["warning"] = "sync_failed_continue_with_existing_proxy_or_direct"
        except SystemExit:
            pass
        return out
    except Exception as exc:  # noqa: BLE001 — surface sync errors without killing worker
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
            "sync_error": str(exc),
        }
        if proc.returncode != 0:
            try:
                env = load_env("browser.env.local")
                if env.get("TELEGRAM_PROXY_SERVER"):
                    out["fallback"] = "existing_TELEGRAM_PROXY_SERVER"
                    out["ok"] = True
                    out["preflight_ok"] = False
                    return out
            except SystemExit:
                pass
            out["ok"] = False
            return out
        out["ok"] = True
        out["preflight_ok"] = False
        return out


def _current_telegram_port_id() -> str:
    try:
        env = load_env("browser.env.local")
        return env.get("TELEGRAM_ASOCKS_PORT_ID", "").strip()
    except SystemExit:
        return ""


def run_send_telegram(topic: str, *, skip_proxy: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    if skip_proxy:
        env["TELEGRAM_SKIP_PROXY"] = "1"
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "send-telegram-post.py"),
            "--topic",
            topic,
            "--publish",
            "--refresh-cover-url",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )


def publish_telegram_with_retries(topic: str, *, max_attempts: int = 3) -> dict:
    """Telegram publish with proxy resync between attempts on transient proxy errors."""
    step: dict = {"attempts": []}
    last_proc: subprocess.CompletedProcess[str] | None = None
    failed_port_ids: set[str] = set()

    for attempt in range(1, max_attempts + 1):
        if attempt > 1:
            step["attempts"][-1]["retry_after_sec"] = 20
            time.sleep(20)
            step["telegram_proxy_retry"] = sync_telegram_proxy(exclude_port_ids=failed_port_ids)
        proc = run_send_telegram(topic)
        last_proc = proc
        port_id = _current_telegram_port_id()
        attempt_info = {
            "attempt": attempt,
            "exit_code": proc.returncode,
            "asocks_port_id": port_id or None,
            "stderr_tail": (proc.stderr or "")[-500:],
        }
        step["attempts"].append(attempt_info)
        if proc.returncode == 0:
            break
        if port_id:
            failed_port_ids.add(port_id)
        err = (proc.stderr or proc.stdout or "").lower()
        if "timed out" not in err and "unexpected_eof" not in err and "urlerror" not in err:
            break

    if last_proc is not None and last_proc.returncode != 0:
        step["attempts"][-1]["retry_after_sec"] = 15
        time.sleep(15)
        step["direct_fallback"] = True
        last_proc = run_send_telegram(topic, skip_proxy=True)
        step["attempts"].append(
            {
                "attempt": "direct_fallback",
                "exit_code": last_proc.returncode,
                "skip_proxy": True,
                "stderr_tail": (last_proc.stderr or "")[-500:],
            }
        )

    assert last_proc is not None
    step.update(
        {
            "exit_code": last_proc.returncode,
            "stdout_tail": last_proc.stdout[-2000:] if last_proc.stdout else "",
            "stderr_tail": last_proc.stderr[-1000:] if last_proc.stderr else "",
        }
    )
    if last_proc.returncode != 0:
        step["failed"] = True
    return step


def ensure_site_cover(topic: str) -> dict:
    """FTP upload cover → morozovanatalia.ru/social-covers/{topic}.jpg (b17 TinyMCE HTTPS)."""
    topic_dir = MEMORY / "output" / topic
    cover = topic_dir / "cover.png"
    if not cover.is_file():
        return {"ok": False, "reason": "no_cover.png"}
    proc = subprocess.run(
        [
            sys.executable,
            str(SCRIPTS / "send-vk-post.py"),
            "--topic",
            topic,
            "--upload-cover",
        ],
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
        out["ok"] = False
        return out
    try:
        data = json.loads(proc.stdout or "{}")
        out["cover_public_url"] = data.get("cover_public_url")
        out["ok"] = bool(out.get("cover_public_url"))
    except json.JSONDecodeError:
        out["ok"] = False
    return out


def run_publish(topic: str, *, submit: bool) -> dict:
    submit_args = ["--submit"] if submit else []
    result: dict = {"topic": topic, "steps": {}}
    topic_dir = MEMORY / "output" / topic

    # 0) Site cover for b17 HTTPS + Telegram link_preview (VPS FTP usually works when cloud DC FTP fails)
    result["steps"]["site_cover"] = ensure_site_cover(topic)
    if not result["steps"]["site_cover"].get("ok"):
        # Non-fatal for TenChat (local file attach); b17 may fail verify — surface in log
        result["steps"]["site_cover"]["warning"] = "upload_failed_continue"

    # 1) Telegram via ASocks KZ
    if not _telegram_done(topic_dir):
        if not (topic_dir / "telegram-post.md").is_file():
            result["steps"]["telegram"] = {"skipped": True, "reason": "no_telegram-post.md"}
        else:
            result["steps"]["telegram_proxy"] = sync_telegram_proxy()
            if not result["steps"]["telegram_proxy"].get("ok"):
                result["steps"]["telegram_proxy"]["warning"] = (
                    "sync_failed_continue_with_existing_proxy_or_direct"
                )
            elif not result["steps"]["telegram_proxy"].get("preflight_ok"):
                result["steps"]["telegram_proxy"]["warning"] = (
                    "preflight_failed_continue_with_send_retries"
                )
            result["steps"]["telegram"] = publish_telegram_with_retries(topic)
            if result["steps"]["telegram"].get("failed"):
                result["telegram_failed"] = True
            else:
                # Durable marker + immediate push so concurrent reset cannot re-send TG.
                tg_log_path = topic_dir / "telegram-publish-log.json"
                if tg_log_path.is_file():
                    try:
                        tg_log = json.loads(tg_log_path.read_text(encoding="utf-8"))
                        marker = mark_telegram_sent(topic, tg_log)
                        result["steps"]["telegram"]["durable_marker"] = str(marker)
                    except (json.JSONDecodeError, OSError) as exc:
                        result["steps"]["telegram"]["durable_marker_error"] = str(exc)
                result["steps"]["telegram_git_push"] = git_push_logs(topic)
    else:
        result["steps"]["telegram"] = {"skipped": True, "reason": "already_published"}

    result["steps"]["tenchat"] = {"skipped": True, "reason": "out_of_msp_short_blog_pipeline"}

    # 2) b17 — create draft if possible, but do NOT block the main short-blog flow.
    b17_md = topic_dir / "b17-blog-post.md"
    if b17_md.is_file() and not _platform_done(topic_dir, "b17"):
        b17_check = subprocess.run(
            [sys.executable, str(SCRIPTS / "check-b17-ip-access.py")],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if b17_check.returncode != 0:
            result["steps"]["b17"] = {
                "skipped": True,
                "reason": "b17_not_accessible",
                "detail": (b17_check.stdout or b17_check.stderr)[-800:],
            }
            result["b17_blocked"] = True
        else:
            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "publish-b17-blog.py"), "--topic", topic, *submit_args],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            result["steps"]["b17"] = {
                "exit_code": proc.returncode,
                "stdout_tail": proc.stdout[-2000:] if proc.stdout else "",
                "stderr_tail": proc.stderr[-1000:] if proc.stderr else "",
            }
            if proc.returncode != 0:
                result["b17_draft"] = True

    # Always record b17/TenChat in the pending repair queue so manual repair can retry.
    if (topic_dir / "b17-blog-post.md").is_file() and not _platform_done(topic_dir, "b17"):
        _ensure_b17_tenchat_pending(topic, "b17")
    if (topic_dir / "tenchat-post.md").is_file() and not _platform_done(topic_dir, "tenchat"):
        _ensure_b17_tenchat_pending(topic, "tenchat")

    if result.get("telegram_failed") and not _telegram_done(topic_dir):
        result["status"] = "failed"
    elif result.get("status") != "failed":
        result["status"] = "ok"
    return result


def _ensure_b17_tenchat_pending(topic: str, platform: str) -> None:
    """Add a topic to the manual repair queue if not already queued."""
    from datetime import datetime

    pending_path = MEMORY / "b17-tenchat-pending-queue.md"
    if not pending_path.is_file():
        pending_path.write_text(
            "# b17 + TenChat — pending repair queue\n\n"
            "Ручная автоматизация. Запускать только по вашему ОК.\n\n"
            "| topic_id | platform | status | created_at | last_retry |\n"
            "|----------|----------|--------|------------|------------|\n",
            encoding="utf-8",
        )
    text = pending_path.read_text(encoding="utf-8")
    if f"| `{topic}` | `{platform}` |" in text:
        return
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = f"| `{topic}` | `{platform}` | `pending` | {now} | - |"
    lines = text.splitlines()
    # Insert after the second table header line
    insert_at = 0
    for i, line_ in enumerate(lines):
        if line_.strip().startswith("|----------|") and i + 1 < len(lines):
            insert_at = i + 1
            break
    lines.insert(insert_at, line)
    pending_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def git_push_logs(topic: str) -> dict:
    """Push output/{topic}/ logs so next run / cloud Otchetik sees them."""
    path = f"posts-emdr-memory/output/{topic}/"
    subprocess.run(["git", "add", path], cwd=PROJECT_ROOT, check=False)
    msg = f"browser-worker: logs {topic}"
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
    msg = f"browser-worker: published {topic} (tg+b17)"
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
    parser = argparse.ArgumentParser(description="Publish deferred Telegram/b17 from VPS (MSP short-blog)")
    parser.add_argument("--topic", help="Single topic id (default: all pending)")
    parser.add_argument("--submit", action="store_true", help="Auto-click Save/Publish")
    parser.add_argument("--finish", action="store_true", help="Registries + queue after publish")
    parser.add_argument("--git-push", action="store_true", help="git commit+push after --finish")
    parser.add_argument("--list", action="store_true", help="List pending topics only")
    parser.add_argument("--dry-run", action="store_true", help="Do not call publish scripts")
    args = parser.parse_args()

    vps_env = materialize_vps_runtime_env()
    print(json.dumps({"vps_env": vps_env}, ensure_ascii=False), flush=True)

    try:
        load_env("browser.env.local")
    except SystemExit:
        pass

    pending = pending_topics(topic=args.topic)

    if args.list:
        print(json.dumps({"pending": pending}, ensure_ascii=False, indent=2))
        return

    if not pending:
        print(json.dumps({"pending": [], "status": "nothing_to_do"}, ensure_ascii=False, indent=2))
        return

    browser_required = needs_browser_for_topics(pending)
    if not args.list and not args.dry_run and browser_required and not browser_ready():
        raise SystemExit(
            "Browser backend недоступен (нужен для b17). Linux: BROWSER_BACKEND=playwright + storage state. "
            "См. posts-emdr-memory/profile/browser-autonomous-vps.md"
        )

    if not args.list and not args.dry_run and browser_required:
        session_proc = subprocess.run(
            [sys.executable, str(SCRIPTS / "browser_ensure_sessions.py"), "--refresh"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
        )
        if session_proc.returncode != 0:
            # Do not hard-fail: per-platform checks skip TenChat/b17 individually.
            # Telegram Bot API does not need browser sessions.
            print(
                json.dumps(
                    {
                        "warning": "session_check_failed_continue",
                        "stdout_tail": (session_proc.stdout or "")[-800:],
                        "stderr_tail": (session_proc.stderr or "")[-400:],
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )

    reports = []
    for tid in pending:
        if args.dry_run:
            reports.append({"topic": tid, "status": "dry_run"})
            continue
        report = run_publish(tid, submit=args.submit)
        write_worker_run_summary(tid, report)
        # Check b17 draft/rate-limit state: do not finish, keep topic pending for retry
        b17_log_path = MEMORY / "output" / tid / "b17-publish-log.json"
        b17_draft = False
        if b17_log_path.is_file():
            try:
                b17_data = json.loads(b17_log_path.read_text(encoding="utf-8"))
                b17_draft = b17_data.get("status") == "draft_saved"
                if b17_draft:
                    report["status"] = "draft"
                    report["b17_draft_saved"] = True
            except (json.JSONDecodeError, OSError):
                pass
        if args.git_push:
            # Always push logs so next run / cloud Otchetik sees them (prevent re-publish on git reset)
            report["git_logs"] = git_push_logs(tid)
        if report.get("status") in {"ok", "draft"} and args.finish:
            # Finish the main short-blog topic even if b17 is only a draft.
            # The repair queue handles b17/TenChat separately.
            try:
                report["finish"] = finish_topic(tid, force_b17_optional=True)
            except SystemExit as exc:
                report["finish"] = {"error": str(exc)}
                report["status"] = "finish_failed"
            if args.git_push and report.get("status") in {"ok", "draft"}:
                report["git"] = git_push_changes(tid)
        reports.append(report)

    print(json.dumps({"pending_count": len(pending), "results": reports}, ensure_ascii=False, indent=2))
    failed = [r for r in reports if r.get("status") in {"failed", "finish_failed"}]
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
