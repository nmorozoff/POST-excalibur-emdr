#!/usr/bin/env python3
"""После успешной публикации b17+TenChat: реестры, закрытие handoff, очередь."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, PROJECT_ROOT

SCRIPTS = PROJECT_ROOT / "scripts"
PROFILE = MEMORY / "profile"


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _log_status(topic_dir: Path, name: str) -> str | None:
    path = topic_dir / f"{name}-publish-log.json"
    if not path.is_file():
        return None
    try:
        return _read_json(path).get("status")
    except (json.JSONDecodeError, OSError):
        return None


def _extract_title(topic_dir: Path, platform: str) -> str:
    log = _read_json(topic_dir / f"{platform}-publish-log.json")
    if log.get("title"):
        return str(log["title"])
    md = topic_dir / f"{platform}-blog-post.md" if platform == "b17" else topic_dir / "tenchat-post.md"
    if md.is_file():
        m = re.search(r"^## Заголовок\s*\n\n(.+?)\n", md.read_text(encoding="utf-8"), re.M)
        if m:
            return m.group(1).strip()
    return topic_dir.name


def _site_url_for_topic(topic_id: str) -> str:
    row_re = re.compile(
        r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*(.+?)\s*\|\s*$"
    )
    for path in (MEMORY / "topics" / "short-blog-queue.md", MEMORY / "topics" / "short-blog-published.md"):
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if f"`{topic_id}`" not in line:
                continue
            m = row_re.match(line.strip())
            if not m:
                continue
            site = m.group(4).strip()
            if site.startswith("http"):
                return site
            return f"https://morozovanatalia.ru{site if site.startswith('/') else '/' + site}"
    return "https://morozovanatalia.ru/anxiety"


def _append_registry(path: Path, row: str) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    for i, line in enumerate(lines):
        if line.strip() == "## Опубликованные" and i + 2 < len(lines):
            lines.insert(i + 2, row)
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            return
    raise SystemExit(f"No ## Опубликованные in {path}")


def _registry_has_topic(path: Path, topic_id: str) -> bool:
    if not path.is_file():
        return False
    return f"| {topic_id} " in path.read_text(encoding="utf-8") or f"| `{topic_id}`" in path.read_text(
        encoding="utf-8"
    )


def finish_topic(topic_id: str, *, skip_queue: bool = False) -> dict:
    topic_dir = MEMORY / "output" / topic_id
    if not topic_dir.is_dir():
        raise SystemExit(f"No output dir: {topic_dir}")

    b17_status = _log_status(topic_dir, "b17")
    ten_status = _log_status(topic_dir, "tenchat")
    if b17_status != "published" or ten_status != "published":
        raise SystemExit(
            f"Not ready to finish {topic_id}: b17={b17_status}, tenchat={ten_status} (need published)"
        )

    b17_log = _read_json(topic_dir / "b17-publish-log.json")
    ten_log = _read_json(topic_dir / "tenchat-publish-log.json")
    d = date.today().isoformat()
    site_url = _site_url_for_topic(topic_id)
    title_b17 = _extract_title(topic_dir, "b17")
    title_ten = _extract_title(topic_dir, "tenchat")
    b17_url = b17_log.get("post_url") or b17_log.get("compose_url", "https://www.b17.ru/my_blog.php")
    ten_url = ten_log.get("post_url") or ten_log.get("compose_url", "https://tenchat.ru/")

    b17_registry = PROFILE / "b17-posts-registry.md"
    ten_registry = PROFILE / "tenchat-posts-registry.md"

    if not _registry_has_topic(b17_registry, topic_id):
        _append_registry(
            b17_registry,
            f"| {topic_id} | {d} | {title_b17} | {b17_url} | {site_url} | b17,психология |",
        )
    if not _registry_has_topic(ten_registry, topic_id):
        _append_registry(
            ten_registry,
            f"| {topic_id} | {d} | {title_ten} | {ten_url} | {site_url} | tenchat,психология |",
        )

    handoff = topic_dir / "browser-local-handoff.md"
    if handoff.is_file():
        done = topic_dir / "browser-local-handoff.done.md"
        handoff.rename(done)

    queue_result = None
    if not skip_queue:
        queue_path = MEMORY / "topics" / "short-blog-queue.md"
        if queue_path.is_file() and f"`{topic_id}`" in queue_path.read_text(encoding="utf-8"):
            proc = subprocess.run(
                [sys.executable, str(SCRIPTS / "mark-short-blog-published.py"), "--topic-id", topic_id],
                cwd=PROJECT_ROOT,
                capture_output=True,
                text=True,
            )
            queue_result = {
                "exit_code": proc.returncode,
                "stdout": proc.stdout.strip(),
                "stderr": proc.stderr.strip(),
            }
            if proc.returncode != 0:
                raise SystemExit(f"mark-short-blog-published failed: {proc.stderr}")
        else:
            queue_result = {"skipped": True, "reason": "topic_not_in_queue"}

    worker_log = {
        "topic": topic_id,
        "status": "browser_worker_finished",
        "date": d,
        "b17_url": b17_url,
        "tenchat_url": ten_url,
        "site_url": site_url,
        "queue": queue_result,
    }
    (topic_dir / "browser-worker-finish.json").write_text(
        json.dumps(worker_log, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return worker_log


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--topic", required=True)
    p.add_argument("--skip-queue", action="store_true", help="Only registries + handoff, not queue")
    args = p.parse_args()
    result = finish_topic(args.topic, skip_queue=args.skip_queue)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
