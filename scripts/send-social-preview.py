#!/usr/bin/env python3
"""Send LinkedIn/Facebook post previews to Telegram preview chat.

Usage:
  python scripts/send-social-preview.py --topic 01-panic-night
  python scripts/send-social-preview.py --topic 01-panic-night --platform linkedin
"""

from __future__ import annotations

import argparse
import json
import re
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / "posts-emdr-memory" / "telegram.env.local"
API = "https://api.telegram.org/bot{token}/{method}"


def load_env() -> dict[str, str]:
    if not ENV_FILE.exists():
        raise SystemExit(f"Missing {ENV_FILE}")
    data: dict[str, str] = {}
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip()
    return data


def api_call_form(token: str, method: str, data: dict | None = None, files: dict | None = None) -> dict:
    url = API.format(token=token, method=method)
    if files:
        boundary = "----SocialPreview"
        body_parts: list[bytes] = []
        for key, val in (data or {}).items():
            body_parts.append(
                f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"\r\n\r\n{val}\r\n'.encode()
            )
        for key, (filename, content, mime) in files.items():
            body_parts.append(
                (
                    f'--{boundary}\r\nContent-Disposition: form-data; name="{key}"; filename="{filename}"\r\n'
                    f"Content-Type: {mime}\r\n\r\n"
                ).encode()
                + content
                + b"\r\n"
            )
        body_parts.append(f"--{boundary}--\r\n".encode())
        req = urllib.request.Request(
            url,
            data=b"".join(body_parts),
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
    else:
        req = urllib.request.Request(url, data=urllib.parse.urlencode(data or {}).encode(), method="POST")
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
        return json.loads(resp.read().decode())


def extract_post(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"## Текст поста\n\n(.*)", text, re.S)
    if not m:
        raise SystemExit(f"Cannot parse post from {md_path}")
    return m.group(1).strip()


PLATFORMS = {
    "linkedin": "linkedin-post.md",
    "facebook": "facebook-post.md",
}


def send_preview(token: str, chat_id: str, platform: str, topic_dir: Path) -> dict:
    md_name = PLATFORMS[platform]
    post_text = extract_post(topic_dir / md_name)
    cover = topic_dir / "cover.png"
    if not cover.exists():
        raise SystemExit(f"Missing {cover}")

    header = f"📋 Превью {platform.upper()} — {topic_dir.name}\n\nОбложка + текст ниже. Скопируйте в {platform.title()}."
    api_call_form(token, "sendMessage", {"chat_id": chat_id, "text": header})

    photo_resp = api_call_form(
        token,
        "sendPhoto",
        {"chat_id": chat_id},
        {"photo": (cover.name, cover.read_bytes(), "image/png")},
    )

    # Telegram limit 4096; split if needed
    chunks: list[str] = []
    remaining = post_text
    while remaining:
        chunks.append(remaining[:4000])
        remaining = remaining[4000:]

    msg_ids = []
    for i, chunk in enumerate(chunks):
        label = f"Текст ({i + 1}/{len(chunks)}):\n\n" if len(chunks) > 1 else ""
        resp = api_call_form(
            token,
            "sendMessage",
            {"chat_id": chat_id, "text": label + chunk, "disable_web_page_preview": "true"},
        )
        msg_ids.append(resp.get("result", {}).get("message_id"))

    return {
        "platform": platform,
        "chars": len(post_text),
        "photo_message_id": photo_resp.get("result", {}).get("message_id"),
        "text_message_ids": msg_ids,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="01-panic-night")
    parser.add_argument("--platform", choices=["linkedin", "facebook", "all"], default="all")
    args = parser.parse_args()

    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN")
    chat_id = env.get("TELEGRAM_PREVIEW_CHAT_ID") or env.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise SystemExit("Need TELEGRAM_BOT_TOKEN and TELEGRAM_PREVIEW_CHAT_ID")

    topic_dir = PROJECT_ROOT / "posts-emdr-memory" / "output" / args.topic
    platforms = list(PLATFORMS) if args.platform == "all" else [args.platform]

    results = [send_preview(token, chat_id, p, topic_dir) for p in platforms]
    log_path = topic_dir / "social-preview-log.json"
    log_path.write_text(json.dumps({"topic": args.topic, "results": results}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
