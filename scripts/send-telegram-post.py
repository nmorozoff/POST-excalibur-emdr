#!/usr/bin/env python3
"""Send Telegram post: cover + text in ONE message (link preview above text).

Default delivery: single sendMessage with large cover preview above full-width HTML text.
Previous posts #01–#02 used this mode (`link_preview_single_message`).

Usage:
  python scripts/send-telegram-post.py --topic 01-panic-night
  python scripts/send-telegram-post.py --topic 01-panic-night --publish
  python scripts/send-telegram-post.py --resolve-chat-id
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
MESSAGE_LIMIT = 4096


def load_env() -> dict[str, str]:
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from posts_emdr_env import load_env as _load, materialize_telegram_env_from_os, ensure_client_story_disclaimer

    materialize_telegram_env_from_os()
    return _load("telegram.env.local", required=["TELEGRAM_BOT_TOKEN"])


def _normalize(text: str) -> str:
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from posts_emdr_env import sanitize_post_text

    return sanitize_post_text(text)


def _urlopen(req: urllib.request.Request, *, timeout: int = 120, context=None):
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from browser_playwright_utils import telegram_proxy_for_urllib

    proxies = telegram_proxy_for_urllib()
    if proxies:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies))
        return opener.open(req, timeout=timeout)
    ctx = context or ssl.create_default_context()
    return urllib.request.urlopen(req, timeout=timeout, context=ctx)


def api_call_form(token: str, method: str, data: dict | None = None, files: dict | None = None) -> dict:
    url = API.format(token=token, method=method)
    if files:
        boundary = "----TgBoundary"
        body_parts: list[bytes] = []
        fields = data or {}
        for key, val in fields.items():
            body_parts.append(
                f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"\r\n\r\n{val}\r\n".encode()
            )
        for key, (filename, content, mime) in files.items():
            body_parts.append(
                (
                    f"--{boundary}\r\nContent-Disposition: form-data; name=\"{key}\"; filename=\"{filename}\"\r\n"
                    f"Content-Type: {mime}\r\n\r\n"
                ).encode()
                + content
                + b"\r\n"
            )
        body_parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(body_parts)
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
    else:
        encoded = urllib.parse.urlencode(data or {}).encode()
        req = urllib.request.Request(url, data=encoded, method="POST")
    ctx = ssl.create_default_context()
    with _urlopen(req, timeout=120, context=ctx) as resp:
        return json.loads(resp.read().decode())


def api_call_json(token: str, method: str, payload: dict) -> dict:
    url = API.format(token=token, method=method)
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    ctx = ssl.create_default_context()
    with _urlopen(req, timeout=120, context=ctx) as resp:
        return json.loads(resp.read().decode())


def extract_html(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    m = re.search(
        r"## Текст поста \(HTML[^\n]*\n\n"
        r"(.*?)"
        r"(?=<!-- END_POST -->|\n---\s*\n## |\Z)",
        text,
        flags=re.DOTALL,
    )
    if not m:
        m = re.search(
            r"## Текст поста\n\n(.*?)(?=<!-- END_POST -->|\n---\s*\n## |\Z)",
            text,
            flags=re.DOTALL,
        )
    if not m:
        # Grsai sometimes returns bare HTML body + <!-- END_POST --> without markdown wrapper.
        if "<!-- END_POST -->" in text and "<a href=" in text:
            return text.split("<!-- END_POST -->", 1)[0].strip()
        raise SystemExit(
            f"Cannot parse HTML from {md_path} — need ## Текст поста (HTML...) or ## Текст поста"
        )
    body = m.group(1).strip()
    if re.search(r"^\s*##\s", body, flags=re.MULTILINE):
        raise SystemExit(
            f"Telegram post in {md_path} includes markdown sections after the body. "
            "Add <!-- END_POST --> before meta/notes."
        )
    return body



def url_is_reachable(image_url: str) -> bool:
    ctx = ssl.create_default_context()
    for method in ("HEAD", "GET"):
        req = urllib.request.Request(image_url, method=method)
        try:
            with urllib.request.urlopen(req, timeout=30, context=ctx) as resp:
                if not (200 <= resp.status < 400):
                    continue
                content_type = (resp.headers.get("Content-Type") or "").lower()
                if content_type.startswith("image/"):
                    return True
                # Some CDNs omit Content-Type on HEAD — verify with GET body sniff.
                if method == "GET" and content_type.startswith("text/html"):
                    return False
                if method == "HEAD" and not content_type:
                    continue
                return not content_type.startswith("text/")
        except Exception:
            continue
    return False


def upload_cover_to_catbox(cover: Path) -> str:
    import subprocess

    result = subprocess.run(
        [
            "curl",
            "-sS",
            "-F",
            "reqtype=fileupload",
            "-F",
            f"fileToUpload=@{cover}",
            "https://catbox.moe/user/api.php",
        ],
        capture_output=True,
        text=True,
        timeout=180,
        check=False,
    )
    public_url = (result.stdout or "").strip()
    if public_url.startswith("https://"):
        return public_url
    raise SystemExit(f"catbox upload failed: {(result.stderr or public_url or 'empty response').strip()}")


def extract_max_cover_url(topic_dir: Path) -> str | None:
    log_path = topic_dir / "max-publish-log.json"
    if not log_path.exists():
        return None
    try:
        data = json.loads(log_path.read_text(encoding="utf-8"))
        attachments = (
            data.get("message", {}).get("body", {}).get("attachments")
            or data.get("attachments")
            or []
        )
        for item in attachments:
            if item.get("type") == "image":
                url = (item.get("payload") or {}).get("url")
                if url:
                    return url
    except (json.JSONDecodeError, AttributeError):
        return None
    return None


def cover_preview_meta_path(topic_dir: Path, cover: Path) -> Path:
    return topic_dir / f"link-preview-{cover.stem}.json"


def load_cover_public_url(
    topic_dir: Path,
    cover: Path,
    *,
    refresh: bool = False,
    force_catbox: bool = False,
) -> str:
    meta_path = cover_preview_meta_path(topic_dir, cover)
    if force_catbox:
        refresh = True

    if not refresh and meta_path.exists():
        cached = json.loads(meta_path.read_text(encoding="utf-8"))
        if cached.get("source") in {"telegram_cdn", "max"}:
            refresh = True
        else:
            cached_url = (cached.get("url") or "").strip()
            if cached_url and url_is_reachable(cached_url):
                return cached_url

    if force_catbox or refresh:
        public_url = upload_cover_to_catbox(cover)
        meta_path.write_text(
            json.dumps({"url": public_url, "source": "catbox"}, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        return public_url

    candidates: list[tuple[str, str]] = []
    cover_url_file = topic_dir / "cover.url"

    max_url = extract_max_cover_url(topic_dir)
    if max_url:
        candidates.append(("max", max_url))

    site_cover = f"https://morozovanatalia.ru/social-covers/{topic_dir.name}.jpg"
    candidates.append(("morozovanatalia", site_cover))

    vk_meta = topic_dir / "vk-cover-public-url.json"
    if vk_meta.exists():
        vk_data = json.loads(vk_meta.read_text(encoding="utf-8"))
        vk_url = (vk_data.get("url") or "").strip()
        vk_source = (vk_data.get("source") or "vk").strip()
        if vk_url:
            candidates.append((vk_source, vk_url))

    if cover_url_file.exists():
        candidates.append(("runware", cover_url_file.read_text(encoding="utf-8").strip()))

    legacy_runware = topic_dir / "cover-runware.url"
    if legacy_runware.exists() and cover.name == "cover-runware.png":
        candidates.append(("runware", legacy_runware.read_text(encoding="utf-8").strip()))

    for source, candidate in candidates:
        if candidate and url_is_reachable(candidate):
            meta_path.write_text(
                json.dumps({"url": candidate, "source": source}, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            return candidate

    public_url = upload_cover_to_catbox(cover)
    meta_path.write_text(
        json.dumps({"url": public_url, "source": "catbox"}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return public_url


def send_photo_only(token: str, chat_id: str, cover: Path) -> dict:
    mime = "image/png" if cover.suffix.lower() == ".png" else "image/jpeg"
    res = api_call_form(
        token,
        "sendPhoto",
        data={"chat_id": chat_id},
        files={"photo": (cover.name, cover.read_bytes(), mime)},
    )
    if not res.get("ok"):
        raise SystemExit(f"sendPhoto failed: {res}")
    return res


def send_full_width_text(token: str, chat_id: str, text: str, *, reply_to: int | None = None) -> dict:
    payload: dict[str, object] = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": True},
    }
    if reply_to is not None:
        payload["reply_to_message_id"] = reply_to
    res = api_call_json(token, "sendMessage", payload)
    if not res.get("ok"):
        raise SystemExit(f"sendMessage failed: {res}")
    return res


def send_post_photo_then_text(token: str, chat_id: str, cover: Path, text: str) -> tuple[dict, dict]:
    photo_res = send_photo_only(token, chat_id, cover)
    text_res = send_full_width_text(token, chat_id, text)
    return photo_res, text_res


def send_post_with_cover_preview(token: str, chat_id: str, text: str, cover_url: str) -> dict:
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML",
        "link_preview_options": {
            "is_disabled": False,
            "url": cover_url,
            "prefer_large_media": True,
            "show_above_text": True,
        },
    }
    res = api_call_json(token, "sendMessage", payload)
    if not res.get("ok"):
        raise SystemExit(f"sendMessage failed: {res}")
    return res


def resolve_chats(token: str) -> dict[str, dict]:
    data = api_call_form(token, "getUpdates", {"limit": 100, "timeout": 0})
    chats: dict[str, dict] = {}
    for upd in data.get("result") or []:
        for key in ("message", "channel_post", "my_chat_member"):
            obj = upd.get(key)
            if not obj:
                continue
            chat = obj.get("chat") or {}
            cid = chat.get("id")
            if cid is None:
                continue
            chats[str(cid)] = {
                "type": chat.get("type"),
                "title": chat.get("title") or chat.get("username") or chat.get("first_name"),
                "username": chat.get("username"),
                "source": key,
            }
    return chats


def resolve_chat_id(token: str) -> None:
    chats = resolve_chats(token)
    if not chats:
        raise SystemExit("chat_id не найден. /start боту или пост в канале с ботом-админом.")
    print(json.dumps({"chats": chats}, ensure_ascii=False, indent=2))
    private = [cid for cid, c in chats.items() if c.get("type") == "private"]
    channels = [cid for cid, c in chats.items() if c.get("type") == "channel"]
    if private:
        update_env_key("TELEGRAM_PREVIEW_CHAT_ID", private[-1])
    if channels:
        update_env_key("TELEGRAM_CHANNEL_CHAT_ID", channels[-1])
    print("Сохранено в telegram.env.local (последний private → PREVIEW, последний channel → CHANNEL)")


def update_env_key(key: str, value: str) -> None:
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    out, replaced = [], False
    prefix = f"{key}="
    for line in lines:
        if line.startswith(prefix):
            out.append(f"{key}={value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")


def resolve_cover(topic_dir: Path) -> Path:
    for name in ("cover.png", "cover-runware.png"):
        path = topic_dir / name
        if path.exists():
            return path
    return topic_dir / "cover.png"


def parse_channel_ids(env: dict[str, str]) -> list[str]:
    raw = env.get("TELEGRAM_CHANNEL_CHAT_IDS", "").strip()
    if raw:
        ids = [item.strip() for item in raw.split(",") if item.strip()]
        if ids:
            return ids
    single = env.get("TELEGRAM_CHANNEL_CHAT_ID") or env.get("TELEGRAM_CHAT_ID", "")
    return [single] if single else []


def parse_channel_utm_sources(env: dict[str, str], channel_count: int) -> list[str]:
    raw = env.get("TELEGRAM_CHANNEL_UTM_SOURCES", "").strip()
    if raw:
        sources = [item.strip() for item in raw.split(",") if item.strip()]
        if len(sources) == channel_count:
            return sources
    return [f"tg{index}" for index in range(1, channel_count + 1)]


def apply_utm_source(html: str, utm_source: str) -> str:
    for old in ("tg1", "tg2", "tg3", "tg"):
        html = re.sub(rf"utm_source={re.escape(old)}", f"utm_source={utm_source}", html)
    return html


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="01-panic-night")
    parser.add_argument("--publish", action="store_true")
    parser.add_argument("--resolve-chat-id", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--refresh-cover-url", action="store_true", help="Re-upload cover public URL")
    parser.add_argument(
        "--delivery",
        choices=("photo_then_text", "link_preview"),
        default="link_preview",
        help="link_preview: ONE message, cover above text (default, posts #01–#02). "
        "photo_then_text: two messages — do NOT use for channels.",
    )
    args = parser.parse_args()

    env = load_env()
    token = env.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        raise SystemExit("TELEGRAM_BOT_TOKEN empty")

    if args.resolve_chat_id:
        resolve_chat_id(token)
        return

    if args.publish:
        chat_ids = parse_channel_ids(env)
        if not chat_ids:
            raise SystemExit(
                "TELEGRAM_CHANNEL_CHAT_IDS (или TELEGRAM_CHANNEL_CHAT_ID) не задан. "
                "Укажите @username каналов в telegram.env.local."
            )
        from posts_emdr_env import assert_telegram_channels

        assert_telegram_channels(env, context="send-telegram-post --publish", require_two=True)
        chat_ids = parse_channel_ids(env)
        if args.delivery == "photo_then_text":
            raise SystemExit(
                "BLOCKER: --publish в каналы запрещён с --delivery photo_then_text "
                "(два сообщения: фото отдельно, текст отдельно). "
                "Используйте default link_preview — одно сообщение с обложкой над текстом."
            )
    else:
        preview_id = env.get("TELEGRAM_PREVIEW_CHAT_ID") or env.get("TELEGRAM_CHAT_ID", "")
        if not preview_id:
            raise SystemExit("TELEGRAM_PREVIEW_CHAT_ID не задан. Напишите боту /start и --resolve-chat-id")
        chat_ids = [preview_id]

    topic_dir = PROJECT_ROOT / "posts-emdr-memory" / "output" / args.topic
    post_file = topic_dir / "telegram-post.md"
    cover = resolve_cover(topic_dir)

    html = _normalize(extract_html(post_file))
    html = ensure_client_story_disclaimer(html, "telegram")
    if len(html) > MESSAGE_LIMIT:
        raise SystemExit(
            f"Telegram text limit is {MESSAGE_LIMIT} chars, post has {len(html)}. "
            "Shorten telegram-post.md or split into a follow-up manually."
        )

    if args.dry_run:
        cover_url = None
        if args.delivery == "link_preview" and cover.exists():
            try:
                cover_url = load_cover_public_url(
                    topic_dir,
                    cover,
                    refresh=args.refresh_cover_url,
                    force_catbox=args.delivery == "link_preview",
                )
            except Exception as exc:
                cover_url = f"<upload failed: {exc}>"
        print(json.dumps({
            "mode": "publish" if args.publish else "preview",
            "delivery": args.delivery,
            "chat_ids": chat_ids,
            "html_chars": len(html),
            "cover": str(cover),
            "cover_public_url": cover_url if args.delivery == "link_preview" else None,
        }, ensure_ascii=False, indent=2))
        return

    if not cover.exists():
        raise SystemExit(f"Cover not found: {cover}")

    cover_url = None
    cover_source = None
    if args.delivery == "link_preview":
        cover_url = load_cover_public_url(
            topic_dir,
            cover,
            refresh=args.refresh_cover_url,
            force_catbox=False,
        )
        cover_source = json.loads(
            cover_preview_meta_path(topic_dir, cover).read_text(encoding="utf-8")
        ).get("source")

    channel_logs: list[dict] = []
    for chat_id in chat_ids:
        if args.delivery == "link_preview":
            msg_res = send_post_with_cover_preview(token, chat_id, html, cover_url)
            channel_logs.append({
                "chat_id": chat_id,
                "message_id": msg_res.get("result", {}).get("message_id"),
            })
        else:
            photo_res, text_res = send_post_photo_then_text(token, chat_id, cover, html)
            channel_logs.append({
                "chat_id": chat_id,
                "photo_message_id": photo_res.get("result", {}).get("message_id"),
                "text_message_id": text_res.get("result", {}).get("message_id"),
            })

    log = {
        "status": "sent",
        "mode": "publish" if args.publish else "preview",
        "delivery": "link_preview_single_message" if args.delivery == "link_preview" else "photo_then_text",
        "html_chars": len(html),
        "channels": channel_logs,
    }
    if args.delivery == "link_preview":
        log["cover_source"] = cover_source
    if len(channel_logs) == 1:
        log["chat_id"] = channel_logs[0]["chat_id"]
        log.update({k: v for k, v in channel_logs[0].items() if k != "chat_id"})
    log_path = topic_dir / ("telegram-publish-log.json" if args.publish else "telegram-preview-log.json")
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
