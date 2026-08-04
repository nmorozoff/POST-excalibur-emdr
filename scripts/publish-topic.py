#!/usr/bin/env python3
"""Full publish pipeline — Cloud Agent safe (no MCP).

Usage:
  python3 scripts/publish-topic.py --topic sb-03-body-before-mind
  python3 scripts/publish-topic.py --topic sb-03-body-before-mind --skip-cover
  python3 scripts/publish-topic.py --topic sb-03-body-before-mind --dry-run

Steps:
  1. materialize_cloud_env (from Cursor Secrets)
  2. cloud_preflight
  3. kie cover (if missing) — gpt-image-2 via Kie.ai 5:4 1K
  4. Max → VK (FTP + MCP handoff) → Facebook
  5. Telegram + b17 → VPS (ASocks / Playwright), не Cloud
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_backend import browser_ready
from posts_emdr_env import (
    PROJECT_ROOT,
    has_vk_access_token,
    materialize_env_files,
    reference_image_path,
    vk_group_id,
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
    ref = reference_image_path(topic)
    if not ref.is_file():
        raise SystemExit(f"Reference image missing: {ref}")
    proc = run(
        [
            sys.executable,
            str(SCRIPTS / "kie-cover.py"),
            "--topic",
            topic,
            "--prompt-file",
            str(prompt),
            "--output",
            str(cover),
            "--task-log",
            str(topic_dir / "kie-cover-log.json"),
        ]
    )
    return {"status": "generated", "path": str(cover), "detail": step_json(proc)}


def _extract_vk_post(md_path: Path) -> str:
    import re

    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"## Текст поста\n\n(.*)", text, re.S)
    if not m:
        raise SystemExit(f"Cannot parse post from {md_path}")
    return m.group(1).strip()


def write_vk_mcp_handoff(topic: str, photo_url: str) -> Path:
    topic_dir = MEMORY / "output" / topic
    handoff = {
        "topic": topic,
        "method": "mcp-kv",
        "tool": "vk_create_post_with_photo",
        "cover_public_url": photo_url,
        "instructions": "posts-emdr-memory/profile/cloud-publish-phases.md",
        "calls": [
            {
                "publish_location": "personal",
                "from_group": False,
                "message": _extract_vk_post(topic_dir / "vk-profile-post.md"),
            },
            {
                "publish_location": "group",
                "from_group": True,
                "group_id": vk_group_id(),
                "message": _extract_vk_post(topic_dir / "vk-group-post.md"),
            },
        ],
    }
    path = topic_dir / "vk-mcp-handoff.json"
    path.write_text(json.dumps(handoff, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def write_browser_local_handoff(topic: str) -> Path:
    topic_dir = MEMORY / "output" / topic
    body = f"""# VPS publish — Telegram + b17

Тема: `{topic}`

Cloud опубликовал Макс / VK(MCP) / Facebook. Осталось на **VPS**:

1. Telegram ×2 (@nmorozova_emdr, @natalia_morozova_psy) — ASocks KZ
2. b17 (Playwright + residential RU)

## Триггер

Webhook (сразу после `git push`):

```bash
curl -fsS -X POST "http://195.209.210.45:8787/publish" \\
  -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \\
  -H "Content-Type: application/json" \\
  -d '{{"topic":"{topic}"}}'
```

Или cron ≤10 мин: `scripts/run-linux-browser-worker.sh`

## Вручную на VPS

```bash
cd ~/POST-excalibur-emdr
source .venv-browser/bin/activate
python3 scripts/asocks_sync_proxy.py --target telegram
python3 scripts/fetch-topic-cover.py --topic {topic}
python3 scripts/publish-browser-deferred.py --topic {topic} --submit --finish --git-push
```

См. `posts-emdr-memory/profile/cloud-publish-phases.md`
"""
    path = topic_dir / "browser-local-handoff.md"
    path.write_text(body, encoding="utf-8")
    return path


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

    if not dry_run:
        dup_check = subprocess.run(
            [sys.executable, str(SCRIPTS / "is-topic-published.py"), "--topic", topic, "--json"],
            capture_output=True,
            text=True,
        )
        if dup_check.returncode == 0:
            dup_data = json.loads(dup_check.stdout or "{}")
            print(json.dumps({
                "topic": topic,
                "status": "skipped",
                "reason": "already_published_end_to_end",
                "check": dup_data,
            }, ensure_ascii=False, indent=2))
            return {"topic": topic, "status": "skipped", "reason": "already_published"}

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

    # Telegram всегда на VPS (api.telegram.org блокируется с Cloud/датацентра).
    log["steps"]["telegram"] = {
        "deferred": True,
        "reason": "vps_asocks_kz",
        "note": "publish-browser-deferred.py на VPS",
    }

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
    vk_prep = json.loads((MEMORY / "output" / topic / "vk-publish-prep.json").read_text(encoding="utf-8"))
    photo_url = vk_prep.get("cover_public_url", "")

    use_vk_api = has_vk_access_token() and not dry_run
    if use_vk_api:
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
        log["steps"]["vk_mode"] = "api"
    elif not dry_run and photo_url:
        handoff_path = write_vk_mcp_handoff(topic, photo_url)
        log["steps"]["vk_mode"] = "mcp_handoff"
        log["steps"]["vk_mcp_handoff"] = str(handoff_path)
        log["mcp_next"] = (
            "Cloud Agent: MCP vk_create_post_with_photo ×2 по vk-mcp-handoff.json, "
            "затем send-vk-post.py --delete-cover"
        )
    else:
        log["steps"]["vk_mode"] = "dry_run_or_no_cover"

    log["steps"]["facebook"] = step_json(
        run(
            [
                sys.executable,
                str(SCRIPTS / "publish-zernio-post.py"),
                "--topic",
                topic,
                *(["--dry-run"] if dry_run else []),
            ],
            check=True,
        )
    )

    browser_ok = browser_ready() and not skip_browser
    log["steps"]["browser_platforms"] = {"ready": browser_ok, "skipped": not browser_ok}
    if browser_ok and not dry_run:
        submit = ["--submit"] if submit_browser else []
        log["steps"]["b17"] = step_json(
            run([sys.executable, str(SCRIPTS / "publish-b17-blog.py"), "--topic", topic, *submit])
        )

    deferred: list[str] = ["telegram"]
    if not browser_ok:
        deferred.append("b17")
    if not dry_run:
        log["steps"]["browser_local_handoff"] = str(write_browser_local_handoff(topic))
    if log.get("steps", {}).get("vk_mode") == "mcp_handoff":
        deferred.append("vk_mcp")

    if not dry_run and browser_ok and "telegram" not in deferred:
        log["status"] = "published_all"
    elif not dry_run:
        log["status"] = "published_scripts_partial"
        log["deferred"] = deferred
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
    parser.add_argument("--submit", action="store_true", help="Auto-click Save on b17")
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
