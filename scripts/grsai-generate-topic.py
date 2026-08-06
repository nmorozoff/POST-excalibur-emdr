#!/usr/bin/env python3
"""Generate MSP short-blog texts via Grsai Chat API (gemini-3.1-pro).

Usage:
  python3 scripts/grsai-generate-topic.py --topic sb-10-phrase-when-anxiety
  python3 scripts/grsai-generate-topic.py --topic sb-10-phrase-when-anxiety --platform max
  python3 scripts/grsai-generate-topic.py --topic sb-10-phrase-when-anxiety --dry-run

Key: posts-emdr-memory/grsai.env.local (GRSAI_API_KEY — тот же, что для обложек).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from grsai_chat import DEFAULT_TIMEOUT_SEC, chat_completion
from posts_emdr_env import MEMORY, load_env, post_number_from_topic, remove_znakomo

PROFILE = MEMORY / "profile"
SCRIPTS = Path(__file__).resolve().parent

QUEUE_ROW_RE = re.compile(
    r"^\|\s*`([^`]+)`\s*\|\s*(\d+)\s*\|\s*([^|]+)\|\s*([^|]+)\|\s*(.+?)\s*\|\s*$"
)

PLATFORM_SPECS: dict[str, dict[str, str]] = {
    "max": {
        "output": "max-post.md",
        "prompt": "max-post-prompt.md",
        "registry": "max-posts-registry.md",
        "kind": "source",
    },
    "telegram": {
        "output": "telegram-post.md",
        "prompt": "telegram-post-prompt.md",
        "registry": "telegram-posts-registry.md",
        "kind": "rewrite",
    },
    "vk-profile": {
        "output": "vk-profile-post.md",
        "prompt": "vk-post-prompt.md",
        "registry": "vk-profile-posts-registry.md",
        "kind": "rewrite",
        "note": "Режим VK профиль: utm_source=vk, перелинковка только vk-profile-posts-registry.md",
    },
    "vk-group": {
        "output": "vk-group-post.md",
        "prompt": "vk-post-prompt.md",
        "registry": "vk-group-posts-registry.md",
        "kind": "rewrite",
        "note": "Режим VK группа: utm_source=vk_group, перелинковка только vk-group-posts-registry.md",
    },
    "facebook": {
        "output": "facebook-post.md",
        "prompt": "facebook-post-prompt.md",
        "registry": "facebook-posts-registry.md",
        "kind": "rewrite",
    },
    "ok": {
        "output": "ok-post.md",
        "prompt": "ok-post-prompt.md",
        "registry": "ok-posts-registry.md",
        "kind": "rewrite",
    },
    "b17": {
        "output": "b17-blog-post.md",
        "prompt": "b17-blog-post-prompt.md",
        "registry": "b17-posts-registry.md",
        "kind": "rewrite",
    },
}

GENERATION_ORDER = [
    "max",
    "telegram",
    "vk-profile",
    "vk-group",
    "facebook",
    "ok",
    "b17",
]

SYSTEM_PROMPT = """Ты — профессиональный русскоязычный копирайтер для психолога Натальи Морозовой (EMDR).
Строго следуй контракту платформы. Пиши живо, без эзотерики, без слова «Знакомо».
Не используй длинное тире «—» (заменяй на запятую).
Выводи ТОЛЬКО содержимое целевого markdown-файла, без пояснений до или после."""


def read_text(path: Path, *, max_chars: int = 14000) -> str:
    if not path.is_file():
        return ""
    text = path.read_text(encoding="utf-8")
    if len(text) > max_chars:
        return text[:max_chars] + "\n\n[... обрезано для лимита контекста ...]"
    return text


def load_topic_brief(topic_id: str) -> dict[str, str]:
    for rel in ("topics/short-blog-queue.md", "topics/short-blog-published.md"):
        path = MEMORY / rel
        if not path.is_file():
            continue
        for line in path.read_text(encoding="utf-8").splitlines():
            if f"`{topic_id}`" not in line:
                continue
            m = QUEUE_ROW_RE.match(line.strip())
            if not m:
                continue
            site_path = m.group(4).strip()
            if site_path.startswith("http"):
                site_url = site_path
            else:
                site_url = f"https://morozovanatalia.ru{site_path if site_path.startswith('/') else '/' + site_path}"
            return {
                "topic_id": m.group(1),
                "post_number": m.group(2),
                "format": m.group(3).strip(),
                "site_path": site_path,
                "site_url": site_url,
                "title": m.group(5).strip(),
            }
    raise SystemExit(f"topic_id not found in queue/published: {topic_id}")


def registry_excerpt(registry_name: str, *, max_rows: int = 10) -> str:
    path = PROFILE / registry_name
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    rows: list[str] = []
    in_published = False
    for line in lines:
        if line.strip() == "## Опубликованные":
            in_published = True
            continue
        if in_published and line.startswith("## "):
            break
        if in_published and line.startswith("|") and "topic_id" not in line and "---" not in line:
            rows.append(line)
    return "\n".join(rows[:max_rows])


def cta_context(post_number: int) -> str:
    soft_slot = post_number % 3
    full_session = post_number % 4 == 0
    return (
        f"Номер поста MSP: {post_number}\n"
        f"Мягкий контакт (short-blog-cta-rules): слот {soft_slot} (sb-NN % 3)\n"
        f"Полный CTA пробной сессии: {'да (#NN % 4 == 0)' if full_session else 'нет'}\n"
        "ЛС Макс: https://max.ru/se13417616_biz/AZ9H9rFePFc\n"
        "ЛС TG/VK/FB/OK: https://t.me/natalyamorozovaa\n"
    )


def shared_context() -> str:
    parts = [
        read_text(PROFILE / "tone-of-voice.md", max_chars=8000),
        read_text(PROFILE / "author-profile.md", max_chars=6000),
        read_text(PROFILE / "emdr-evidence.md", max_chars=6000),
        read_text(PROFILE / "crosslink-rules.md", max_chars=5000),
        read_text(PROFILE / "short-blog-cta-rules.md", max_chars=5000),
        read_text(MEMORY / "shared/agent-pipeline-pitfalls.md", max_chars=4000),
    ]
    return "\n\n---\n\n".join(p for p in parts if p.strip())


def strip_code_fence(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    return text.strip()


def postprocess_platform(platform: str, text: str) -> str:
    text = strip_code_fence(text)
    text = remove_znakomo(text)
    if platform == "telegram" and "<!-- END_POST -->" not in text:
        if "\n---\n" in text:
            head, tail = text.split("\n---\n", 1)
            if "## Мета" in tail or "## Meta" in tail:
                text = head.rstrip() + "\n\n<!-- END_POST -->\n\n---\n" + tail
            else:
                text = head.rstrip() + "\n\n<!-- END_POST -->"
        else:
            text = text.rstrip() + "\n\n<!-- END_POST -->"
    return text


def parse_cover_meta(max_post: str) -> dict[str, str]:
    header = max_post.split("\n---\n", 1)[0]
    line1 = re.search(r"Line 1:\s*(.+)", header)
    line2 = re.search(r"Line 2:\s*(.+)", header)
    line3 = re.search(r"Line 3:\s*(.+)", header)
    yellow = re.search(r"жёлтый:\s*(.+?)\)", header)
    if not (line1 and line2 and line3):
        raise SystemExit("Cannot parse cover lines from max-post.md (need Line 1/2/3 in header)")
    line2_text = re.sub(r"\s*\*\(жёлтый:.*", "", line2.group(1)).strip()
    yellow_word = yellow.group(1).strip() if yellow else ""
    if not yellow_word:
        yellow_word = line2_text.split()[-1] if line2_text else ""
    return {
        "line1": line1.group(1).strip(),
        "line2": line2_text,
        "line3": line3.group(1).strip(),
        "yellow": yellow_word,
    }


def outfit_block(topic_id: str) -> str:
    n = post_number_from_topic(topic_id) or 1
    slot = ((n - 1) % 12) + 1
    text = read_text(PROFILE / "cover-outfit-rotation.md", max_chars=20000)
    for line in text.splitlines():
        if line.startswith(f"| **{slot}** |") or line.startswith(f"| {slot} |"):
            m = re.search(r"`(OUTFIT:.*?)`", line)
            if m:
                return m.group(1)
    raise SystemExit(f"OUTFIT slot {slot} not found in cover-outfit-rotation.md")


def build_cover_prompt(topic_id: str, cover_meta: dict[str, str]) -> str:
    template_path = PROFILE / "social-cover-prompt-template.md"
    template = read_text(template_path, max_chars=20000)
    m = re.search(r"```\n(YouTube thumbnail[\s\S]+?)```", template)
    if not m:
        raise SystemExit("Cannot extract cover template from social-cover-prompt-template.md")
    block = m.group(1)
    block = block.replace("{OUTFIT_BLOCK}", outfit_block(topic_id))
    block = block.replace("{LINE1}", cover_meta["line1"])
    block = block.replace("{LINE2}", cover_meta["line2"])
    block = block.replace("{LINE3}", cover_meta["line3"])
    block = block.replace("{YELLOW_WORD}", cover_meta["yellow"] or cover_meta["line2"].split()[-1])
    return block.strip() + "\n"


def build_max_user_prompt(brief: dict[str, str]) -> str:
    post_num = int(brief["post_number"])
    contract = read_text(PROFILE / PLATFORM_SPECS["max"]["prompt"])
    registry = registry_excerpt(PLATFORM_SPECS["max"]["registry"])
    return f"""Создай файл max-post.md для темы MSP short-blog.

topic_id: {brief['topic_id']}
Заголовок темы: {brief['title']}
Формат: {brief['format']}
Номер MSP: #{brief['post_number']}
Сайт (для финальной ссылки): {brief['site_url']}?utm_source=max
EMDR-лендинг: https://morozovanatalia.ru/emdr-therapy?utm_source=max

{cta_context(post_num)}

Контракт max-post:
{contract}

Реестр для перелинковки (max → max, последние посты):
{registry}

Общий контекст:
{shared_context()}

В шапке файла обязательно блок **Обложка:** с Line 1/2/3 и *(жёлтый: слово)*.
Целевой объём ## Текст поста: 3500–3800 символов.
"""


def build_rewrite_user_prompt(
    platform: str,
    brief: dict[str, str],
    spec: dict[str, str],
    max_post: str,
) -> str:
    post_num = int(brief["post_number"])
    contract = read_text(PROFILE / spec["prompt"])
    registry = registry_excerpt(spec["registry"])
    utm_map = {
        "telegram": "tg1",
        "vk-profile": "vk",
        "vk-group": "vk_group",
        "facebook": "fb",
        "ok": "ok",
        "b17": "b17",
    }
    utm = utm_map.get(platform, "max")
    extra = spec.get("note", "")
    return f"""Создай файл {spec['output']} — рерайт (НЕ копипаст) max-post.md.

topic_id: {brief['topic_id']}
Заголовок: {brief['title']}
Сайт для финальной ссылки: {brief['site_url']}?utm_source={utm}

{cta_context(post_num)}
{extra}

Контракт платформы:
{contract}

Реестр перелинковки ({platform}):
{registry}

Исходник max-post.md:
---
{max_post}
---

Общий контекст:
{shared_context()}
"""


def generate_platform(
    platform: str,
    *,
    api_key: str,
    base_url: str,
    model: str,
    brief: dict[str, str],
    max_post: str | None,
    temperature: float,
    timeout_sec: int,
) -> tuple[str, dict[str, Any]]:
    spec = PLATFORM_SPECS[platform]
    if spec["kind"] == "source":
        user_prompt = build_max_user_prompt(brief)
    else:
        if not max_post:
            raise SystemExit(f"max-post.md required before generating {platform}")
        user_prompt = build_rewrite_user_prompt(platform, brief, spec, max_post)

    result = chat_completion(
        api_key=api_key,
        base_url=base_url,
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=temperature,
        timeout_sec=timeout_sec,
    )
    text = postprocess_platform(platform, result.content)
    meta = {
        "model": result.model,
        "usage": result.usage,
        "chars": len(text),
    }
    return text, meta


def main() -> None:
    parser = argparse.ArgumentParser(description="Grsai text generation for Posts EMDR")
    parser.add_argument("--topic", required=True, help="topic_id e.g. sb-10-phrase-when-anxiety")
    parser.add_argument(
        "--platform",
        choices=list(PLATFORM_SPECS.keys()) + ["all"],
        default="all",
        help="Generate one platform or all (default: all)",
    )
    parser.add_argument("--dry-run", action="store_true", help="Print plan only, no API calls")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Regenerate even if output file already exists (default: skip existing)",
    )
    parser.add_argument("--temperature", type=float, default=0.7)
    args = parser.parse_args()

    brief = load_topic_brief(args.topic)
    out_dir = MEMORY / "output" / args.topic
    out_dir.mkdir(parents=True, exist_ok=True)

    platforms = GENERATION_ORDER if args.platform == "all" else [args.platform]
    if args.platform != "all" and args.platform != "max":
        if "max" not in platforms and not (out_dir / "max-post.md").is_file():
            raise SystemExit("max-post.md missing — generate max first")

    if args.dry_run:
        print(
            json.dumps(
                {
                    "dry_run": True,
                    "topic": brief,
                    "platforms": platforms,
                    "output_dir": str(out_dir),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return

    env = load_env("grsai.env.local", required=["GRSAI_API_KEY"])
    api_key = env["GRSAI_API_KEY"]
    base_url = env.get("GRSAI_API_BASE", "https://grsaiapi.com")
    model = env.get("GRSAI_CHAT_MODEL", "gemini-3.1-pro")

    model = env.get("GRSAI_CHAT_MODEL", "gemini-3.1-pro")
    timeout_raw = env.get("GRSAI_CHAT_TIMEOUT_SEC", str(DEFAULT_TIMEOUT_SEC)).strip()
    try:
        timeout_sec = max(120, int(timeout_raw))
    except ValueError:
        timeout_sec = DEFAULT_TIMEOUT_SEC

    log_path = out_dir / "grsai-content-log.json"
    log: dict[str, Any] = {}
    if log_path.is_file():
        try:
            log = json.loads(log_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            log = {}
    log.update(
        {
            "topic": args.topic,
            "backend": "grsai",
            "model": model,
            "base_url": base_url,
            "timeout_sec": timeout_sec,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
    )
    log.setdefault("platforms", {})

    max_post: str | None = None
    max_path = out_dir / "max-post.md"
    if max_path.is_file():
        max_post = max_path.read_text(encoding="utf-8")

    for platform in platforms:
        out_name = PLATFORM_SPECS[platform]["output"]
        out_path = out_dir / out_name
        if out_path.is_file() and not args.force:
            print(f"Skip {platform} (exists): {out_name}", file=sys.stderr)
            log["platforms"].setdefault(
                platform,
                {"file": out_name, "skipped": True, "chars": len(out_path.read_text(encoding="utf-8"))},
            )
            if platform == "max":
                max_post = out_path.read_text(encoding="utf-8")
            continue

        if platform != "max" and not max_post:
            raise SystemExit("max-post.md missing — generate max first")

        print(f"Generating {platform} (timeout {timeout_sec}s)...", file=sys.stderr)
        text, meta = generate_platform(
            platform,
            api_key=api_key,
            base_url=base_url,
            model=model,
            brief=brief,
            max_post=max_post,
            temperature=args.temperature,
            timeout_sec=timeout_sec,
        )
        out_path.write_text(text + "\n", encoding="utf-8")
        log["platforms"][platform] = {"file": out_name, **meta}
        print(f"  → {out_name} ({meta['chars']} chars)", file=sys.stderr)

        if platform == "max":
            max_post = text
            cover_meta = parse_cover_meta(text)
            cover_prompt = build_cover_prompt(args.topic, cover_meta)
            cover_path = out_dir / "cover-prompt.txt"
            if not cover_path.is_file() or args.force:
                cover_path.write_text(cover_prompt, encoding="utf-8")
                log["cover_prompt"] = {"chars": len(cover_prompt), "cover_meta": cover_meta}
                print("  → cover-prompt.txt", file=sys.stderr)
            else:
                print("  → cover-prompt.txt (exists, skip)", file=sys.stderr)

    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "ok", "topic": args.topic, "log": str(log_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
