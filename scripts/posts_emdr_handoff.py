#!/usr/bin/env python3
"""Machine handoff for Posts EMDR Cloud runs — агенту не писать вручную."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from posts_emdr_env import PROJECT_ROOT

HANDOFF_PATH = PROJECT_ROOT / ".cursor" / "posts-emdr-handoff.md"


def write_handoff(
    *,
    status: str,
    topic_id: str = "",
    title: str = "",
    note: str = "",
) -> Path:
    """status: in_progress | done | blocked"""
    HANDOFF_PATH.parent.mkdir(parents=True, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    lines = [
        "# Posts EMDR — handoff (machine)",
        "",
        f"updated: {now}",
        f"status: {status}",
    ]
    if topic_id:
        lines.append(f"topic_id: {topic_id}")
    if title:
        lines.append(f"title: {title}")
    if note:
        lines.append(f"note: {note}")
    lines.append("")
    if status == "done":
        lines.append("=== POSTS EMDR DONE ===")
    elif status == "in_progress":
        lines.append("=== POSTS EMDR IN PROGRESS ===")
    elif status == "blocked":
        lines.append("=== POSTS EMDR BLOCKED ===")
    lines.append("")
    HANDOFF_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return HANDOFF_PATH


def write_handoff_done(topic_id: str, *, verify: str = "pass") -> Path:
    return write_handoff(
        status="done",
        topic_id=topic_id,
        note=f"verify={verify}; written by close-cloud-publish.py",
    )


def write_handoff_in_progress(topic_id: str, title: str = "") -> Path:
    return write_handoff(status="in_progress", topic_id=topic_id, title=title)
