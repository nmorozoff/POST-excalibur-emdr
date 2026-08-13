#!/usr/bin/env python3
"""VPS publish guard: flock + durable TG markers outside git.

Prevents duplicate Telegram posts when concurrent webhook/cron runs
`git stash` / `git reset --hard` and wipe uncommitted `telegram-publish-log.json`.

Usage:
  # Hold repo lock, sync main, then run worker (webhook / cron):
  python3 scripts/vps_publish_guard.py run -- \\
    python3 scripts/publish-browser-deferred.py --topic sb-14 --submit --finish --git-push

  python3 scripts/vps_publish_guard.py status
  python3 scripts/vps_publish_guard.py try-lock   # exit 0 free / 3 busy
"""

from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

SCRIPTS = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPTS.parent
sys.path.insert(0, str(SCRIPTS))

from posts_emdr_env import MEMORY, PROJECT_ROOT as _PR  # noqa: E402

assert PROJECT_ROOT == _PR

STATE_DIR = Path(
    os.environ.get(
        "POSTS_EMDR_STATE_DIR",
        str(Path(os.environ.get("TMPDIR", "/tmp")) / "posts-emdr-state"),
    )
).expanduser()
LOCK_FILE = STATE_DIR / "repo-publish.lock"


def state_dir() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def platform_marker_path(topic: str, platform: str) -> Path:
    safe_topic = topic.replace("/", "_").replace("..", "_")
    return state_dir() / "platforms" / safe_topic / f"{platform}.json"


def read_platform_marker(topic: str, platform: str) -> dict | None:
    path = platform_marker_path(topic, platform)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def write_platform_marker(topic: str, platform: str, payload: dict) -> Path:
    path = platform_marker_path(topic, platform)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = {
        **payload,
        "topic": topic,
        "platform": platform,
        "marked_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    path.write_text(json.dumps(body, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def telegram_marker_done(topic: str) -> bool:
    data = read_platform_marker(topic, "telegram")
    if not data:
        return False
    return data.get("status") in {"sent", "published"}


def mark_telegram_sent(topic: str, log: dict) -> Path:
    return write_platform_marker(
        topic,
        "telegram",
        {
            "status": log.get("status") or "sent",
            "channels": log.get("channels"),
            "delivery": log.get("delivery"),
            "source": "send-telegram-post",
        },
    )


def restore_telegram_log_from_marker(topic_dir: Path, topic: str) -> bool:
    """If git reset wiped telegram-publish-log.json, restore from durable marker."""
    log_path = topic_dir / "telegram-publish-log.json"
    if log_path.is_file():
        return False
    data = read_platform_marker(topic, "telegram")
    if not data or data.get("status") not in {"sent", "published"}:
        return False
    restored = {
        "status": data.get("status") or "sent",
        "mode": "publish",
        "delivery": data.get("delivery") or "link_preview_single_message",
        "channels": data.get("channels") or [],
        "restored_from": "posts-emdr-state",
    }
    topic_dir.mkdir(parents=True, exist_ok=True)
    log_path.write_text(json.dumps(restored, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return True


def lock_held() -> bool:
    state_dir()
    fd = os.open(str(LOCK_FILE), os.O_RDWR | os.O_CREAT, 0o644)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        fcntl.flock(fd, fcntl.LOCK_UN)
        return False
    finally:
        os.close(fd)


@contextmanager
def acquire_repo_lock(*, blocking: bool = False) -> Iterator[int]:
    """Exclusive flock for the whole VPS publish (git pull + TG + b17)."""
    state_dir()
    fd = os.open(str(LOCK_FILE), os.O_RDWR | os.O_CREAT, 0o644)
    flags = fcntl.LOCK_EX if blocking else (fcntl.LOCK_EX | fcntl.LOCK_NB)
    try:
        fcntl.flock(fd, flags)
    except BlockingIOError:
        os.close(fd)
        raise
    try:
        os.write(fd, f"pid={os.getpid()} ts={time.time()}\n".encode())
        try:
            os.ftruncate(fd, os.lseek(fd, 0, os.SEEK_CUR))
        except OSError:
            pass
        yield fd
    finally:
        try:
            fcntl.flock(fd, fcntl.LOCK_UN)
        finally:
            os.close(fd)


def git_pull_main() -> dict:
    """Fetch origin/main; stash dirty tree; reset --hard FETCH_HEAD."""
    env_file = MEMORY / "github.env.local"
    env = os.environ.copy()
    if env_file.is_file():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    token = env.get("GITHUB_TOKEN", "").strip()
    if not (PROJECT_ROOT / ".git").is_dir():
        return {"ok": False, "reason": "no_git"}

    if token:
        remote_url = f"https://{token}@github.com/nmorozoff/POST-excalibur-emdr.git"
        subprocess.run(
            ["git", "remote", "set-url", "origin", remote_url],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            env=env,
        )

    stash = subprocess.run(
        ["git", "stash", "push", "-u", "-m", "vps-publish-guard-auto"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    fetch = subprocess.run(
        ["git", "fetch", "origin", "main"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    if fetch.returncode != 0:
        return {
            "ok": False,
            "stash_exit": stash.returncode,
            "stdout_tail": (fetch.stdout or "")[-500:],
            "stderr_tail": (fetch.stderr or "")[-500:],
        }
    reset = subprocess.run(
        ["git", "reset", "--hard", "FETCH_HEAD"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        env=env,
    )
    return {
        "ok": reset.returncode == 0,
        "mode": "fetch_reset_hard",
        "stash_exit": stash.returncode,
        "stdout_tail": (reset.stdout or "")[-500:],
        "stderr_tail": (reset.stderr or "")[-500:],
    }


def run_under_lock(argv: list[str], *, git_pull: bool = True) -> int:
    try:
        with acquire_repo_lock(blocking=False):
            pull_info = git_pull_main() if git_pull else {"ok": True, "skipped": True}
            print(json.dumps({"vps_publish_guard": "acquired", "git_pull": pull_info}, ensure_ascii=False), flush=True)
            if git_pull and not pull_info.get("ok"):
                print(json.dumps({"error": "git_pull_failed", "git_pull": pull_info}, ensure_ascii=False), flush=True)
                return 2
            child_env = os.environ.copy()
            child_env["POSTS_EMDR_PUBLISH_LOCKED"] = "1"
            proc = subprocess.run(argv, cwd=PROJECT_ROOT, env=child_env)
            return int(proc.returncode)
    except BlockingIOError:
        print(
            json.dumps(
                {
                    "ok": False,
                    "accepted": False,
                    "status": "busy",
                    "error": "publish_lock_held",
                    "lock_file": str(LOCK_FILE),
                    "note": "another webhook/cron publish is running; not starting a second TG/b17 job",
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        return 3


def main() -> None:
    parser = argparse.ArgumentParser(description="VPS publish flock + durable state")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_run = sub.add_parser("run", help="Acquire lock, optional git pull, run command")
    p_run.add_argument("--no-git-pull", action="store_true")
    p_run.add_argument("command", nargs=argparse.REMAINDER, help="Command after --")

    sub.add_parser("status", help="Show lock + state dir")
    sub.add_parser("try-lock", help="Exit 0 if free, 3 if busy")

    args = parser.parse_args()

    if args.cmd == "status":
        print(
            json.dumps(
                {
                    "state_dir": str(state_dir()),
                    "lock_file": str(LOCK_FILE),
                    "lock_held": lock_held(),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    if args.cmd == "try-lock":
        sys.exit(3 if lock_held() else 0)

    if args.cmd == "run":
        cmd = list(args.command)
        if cmd and cmd[0] == "--":
            cmd = cmd[1:]
        if not cmd:
            raise SystemExit("vps_publish_guard.py run -- <command...>")
        sys.exit(run_under_lock(cmd, git_pull=not args.no_git_pull))


if __name__ == "__main__":
    main()
