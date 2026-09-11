#!/usr/bin/env python3
"""Единая точка Cloud-прогона MSP short-blog — меньше шансов, что агент «забудет» шаг.

Usage:
  python3 scripts/run-cloud-publish.py --sync          # intake → контент → скрипты → TG
  # агент: только MCP по cloud-mcp-bundle.json + record-* из bundle
  python3 scripts/run-cloud-publish.py --topic ID --finish   # close + отчёт + git push

Exit:
  0 — ok / awaiting_mcp / finished
  1 — queue empty / already published
  2 — blocker (preflight, verify fail, incidents)
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, PROJECT_ROOT

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
    "grsai-content-log.json",
)


def _run(cmd: list[str], *, check: bool = True) -> subprocess.CompletedProcess:
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise SystemExit(
            f"BLOCKER ({proc.returncode}): {' '.join(cmd)}\n"
            f"stdout:\n{proc.stdout[-2000:]}\nstderr:\n{proc.stderr[-2000:]}"
        )
    return proc


def _json_out(proc: subprocess.CompletedProcess) -> dict:
    try:
        return json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return {"raw_stdout": (proc.stdout or "")[-500:], "stderr": (proc.stderr or "")[-500:]}


def _handoff_topic_id() -> str | None:
    handoff = PROJECT_ROOT / ".cursor/posts-emdr-handoff.md"
    if not handoff.is_file():
        return None
    for line in handoff.read_text(encoding="utf-8").splitlines():
        if line.startswith("topic_id:"):
            return line.split(":", 1)[1].strip() or None
    return None


def _topic_awaiting_mcp(topic: str) -> bool:
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS / "is-topic-published.py"), "--topic", topic, "--json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        return False
    return proc.returncode == 2 and bool(data.get("awaiting_mcp"))


def intake_topic(*, sync: bool) -> dict:
    inc = subprocess.run(
        [sys.executable, str(SCRIPTS / "incident_queue.py"), "--project-root", str(PROJECT_ROOT)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if inc.returncode == 2:
        handoff_topic = _handoff_topic_id()
        if handoff_topic and _topic_awaiting_mcp(handoff_topic):
            return {
                "topic_id": handoff_topic,
                "continuing": "awaiting_mcp",
                "note": "open incidents, но тема в awaiting_mcp — только MCP VK, без publish-topic",
            }
        raise SystemExit("BLOCKER: open incidents — Fixic перед прогоном")

    cmd = [sys.executable, str(SCRIPTS / "next-short-blog-topic.py"), "--json"]
    if sync:
        cmd.append("--sync")
    proc = _run(cmd)
    data = _json_out(proc)
    tid = data.get("topic_id")
    if not tid:
        raise SystemExit(json.dumps({"status": "queue_empty", **data}, ensure_ascii=False))
    if data.get("reason") == "already_published_still_in_queue":
        raise SystemExit(json.dumps({"status": "already_published_still_in_queue", **data}, ensure_ascii=False))
    return data


def ensure_content(topic: str) -> dict:
    topic_dir = MEMORY / "output" / topic
    missing = [f for f in CONTENT_FILES if not (topic_dir / f).is_file()]
    if not missing:
        return {"skipped": True, "reason": "content_exists"}
    _run([sys.executable, str(SCRIPTS / "grsai-generate-topic.py"), "--topic", topic])
    still = [f for f in CONTENT_FILES if not (topic_dir / f).is_file()]
    if still:
        raise SystemExit(f"BLOCKER: после grsai нет файлов: {still}")
    return {"generated": True}


def ensure_telegram(topic: str, *, attempts: int = 3) -> dict:
    from publish_idempotency import telegram_already_published

    if telegram_already_published(topic):
        return {"skipped": True, "reason": "already_sent"}

    last_err = ""
    for i in range(attempts):
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
        if proc.returncode == 0:
            return {"status": "published", "attempt": i + 1, "detail": _json_out(proc)}
        last_err = (proc.stderr or proc.stdout or "")[-800:]
        if i + 1 < attempts:
            time.sleep(12)
    raise SystemExit(f"BLOCKER: Telegram после {attempts} попыток:\n{last_err}")


def write_mcp_bundle(topic: str) -> Path:
    topic_dir = MEMORY / "output" / topic
    bundle: dict = {
        "topic": topic,
        "phase": "awaiting_mcp",
        "instructions": "Вызвать MCP строго по calls. После каждого — record_* из record_after.",
        "vk": None,
        "ok": None,
    }
    vk_path = topic_dir / "vk-mcp-handoff.json"
    if vk_path.is_file():
        vk = json.loads(vk_path.read_text(encoding="utf-8"))
        bundle["vk"] = {
            "handoff": str(vk_path),
            "tool": "vk_create_post_with_photo",
            "calls": vk.get("calls") or [],
            "cover_public_url": vk.get("cover_public_url"),
            "record_after": [
                {
                    "script": "record-vk-mcp-publish.py",
                    "location": "personal",
                    "args_template": (
                        f"--topic {topic} --location personal --wall-url <WALL_URL> "
                        "--title <TITLE> --site-url <SITE_URL> --tags <TAGS>"
                    ),
                },
                {
                    "script": "record-vk-mcp-publish.py",
                    "location": "group",
                    "args_template": (
                        f"--topic {topic} --location group --wall-url <WALL_URL> "
                        "--from-group --title <TITLE> --site-url <SITE_URL> --tags <TAGS>"
                    ),
                },
            ],
        }
    ok_path = topic_dir / "ok-mcp-handoff.json"
    if ok_path.is_file():
        ok = json.loads(ok_path.read_text(encoding="utf-8"))
        bundle["ok"] = {
            "handoff": str(ok_path),
            "tool": "ok_create_post_with_photo",
            "text": ok.get("text"),
            "image_url": ok.get("image_url"),
            "gid": ok.get("gid"),
            "onBehalfOfGroup": ok.get("onBehalfOfGroup", True),
            "record_after": ok.get("record_after_publish"),
        }
    out = topic_dir / "cloud-mcp-bundle.json"
    out.write_text(json.dumps(bundle, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return out


def scripts_phase(topic: str) -> dict:
    chk = subprocess.run(
        [sys.executable, str(SCRIPTS / "is-topic-published.py"), "--topic", topic, "--json"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if chk.returncode == 0:
        return {"status": "already_published", "topic": topic, "check": _json_out(chk)}
    if chk.returncode == 2:
        check = _json_out(chk)
        bundle = write_mcp_bundle(topic)
        if check.get("awaiting_mcp"):
            return {
                "status": "awaiting_mcp",
                "topic": topic,
                "check": check,
                "mcp_bundle": str(bundle),
                "note": "Скрипты готовы — только MCP VK (одна попытка), затем --finish",
            }
        return {
            "status": "awaiting_finish",
            "topic": topic,
            "check": check,
            "mcp_bundle": str(bundle),
            "note": "Cloud+TG готовы — только MCP если не сделан, затем --finish",
        }

    _run([sys.executable, str(SCRIPTS / "materialize_cloud_env.py"), "--check"])
    content = ensure_content(topic)
    pub = _run([sys.executable, str(SCRIPTS / "publish-topic.py"), "--topic", topic])
    pub_log = _json_out(pub)
    tg = ensure_telegram(topic)
    bundle = write_mcp_bundle(topic)
    return {
        "status": "awaiting_mcp",
        "topic": topic,
        "content": content,
        "publish": pub_log.get("status"),
        "telegram": tg,
        "mcp_bundle": str(bundle),
    }


def git_push_publish(topic: str) -> dict:
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
    if add.returncode != 0:
        return {"git_add": "failed", "stderr": add.stderr}

    status = subprocess.run(["git", "status", "--porcelain"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    if not (status.stdout or "").strip():
        return {"git": "nothing_to_commit"}

    commit = subprocess.run(
        ["git", "commit", "-m", f"publish: {topic}"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    if commit.returncode != 0:
        return {"git_commit": "failed", "stderr": commit.stderr}

    push = subprocess.run(["git", "push", "origin", "HEAD"], cwd=PROJECT_ROOT, capture_output=True, text=True)
    return {
        "git_commit": "ok",
        "git_push": "ok" if push.returncode == 0 else "failed",
        "push_stderr": (push.stderr or "")[-500:] if push.returncode != 0 else "",
    }


def finish_phase(topic: str) -> dict:
    close = _run([sys.executable, str(SCRIPTS / "close-cloud-publish.py"), "--topic", topic])
    close_data = _json_out(close)
    verify = _run(
        [sys.executable, str(SCRIPTS / "verify-publish-run.py"), "--topic", topic, "--write", "--json"]
    )
    report = _json_out(verify)
    overall = report.get("overall")
    if overall not in {"pass", "pass_b17_pending"}:
        raise SystemExit(
            f"BLOCKER verify={overall}\n" + json.dumps(report.get("issues") or [], ensure_ascii=False)
        )

    msg = subprocess.run(
        [sys.executable, str(SCRIPTS / "send-max-publish-report.py"), "--topic", topic],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    git = git_push_publish(topic)
    return {
        "status": "finished",
        "topic": topic,
        "verify": overall,
        "close": close_data,
        "max_report": "sent" if msg.returncode == 0 else "failed",
        "git": git,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Cloud MSP publish orchestrator")
    parser.add_argument("--sync", action="store_true", help="Intake + scripts phase")
    parser.add_argument("--topic", help="Topic id for --finish")
    parser.add_argument("--finish", action="store_true", help="close + verify + report + git")
    args = parser.parse_args()

    if args.sync:
        topic_data = intake_topic(sync=True)
        topic = topic_data["topic_id"]
        result = scripts_phase(topic)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if args.finish:
        if not args.topic:
            raise SystemExit("--finish requires --topic")
        result = finish_phase(args.topic)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    raise SystemExit("Укажите --sync или --topic ID --finish")


if __name__ == "__main__":
    main()
