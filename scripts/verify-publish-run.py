#!/usr/bin/env python3
"""Проверка полноты публикации темы по всем платформам + обложки.

Usage:
  python3 scripts/verify-publish-run.py --topic sb-05-tolerate-uncertainty
  python3 scripts/verify-publish-run.py --topic sb-05 --json
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import sys
from pathlib import Path
from urllib.request import Request, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import MEMORY, PROJECT_ROOT, load_env, publish_text_format_issues

PROFILE = MEMORY / "profile"
EXPECTED_TG_CHANNELS = ("nmorozova_emdr", "natalia_morozova_psy")


def _read_json(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _registry_row(topic: str, registry: Path) -> bool:
    if not registry.is_file():
        return False
    return topic in registry.read_text(encoding="utf-8")


def _url_ok(url: str, *, expect_image: bool = False) -> dict:
    if not url:
        return {"ok": False, "reason": "empty_url"}
    try:
        req = Request(url, method="HEAD")
        with urlopen(req, timeout=20, context=ssl.create_default_context()) as resp:
            ct = (resp.headers.get("Content-Type") or "").lower()
            ok = resp.status == 200
            if expect_image and ok:
                ok = "image" in ct
            return {"ok": ok, "status": resp.status, "content_type": ct}
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def verify_topic(topic: str) -> dict:
    topic_dir = MEMORY / "output" / topic
    report: dict = {
        "topic": topic,
        "overall": "unknown",
        "platforms": {},
        "covers": {},
        "queue": {},
        "vps": {},
        "issues": [],
        "links": {},
    }

    if not topic_dir.is_dir():
        report["overall"] = "fail"
        report["issues"].append(f"Нет папки output/{topic}")
        return report

    cover = topic_dir / "cover.png"
    has_local_cover = cover.is_file()
    report["covers"]["local_cover"] = {"ok": has_local_cover, "path": str(cover)}

    site_url = f"https://morozovanatalia.ru/social-covers/{topic}.jpg"
    site_check = _url_ok(site_url, expect_image=True)
    report["covers"]["site_cover"] = {"url": site_url, **site_check}
    if not has_local_cover and not site_check.get("ok"):
        report["issues"].append("Нет cover.png и site cover недоступен")
    elif not has_local_cover:
        report["covers"]["local_cover"]["note"] = "ok_on_site_only"

    # Max
    max_log = _read_json(topic_dir / "max-publish-log.json")
    max_ok = bool(max_log and max_log.get("status") in {"sent", "ok"})
    max_url = None
    if max_log:
        msg = max_log.get("message") or {}
        body = msg.get("body") or {}
        max_url = body.get("url") or max_log.get("url")
    reg_max = _registry_row(topic, PROFILE / "max-posts-registry.md")
    report["platforms"]["max"] = {
        "ok": max_ok or reg_max,
        "log": bool(max_log),
        "registry": reg_max,
        "url": max_url,
    }
    if max_url:
        report["links"]["max"] = max_url
    elif reg_max:
        m = re.search(
            rf"\| {re.escape(topic)} \| [^|]+ \| [^|]+ \| (https://max\.ru/[^\s|]+)",
            (PROFILE / "max-posts-registry.md").read_text(encoding="utf-8"),
        )
        if m:
            report["links"]["max"] = m.group(1)
    if not report["platforms"]["max"]["ok"]:
        report["issues"].append("Макс: нет publish-log или реестра")

    # Telegram
    tg_log = _read_json(topic_dir / "telegram-publish-log.json")
    tg_ok = tg_log and tg_log.get("status") == "sent"
    delivery = (tg_log or {}).get("delivery")
    channels = (tg_log or {}).get("channels") or []
    ch_names = {str(c.get("chat_id", "")).lstrip("@") for c in channels}
    missing_ch = [c for c in EXPECTED_TG_CHANNELS if c not in ch_names]
    cover_src = (tg_log or {}).get("cover_source")
    tg_links = []
    for ch in channels:
        chat = str(ch.get("chat_id", "")).lstrip("@")
        mid = ch.get("message_id")
        if chat and mid:
            tg_links.append(f"https://t.me/{chat}/{mid}")
    report["platforms"]["telegram"] = {
        "ok": bool(tg_ok and not missing_ch and delivery == "link_preview_single_message"),
        "delivery": delivery,
        "channels": list(ch_names),
        "missing_channels": missing_ch,
        "cover_source": cover_src,
        "urls": tg_links,
    }
    if tg_links:
        report["links"]["telegram"] = tg_links
    if not tg_ok:
        report["issues"].append("Telegram: не отправлен (или VPS ещё не отработал)")
    elif missing_ch:
        report["issues"].append(f"Telegram: нет каналов {missing_ch}")
    elif delivery != "link_preview_single_message":
        report["issues"].append(f"Telegram: delivery={delivery!r}, нужен link_preview_single_message")
    if tg_ok and not cover_src:
        report["issues"].append("Telegram: cover_source пуст — возможно без превью")

    # VK
    vk_prof = _registry_row(topic, PROFILE / "vk-profile-posts-registry.md")
    vk_group = _registry_row(topic, PROFILE / "vk-group-posts-registry.md")
    report["platforms"]["vk_profile"] = {"ok": vk_prof, "registry": vk_prof}
    report["platforms"]["vk_group"] = {"ok": vk_group, "registry": vk_group}
    for reg_path, key in (
        (PROFILE / "vk-profile-posts-registry.md", "vk_profile"),
        (PROFILE / "vk-group-posts-registry.md", "vk_group"),
    ):
        if reg_path.is_file():
            m = re.search(
                rf"\| {re.escape(topic)} \| [^|]+ \| [^|]+ \| \d+ \| (https://vk\.com/[^\s|]+)",
                reg_path.read_text(encoding="utf-8"),
            )
            if m:
                report["links"][key] = m.group(1)
    if not vk_prof:
        report["issues"].append("VK профиль: нет в реестре")
    if not vk_group:
        report["issues"].append("VK группа: нет в реестре")

    vk_handoff = _read_json(topic_dir / "vk-mcp-handoff.json")
    if vk_handoff:
        for call in vk_handoff.get("calls") or []:
            msg = call.get("message") or ""
            for issue in publish_text_format_issues(msg, "vk"):
                report["issues"].append(issue)

    vk_story_log = _read_json(topic_dir / "vk-story-publish-log.json")
    report["platforms"]["vk_story"] = {
        "ok": bool(vk_story_log and vk_story_log.get("status") == "published"),
        "log": bool(vk_story_log),
        "required": False,
    }

    # Facebook
    fb_log = _read_json(topic_dir / "zernio-publish-log.json")
    fb_reg = _registry_row(topic, PROFILE / "facebook-posts-registry.md")
    fb_status = (fb_log or {}).get("status")
    fb_scheduled = fb_log and fb_status == "scheduled" and not fb_reg
    fb_ok = bool((fb_log and fb_status in {"published", "ok", "sent"}) or fb_reg)
    report["platforms"]["facebook"] = {
        "ok": fb_ok,
        "log": bool(fb_log),
        "registry": fb_reg,
        "status": fb_status,
        "pending_scheduled": fb_scheduled,
    }
    fb_url = (fb_log or {}).get("platform_post_url") or (fb_log or {}).get("post_url")
    if fb_url:
        report["links"]["facebook"] = fb_url
    elif fb_reg:
        m = re.search(
            rf"\| {re.escape(topic)} \| [^|]+ \| [^|]+ \| [^|]+ \| (https://www\.facebook\.com/[^\s|]+)",
            (PROFILE / "facebook-posts-registry.md").read_text(encoding="utf-8"),
        )
        if m:
            report["links"]["facebook"] = m.group(1)
    if fb_scheduled:
        report["issues"].append(
            "Facebook: Zernio scheduled — Meta transient error, ждём auto-retry (partial)"
        )
    elif not fb_ok:
        report["issues"].append("Facebook: нет publish-log или реестра")

    # OK (группа) — обязателен только если есть ok-post.md
    ok_md = topic_dir / "ok-post.md"
    ok_log = _read_json(topic_dir / "ok-publish-log.json")
    ok_reg = _registry_row(topic, PROFILE / "ok-posts-registry.md")
    ok_status = (ok_log or {}).get("status")
    ok_ok = bool((ok_log and ok_status in {"published", "ok", "sent"}) or ok_reg)
    if ok_md.is_file():
        report["platforms"]["ok"] = {
            "ok": ok_ok,
            "log": bool(ok_log),
            "registry": ok_reg,
            "status": ok_status,
            "required": True,
        }
        ok_url = (ok_log or {}).get("url") or (ok_log or {}).get("post_url")
        if ok_url:
            report["links"]["ok"] = ok_url
        elif ok_reg:
            m = re.search(
                rf"\| {re.escape(topic)} \| [^|]+ \| [^|]+ \| [^|]+ \| (https://ok\.ru/[^\s|]+)",
                (PROFILE / "ok-posts-registry.md").read_text(encoding="utf-8"),
            )
            if m:
                report["links"]["ok"] = m.group(1)
        if not ok_ok:
            report["issues"].append("OK: нет publish-log или реестра")
        ok_handoff = _read_json(topic_dir / "ok-mcp-handoff.json")
        if ok_handoff:
            ok_text = ok_handoff.get("text") or ""
            fmt_issues = publish_text_format_issues(ok_text, "ok")
            report["platforms"]["ok"]["format_ok"] = not fmt_issues
            for issue in fmt_issues:
                report["issues"].append(issue)
    else:
        report["platforms"]["ok"] = {
            "ok": True,
            "legacy": True,
            "required": False,
            "note": "no ok-post.md (тема до интеграции OK)",
        }

    # b17
    b17_log = _read_json(topic_dir / "b17-publish-log.json")
    b17_status = (b17_log or {}).get("status")
    b17_ok = bool(b17_log and b17_status == "published")
    b17_draft = b17_status == "draft_saved"
    b17_reg = _registry_row(topic, PROFILE / "b17-posts-registry.md")
    report["platforms"]["b17"] = {
        "ok": b17_ok or b17_reg,
        "log": bool(b17_log),
        "registry": b17_reg,
        "status": b17_status,
        "draft_saved": b17_draft,
    }
    b17_url = (b17_log or {}).get("public_url") or (b17_log or {}).get("post_url")
    if b17_url:
        report["links"]["b17"] = b17_url
    if not report["platforms"]["b17"]["ok"]:
        if b17_draft:
            report["issues"].append("b17: сохранено в черновик (rate limit), требуется повторный запуск")
        else:
            report["issues"].append("b17: не published (VPS мог ещё не отработать)")

    # Queue / VPS
    published_path = MEMORY / "topics" / "short-blog-published.md"
    queue_path = MEMORY / "topics" / "short-blog-queue.md"
    in_published = published_path.is_file() and f"`{topic}`" in published_path.read_text(
        encoding="utf-8"
    )
    still_in_queue = queue_path.is_file() and f"`{topic}`" in queue_path.read_text(encoding="utf-8")
    report["queue"] = {
        "published": in_published,
        "still_in_queue": still_in_queue,
    }
    if still_in_queue and not in_published:
        report["issues"].append("Тема всё ещё in_progress в очереди")

    finish = _read_json(topic_dir / "browser-worker-finish.json")
    handoff_done = (topic_dir / "browser-local-handoff.done.md").is_file()
    report["vps"] = {
        "finish_json": bool(finish),
        "handoff_done": handoff_done,
        "status": (finish or {}).get("status"),
    }
    # b17 and TenChat are NOT required for the main short-blog pass.
    # They are handled by the manual repair queue: b17-tenchat-pending-queue.md
    b17_status = report["platforms"]["b17"].get("status")
    b17_draft = b17_status == "draft_saved"

    if not report["platforms"]["telegram"]["ok"]:
        report["issues"].append("VPS phase 3: Telegram ещё не отработал")

    fb_pending = report["platforms"]["facebook"].get("pending_scheduled")
    hard_fail = (
        not report["platforms"]["max"]["ok"]
        or not report["platforms"]["vk_profile"]["ok"]
        or not report["platforms"]["vk_group"]["ok"]
        or (not report["platforms"]["facebook"]["ok"] and not fb_pending)
        or (
            report["platforms"]["ok"].get("required")
            and not report["platforms"]["ok"]["ok"]
        )
        or not report["platforms"]["telegram"]["ok"]
    )
    # b17 draft_saved is informational, not a failure/blocker.
    main_ok = (
        report["platforms"]["max"]["ok"]
        and report["platforms"]["vk_profile"]["ok"]
        and report["platforms"]["vk_group"]["ok"]
        and (report["platforms"]["facebook"]["ok"] or fb_pending)
        and (not report["platforms"]["ok"].get("required") or report["platforms"]["ok"]["ok"])
        and report["platforms"]["telegram"]["ok"]
    )

    if not report["issues"] or (main_ok and not b17_draft):
        report["overall"] = "pass"
    elif b17_draft and main_ok:
        report["overall"] = "pass_b17_pending"
        report["issues"].append(
            "b17: сохранено в черновик (rate limit). Тема считается опубликованной; "
            "b17 выйдет через ручной repair-запуск."
        )
    elif hard_fail:
        report["overall"] = "fail"
    elif fb_pending:
        report["overall"] = "partial"
    else:
        report["overall"] = "fail"

    return report


def format_report_md(report: dict) -> str:
    topic = report["topic"]
    overall = report["overall"]
    emoji = {"pass": "✅", "partial": "⏳", "fail": "❌"}.get(overall, "❓")
    lines = [
        f"{emoji} **Posts EMDR — {topic}**",
        f"Статус: **{overall}**",
        "",
    ]
    if report.get("links"):
        lines.append("**Ссылки:**")
        for name, url in report["links"].items():
            if isinstance(url, list):
                for u in url:
                    lines.append(f"• {name}: {u}")
            else:
                lines.append(f"• {name}: {url}")
        lines.append("")
    if report.get("issues"):
        lines.append("**Проблемы:**")
        for issue in report["issues"]:
            lines.append(f"• {issue}")
        lines.append("")
    if overall == "partial":
        lines.append(
            "_VPS мог ещё публиковать TG/b17; Zernio scheduled — ждём Meta retry. "
            "Подождите 5–15 мин и повторите проверку._"
        )
    elif overall == "fail":
        lines.append("_Нужна помощь: откройте Cursor / проверьте VPS логи._")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description="Verify publish run for topic")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--write", action="store_true", help="Save to output/{topic}/publish-run-report.json")
    args = parser.parse_args()

    report = verify_topic(args.topic)
    if args.write:
        out = MEMORY / "output" / args.topic / "publish-run-report.json"
        out.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(format_report_md(report))

    if report["overall"] == "pass":
        sys.exit(0)
    if report["overall"] == "partial":
        sys.exit(3)
    sys.exit(2)


if __name__ == "__main__":
    main()
