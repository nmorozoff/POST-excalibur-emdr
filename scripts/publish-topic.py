#!/usr/bin/env python3
"""Full publish pipeline — Cloud Agent safe (no MCP).

Usage:
  python3 scripts/publish-topic.py --topic sb-03-body-before-mind
  python3 scripts/publish-topic.py --topic sb-03-body-before-mind --skip-cover
  python3 scripts/publish-topic.py --topic sb-03-body-before-mind --dry-run

Steps:
  1. materialize_cloud_env (from Cursor Secrets)
  2. cloud_preflight
  3. runware cover (if missing)
  4. Max → Telegram → VK (FTP + API) → Facebook
  5. b17 + TenChat if Undetectable reachable
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import (
    PROJECT_ROOT,
    materialize_env_files,
    reference_image_path,
    undetectable_reachable,
)
from cloud_preflight import run_preflight

SCRIPTS = PROJECT_ROOT / "scripts"
MEMORY = PROJECT_ROOT / "posts-emdr-memory"


def run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(
        cmd,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if check and proc.returncode != 0:
        raise SystemExit(
            f"Command failed ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout}\nstderr:\n{proc.stderr}"
        )
    return proc


def step_json(proc: subprocess.CompletedProcess) -> dict:
    text = (proc.stdout or "").strip()
    if not text:
        return {"stdout": "", "stderr": proc.stderr}
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"stdout": text, "stderr": proc.stderr}


def ensure_cover(topic: str) -> dict:
    topic_dir = MEMORY / "output" / topic
    cover = topic_dir / "cover.png"
    prompt = topic_dir / "cover-prompt.txt"
    if cover.exists():
        return {"status": "exists", "path": str(cover)}
    if not prompt.exists():
        raise SystemExit(f"Missing {prompt}")
    ref = reference_image_path()
    if not ref.is_file():
        raise SystemExit(f"Reference image missing: {ref}")
    proc = run(
        [
            sys.executable,
            str(SCRIPTS / "runware-cover.py"),
            "--prompt-file",
            str(prompt),
            "--reference",
            str(ref),
            "--output",
            str(cover),
        ]
    )
    return {"status": "generated", "path": str(cover), "detail": step_json(proc)}


def publish_topic(
    topic: str,
    *,
    dry_run: bool = False,
    skip_cover: bool = False,
    skip_browser: bool = False,
    submit_browser: bool = False,
) -> dict:
    materialize_env_files()
    preflight = run_preflight(strict=False)
    if not dry_run and not preflight.get("ready_for_auto_publish"):
        raise SystemExit(
            "Preflight failed — configure Cursor Cloud Secrets. "
            f"See posts-emdr-memory/CLOUD-SETUP.md\n{json.dumps(preflight, ensure_ascii=False, indent=2)}"
        )

    log: dict = {"topic": topic, "dry_run": dry_run, "steps": {}}

    if not skip_cover:
        log["steps"]["cover"] = ensure_cover(topic)

    publish_flag = ["--dry-run"] if dry_run else ["--publish"]

    log["steps"]["max"] = step_json(
        run(
            [sys.executable, str(SCRIPTS / "send-max-draft.py"), "--topic", topic, *publish_flag],
            check=True,
        )
    )

    tg_cmd = [
        sys.executable,
        str(SCRIPTS / "send-telegram-post.py"),
        "--topic",
        topic,
        *publish_flag,
    ]
    log["steps"]["telegram"] = step_json(run(tg_cmd, check=True))

    vk_flags = ["--dry-run"] if dry_run else []
    vk_upload = run(
        [
            sys.executable,
            str(SCRIPTS / "send-vk-post.py"),
            "--topic",
            topic,
            "--upload-cover",
            *vk_flags,
        ],
        check=True,
    )
    log["steps"]["vk_upload"] = step_json(vk_upload)

    if not dry_run:
        log["steps"]["vk_profile"] = step_json(
            run(
                [
                    sys.executable,
                    str(SCRIPTS / "vk_publish.py"),
                    "--topic",
                    topic,
                    "--location",
                    "personal",
                ]
            )
        )
        log["steps"]["vk_group"] = step_json(
            run(
                [
                    sys.executable,
                    str(SCRIPTS / "vk_publish.py"),
                    "--topic",
                    topic,
                    "--location",
                    "group",
                    "--from-group",
                ]
            )
        )
        run([sys.executable, str(SCRIPTS / "send-vk-post.py"), "--topic", topic, "--delete-cover"])

    log["steps"]["facebook"] = step_json(
        run(
            [
                sys.executable,
                str(SCRIPTS / "publish-zernio-post.py"),
                "--topic",
                topic,
                *publish_flag,
            ],
            check=True,
        )
    )

    undetectable_ok = undetectable_reachable() and not skip_browser
    log["steps"]["browser_platforms"] = {"undetectable": undetectable_ok, "skipped": not undetectable_ok}
    if undetectable_ok and not dry_run:
        submit = ["--submit"] if submit_browser else []
        log["steps"]["b17"] = step_json(
            run([sys.executable, str(SCRIPTS / "publish-b17-blog.py"), "--topic", topic, *submit])
        )
        log["steps"]["tenchat"] = step_json(
            run([sys.executable, str(SCRIPTS / "publish-tenchat-post.py"), "--topic", topic, *submit])
        )

    if not dry_run and undetectable_ok:
        log["status"] = "published_all"
    elif not dry_run:
        log["status"] = "published_auto_platforms"
        log["deferred"] = ["b17", "tenchat"]
    else:
        log["status"] = "dry_run"

    topic_dir = MEMORY / "output" / topic
    (topic_dir / "publish-log.md").write_text(
        _publish_log_md(topic, log),
        encoding="utf-8",
    )
    (topic_dir / "publish-pipeline-log.json").write_text(
        json.dumps(log, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return log


def _publish_log_md(topic: str, log: dict) -> str:
    today = date.today().isoformat()
    lines = [
        f"# Publish log — {topic}",
        "",
        f"**Date:** {today}",
        f"**Status:** {log.get('status')}",
        "",
        "## Steps",
        "",
    ]
    for name, detail in log.get("steps", {}).items():
        lines.append(f"### {name}")
        lines.append("```json")
        lines.append(json.dumps(detail, ensure_ascii=False, indent=2)[:2000])
        lines.append("```")
        lines.append("")
    if log.get("deferred"):
        lines.append(f"**Deferred (no Undetectable):** {', '.join(log['deferred'])}")
    return "\n".join(lines) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-cover", action="store_true")
    parser.add_argument("--skip-browser", action="store_true")
    parser.add_argument("--submit", action="store_true", help="Auto-click Save/Publish on b17/TenChat")
    args = parser.parse_args()

    result = publish_topic(
        args.topic,
        dry_run=args.dry_run,
        skip_cover=args.skip_cover,
        skip_browser=args.skip_browser,
        submit_browser=args.submit,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
