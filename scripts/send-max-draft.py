#!/usr/bin/env python3
"""Send Max post: preview to DM (default) or publish to channel.

Usage:
  # Черновик в ЛС с ботом (по умолчанию):
  python scripts/send-max-draft.py --topic 01-panic-night

  # Публикация в канал (чистый текст, без «Черновик»):
  python scripts/send-max-draft.py --topic 01-panic-night --publish

  python scripts/send-max-draft.py --resolve-chat-id   # chat_id лички → MAX_PREVIEW_CHAT_ID
  python scripts/send-max-draft.py --delete-mid mid.xxx
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import ssl
import time
import uuid
from pathlib import Path
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import fix_max_markdown_links, sanitize_post_text, validate_max_ls_cta

API_BASE = "https://platform-api2.max.ru"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / "posts-emdr-memory" / "max.env.local"


def load_env() -> dict[str, str]:
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from posts_emdr_env import load_env as _load

    return _load("max.env.local", required=["MAX_BOT_TOKEN"])


DRAFT_HEADER_TMPL = "📋 **Черновик {topic}**\n\n"


def api_request(
    token: str,
    method: str,
    path: str,
    *,
    query: dict | None = None,
    body: dict | None = None,
    raw_body: bytes | None = None,
    content_type: str = "application/json",
    insecure_tls: bool = False,
) -> dict:
    url = API_BASE + path
    if query:
        url += "?" + urlencode({k: str(v) for k, v in query.items() if v is not None})

    headers = {"Authorization": token}
    data = raw_body
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = content_type
    elif raw_body is not None:
        headers["Content-Type"] = content_type

    req = Request(url, data=data, headers=headers, method=method)
    ctx = ssl._create_unverified_context() if insecure_tls else None
    try:
        with urlopen(req, timeout=120, context=ctx) as resp:
            text = resp.read().decode("utf-8")
            return json.loads(text) if text else {}
    except HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"MAX API {e.code} {path}: {err}") from e


def parse_chat_id(raw: str) -> int:
    raw = raw.strip()
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    raise ValueError(
        f"MAX_CHAT_ID must be numeric (e.g. -76326762551894), not username. Got: {raw!r}"
    )


def extract_post_body(md_path: Path) -> str:
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from posts_emdr_env import normalize_typography

    text = md_path.read_text(encoding="utf-8")
    m = re.search(
        r"## Текст поста.*?\n\n(.*?)\n\n---\n\n## Мета",
        text,
        flags=re.DOTALL,
    )
    if not m:
        # fallback: до последнего --- перед ## Мета
        m = re.search(
            r"## Текст поста.*?\n\n(.*?)\n\n---\s*\n\n## ",
            text,
            flags=re.DOTALL,
        )
    if not m:
        raise SystemExit(f"Cannot parse post body from {md_path}")
    return sanitize_post_text(m.group(1).strip())


def split_post_text(post_text: str, *, limit: int = 3500) -> list[str]:
    """Разбить длинный пост на части для лимита Max (~3900)."""
    if len(post_text) <= limit:
        return [post_text]
    if "\n\n---\n\n" in post_text:
        parts = post_text.split("\n\n---\n\n")
        chunks: list[str] = []
        buf = ""
        for part in parts:
            candidate = part if not buf else f"{buf}\n\n---\n\n{part}"
            if buf and len(candidate) > limit:
                chunks.append(buf)
                buf = part
            else:
                buf = candidate
        if buf:
            chunks.append(buf)
        if all(len(c) <= limit for c in chunks) and len(chunks) > 1:
            return chunks
    # fallback: по абзацам
    paragraphs = post_text.split("\n\n")
    chunks = []
    buf = ""
    for para in paragraphs:
        candidate = para if not buf else f"{buf}\n\n{para}"
        if buf and len(candidate) > limit:
            chunks.append(buf)
            buf = para
        else:
            buf = candidate
    if buf:
        chunks.append(buf)
    return chunks if chunks else [post_text[:limit]]


def upload_image(token: str, image_path: Path, insecure_tls: bool) -> dict:
    meta = api_request(token, "POST", "/uploads", query={"type": "image"}, insecure_tls=insecure_tls)
    upload_url = meta.get("url")
    if not upload_url:
        raise SystemExit(f"No upload url: {meta}")

    boundary = f"----MaxDraft{uuid.uuid4().hex}"
    mime = mimetypes.guess_type(image_path.name)[0] or "image/png"
    file_bytes = image_path.read_bytes()

    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="data"; filename="{image_path.name}"\r\n'
        f"Content-Type: {mime}\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = Request(
        upload_url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    ctx = ssl._create_unverified_context() if insecure_tls else None
    with urlopen(req, timeout=180, context=ctx) as resp:
        result = json.loads(resp.read().decode("utf-8"))

    photos = result.get("photos")
    if not photos:
        raise SystemExit(f"Upload returned no photos: {result}")

    time.sleep(1.5)
    return photos


def send_message(
    token: str,
    text: str,
    *,
    chat_id: int | None = None,
    user_id: int | None = None,
    photos: dict | None = None,
    format_mode: str | None = "markdown",
    insecure_tls: bool = False,
) -> dict:
    payload: dict = {"text": text, "notify": True}
    if format_mode:
        payload["format"] = format_mode
    if photos:
        payload["attachments"] = [{"type": "image", "payload": {"photos": photos}}]

    query: dict = {}
    if chat_id is not None:
        query["chat_id"] = chat_id
    elif user_id is not None:
        query["user_id"] = int(user_id)
    else:
        raise ValueError("chat_id or user_id required")

    return api_request(
        token,
        "POST",
        "/messages",
        query=query,
        body=payload,
        insecure_tls=insecure_tls,
    )


def resolve_chat_id_interactive(token: str, insecure_tls: bool) -> int:
    """Delete webhooks temporarily, poll once for bot_started/message_created."""
    subs = api_request(token, "GET", "/subscriptions", insecure_tls=insecure_tls)
    saved = subs.get("subscriptions") or []
    for sub in saved:
        url = sub.get("url")
        if url:
            api_request(
                token,
                "DELETE",
                "/subscriptions",
                query={"url": url},
                insecure_tls=insecure_tls,
            )

    print("Напишите боту в Макс «старт» или любое сообщение (30 сек)...")
    data = api_request(
        token,
        "GET",
        "/updates",
        query={"limit": 10, "timeout": 30, "types": "bot_started,message_created,bot_added"},
        insecure_tls=insecure_tls,
    )
    for upd in data.get("updates") or []:
        cid = upd.get("chat_id") or (upd.get("message") or {}).get("recipient", {}).get("chat_id")
        if cid is not None:
            return int(cid)

    raise SystemExit("chat_id не найден. Напишите боту и повторите --resolve-chat-id")


def update_env_key(key: str, value: int | str) -> None:
    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    out: list[str] = []
    prefix = f"{key}="
    replaced = False
    for line in lines:
        if line.startswith(prefix):
            out.append(f"{key}={value}")
            replaced = True
        else:
            out.append(line)
    if not replaced:
        out.append(f"{key}={value}")
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")


def update_env_chat_id(chat_id: int) -> None:
    update_env_key("MAX_PREVIEW_CHAT_ID", chat_id)


def delete_message(token: str, message_id: str, insecure_tls: bool) -> dict:
    return api_request(
        token,
        "DELETE",
        "/messages",
        query={"message_id": message_id},
        insecure_tls=insecure_tls,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview or publish Max post")
    parser.add_argument("--topic", default="01-panic-night")
    parser.add_argument("--text-file", type=Path)
    parser.add_argument("--cover", type=Path)
    parser.add_argument(
        "--publish",
        action="store_true",
        help="Опубликовать в канал (чистый текст, без шапки «Черновик»)",
    )
    parser.add_argument("--resolve-chat-id", action="store_true")
    parser.add_argument("--delete-mid", metavar="MESSAGE_ID")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Без обложки (только текст) — для согласования черновика",
    )
    args = parser.parse_args()

    env = load_env()
    token = env.get("MAX_BOT_TOKEN", "")
    if not token:
        raise SystemExit("MAX_BOT_TOKEN empty in max.env.local")

    insecure = env.get("MAX_API_INSECURE_TLS", "true").lower() == "true"

    if args.delete_mid:
        result = delete_message(token, args.delete_mid, insecure)
        print(json.dumps({"status": "deleted", "result": result}, ensure_ascii=False, indent=2))
        return

    if args.resolve_chat_id:
        cid = resolve_chat_id_interactive(token, insecure)
        update_env_chat_id(cid)
        print(json.dumps({"status": "ok", "MAX_PREVIEW_CHAT_ID": cid}, ensure_ascii=False))
        return

    if args.publish:
        chat_raw = env.get("MAX_CHANNEL_CHAT_ID") or env.get("MAX_CHAT_ID", "")
        mode = "publish"
        use_user_id = None
    else:
        chat_raw = env.get("MAX_PREVIEW_CHAT_ID") or env.get("MAX_DM_CHAT_ID") or ""
        use_user_id = env.get("MAX_PREVIEW_USER_ID") or None
        mode = "preview"

    if not chat_raw and not use_user_id:
        raise SystemExit(
            "MAX_PREVIEW_CHAT_ID не задан. Напишите боту в ЛС и запустите:\n"
            "  python scripts/send-max-draft.py --resolve-chat-id"
        )

    chat_id = None
    if chat_raw:
        try:
            chat_id = parse_chat_id(chat_raw)
        except ValueError as e:
            raise SystemExit(f"{e}") from e

    topic_dir = PROJECT_ROOT / "posts-emdr-memory" / "output" / args.topic
    text_file = args.text_file or topic_dir / "max-post.md"
    cover = args.cover or topic_dir / "cover.png"
    if not cover.exists():
        cover = topic_dir / "cover-runware.png"

    post_text = extract_post_body(text_file)
    post_text = fix_max_markdown_links(post_text)

    ls_issues = validate_max_ls_cta(post_text)
    if ls_issues and mode == "publish":
        raise SystemExit(
            "Публикация в Макс заблокирована (неверная ссылка ЛС):\n"
            + "\n".join(f"  • {i}" for i in ls_issues)
        )

    if mode == "publish":
        full_text = post_text
    else:
        header = DRAFT_HEADER_TMPL.format(topic=args.topic)
        full_text = header + post_text

    if args.dry_run:
        print(json.dumps({
            "mode": mode,
            "chat_id": chat_id,
            "text_chars": len(full_text),
            "cover": str(cover),
            "cover_exists": cover.exists(),
            "has_draft_header": mode == "preview",
        }, ensure_ascii=False, indent=2))
        return

    if not cover.exists() and not args.text_only:
        raise SystemExit(f"Cover not found: {cover}")

    def deliver(text: str, *, photos_payload: dict | None = None) -> dict:
        return send_message(
            token,
            text,
            chat_id=chat_id,
            user_id=int(use_user_id) if use_user_id and chat_id is None else None,
            photos=photos_payload,
            insecure_tls=insecure,
        )

    if args.text_only:
        result = deliver(full_text, photos_payload=None)
        if isinstance(result, dict) and "message" in result:
            result = {"status": "ok", "mode": mode, "text_only": True, **result}
            preview_cid = result.get("message", {}).get("recipient", {}).get("chat_id")
            if mode == "preview" and preview_cid:
                update_env_key("MAX_PREVIEW_CHAT_ID", preview_cid)
    else:
        photos = upload_image(token, cover, insecure)
        result = deliver(full_text, photos_payload=photos)
        if isinstance(result, dict) and "message" in result:
            result = {"status": "ok", "mode": mode, **result}
            preview_cid = result.get("message", {}).get("recipient", {}).get("chat_id")
            if mode == "preview" and preview_cid:
                update_env_key("MAX_PREVIEW_CHAT_ID", preview_cid)

    log_name = "max-publish-log.json" if mode == "publish" else "max-preview-log.json"
    log_path = topic_dir / log_name
    log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({
        "status": "sent",
        "mode": mode,
        "chat_id": chat_id,
        "log": str(log_path),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
