#!/usr/bin/env python3
"""Локальный MSP short-blog — Mac cron 12:00 MSK, без Cloud Agent.

Usage:
  python3 scripts/run-local-publish.py --worker   # внутри vps_publish_guard
  python3 scripts/local-publish-wrapper.sh        # cron entry

Платформы: Макс → TG → FB → VK (Undetectable) → b17 → TenChat.
OK: MCP в Cloud отключён; при наличии ok.env.local — record вручную или доработка позже.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, PROJECT_ROOT, materialize_env_files
from publish_idempotency import (
    b17_already_saved,
    facebook_already_published,
    max_already_published,
    telegram_already_published,
    telegram_cover_ok,
    tenchat_already_published,
    vk_location_published,
)

SCRIPTS = PROJECT_ROOT / "scripts"
CONTENT_FILES = (
    "max-post.md",
    "cover-prompt.txt",
    "telegram-post.md",
    "vk-profile-post.md",
    "vk-group-post.md",
    "facebook-post.md",
    "ok-post.md",
    "b17-blog-post.md",
    "tenchat-post.md",
    "grsai-content-log.json",
)


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemExit(
            f"BLOCKER ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{(proc.stdout or '')[-2500:]}\nstderr:\n{(proc.stderr or '')[-2500:]}"
        )
    return proc


def _json_out(proc: subprocess.CompletedProcess) -> dict:
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"raw": (proc.stdout or "")[-800:]}


def intake_topic() -> str:
    proc = _run([sys.executable, str(SCRIPTS / "next-short-blog-topic.py"), "--sync", "--json"])
    data = _json_out(proc)
    tid = data.get("topic_id")
    if not tid:
        raise SystemExit(json.dumps({"status": "queue_empty", **data}, ensure_ascii=False))
    return tid


def ensure_content(topic: str) -> dict:
    topic_dir = MEMORY / "output" / topic
    missing = [f for f in CONTENT_FILES if not (topic_dir / f).is_file()]
    if not missing:
        return {"skipped": True}
    _run([sys.executable, str(SCRIPTS / "grsai-generate-topic.py"), "--topic", topic])
    still = [f for f in CONTENT_FILES if not (topic_dir / f).is_file()]
    if still:
        raise SystemExit(f"BLOCKER: после grsai нет: {still}")
    return {"generated": True, "missing_before": missing}


def ensure_cover(topic: str) -> None:
    cover = MEMORY / "output" / topic / "cover.png"
    if cover.is_file():
        return
    _run([sys.executable, str(SCRIPTS / "publish-topic.py"), "--topic", topic, "--skip-browser"])


def publish_all(topic: str) -> dict:
    steps: dict = {}

    if not max_already_published(topic):
        steps["max"] = _json_out(
            _run([sys.executable, str(SCRIPTS / "send-max-draft.py"), "--topic", topic, "--publish"])
        )
    else:
        steps["max"] = {"skipped": True}

    _run(
        [
            sys.executable,
            str(SCRIPTS / "send-vk-post.py"),
            "--topic",
            topic,
            "--upload-cover",
        ]
    )
    steps["vk_upload"] = {"ok": True}

    if not (telegram_already_published(topic) and telegram_cover_ok(topic)):
        steps["telegram"] = _json_out(
            _run(
                [
                    sys.executable,
                    str(SCRIPTS / "send-telegram-post.py"),
                    "--topic",
                    topic,
                    "--publish",
                ]
            )
        )
    else:
        steps["telegram"] = {"skipped": True}

    if not facebook_already_published(topic):
        steps["facebook"] = _json_out(
            _run([sys.executable, str(SCRIPTS / "publish-zernio-post.py"), "--topic", topic])
        )
    else:
        steps["facebook"] = {"skipped": True}

    for loc, extra in (("personal", []), ("group", ["--from-group"])):
        if vk_location_published(topic, loc):
            steps[f"vk_{loc}"] = {"skipped": True}
            continue
        cmd = [
            sys.executable,
            str(SCRIPTS / "publish-vk-browser.py"),
            "--topic",
            topic,
            "--location",
            loc,
            "--submit",
            *extra,
        ]
        steps[f"vk_{loc}"] = _json_out(_run(cmd))

    if not b17_already_saved(topic):
        steps["b17"] = _json_out(
            _run(
                [
                    sys.executable,
                    str(SCRIPTS / "publish-b17-blog.py"),
                    "--topic",
                    topic,
                    "--submit",
                ]
            )
        )
    else:
        steps["b17"] = {"skipped": True}

    if (MEMORY / "output" / topic / "tenchat-post.md").is_file():
        if not tenchat_already_published(topic):
            steps["tenchat"] = _json_out(
                _run(
                    [
                        sys.executable,
                        str(SCRIPTS / "publish-tenchat-post.py"),
                        "--topic",
                        topic,
                        "--submit",
                    ]
                )
            )
        else:
            steps["tenchat"] = {"skipped": True}

    return steps


def finish(topic: str) -> dict:
    close = _run([sys.executable, str(SCRIPTS / "close-cloud-publish.py"), "--topic", topic])
    verify = _run(
        [sys.executable, str(SCRIPTS / "verify-publish-run.py"), "--topic", topic, "--write", "--json"]
    )
    report = _json_out(verify)
    subprocess.run(
        [sys.executable, str(SCRIPTS / "send-max-publish-report.py"), "--topic", topic],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    add = subprocess.run(
        [
            "git",
            "add",
            f"posts-emdr-memory/output/{topic}/",
            "posts-emdr-memory/profile/*-posts-registry.md",
            "posts-emdr-memory/topics/short-blog-published.md",
            ".cursor/posts-emdr-handoff.md",
            "posts-emdr-memory/b17-tenchat-pending-queue.md",
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    git = {"git_add": add.returncode}
    st = subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    if (st.stdout or "").strip():
        subprocess.run(["git", "commit", "-m", f"publish(local): {topic}"], cwd=PROJECT_ROOT, check=False)
        push = subprocess.run(["git", "push", "origin", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True)
        git["push"] = push.returncode
    return {"close": _json_out(close), "verify": report, "git": git}


def worker() -> None:
    os.environ.setdefault("BROWSER_BACKEND", "undetectable")
    materialize_env_files()
    subprocess.run(["git", "pull", "--ff-only", "origin", "main"], cwd=PROJECT_ROOT, check=False)

    topic = intake_topic()
    already = subprocess.run(
        [sys.executable, str(SCRIPTS / "is-topic-published.py"), "--topic", topic, "--json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if already.returncode == 0:
        print(json.dumps({"status": "already_published", "topic": topic}, ensure_ascii=False))
        return

    content = ensure_content(topic)
    ensure_cover(topic)
    steps = publish_all(topic)
    result = finish(topic)
    print(
        json.dumps(
            {"status": "finished", "topic": topic, "content": content, "steps": steps, "finish": result},
            ensure_ascii=False,
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Local MSP publish (Mac cron)")
    parser.add_argument("--worker", action="store_true", help="Run full pipeline (inside flock)")
    args = parser.parse_args()
    if not args.worker:
        raise SystemExit("Use scripts/local-publish-wrapper.sh or --worker inside guard")
    worker()


if __name__ == "__main__":
    main()
