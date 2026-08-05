#!/usr/bin/env python3
"""Shared env loader for Posts EMDR — local files + Cloud Agent env vars."""

from __future__ import annotations

import base64
import json
import os
import re
import secrets
import tempfile
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORY = PROJECT_ROOT / "posts-emdr-memory"


def wordpress_media_upload(cover_path: Path, topic: str | None = None) -> dict[str, str]:
    """Upload cover to WordPress Media Library via REST API."""
    try:
        data = load_env("wordpress.env.local", required=["WORDPRESS_URL", "WORDPRESS_USER", "WORDPRESS_APP_PASSWORD"])
    except SystemExit as exc:
        return {"error": str(exc), "url": "", "id": ""}

    base_url = data["WORDPRESS_URL"].rstrip("/")
    user = data["WORDPRESS_USER"]
    password = data["WORDPRESS_APP_PASSWORD"]
    credentials = base64.b64encode(f"{user}:{password}".encode()).decode("ascii")

    # Convert to JPEG if needed (WP accepts PNG, but JPEG is smaller and reliable)
    from PIL import Image
    jpeg_path = Path(tempfile.gettempdir()) / f"wp-cover-{cover_path.stem}.jpg"
    img = Image.open(cover_path)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGB")
    img.save(jpeg_path, "JPEG", quality=85, optimize=True)

    filename = f"{cover_path.stem}.jpg" if topic is None else f"{topic}.jpg"
    slug = topic or cover_path.stem

    boundary = f"----WebKitFormBoundary{secrets.token_hex(8)}"
    body_lines = [
        f"--{boundary}",
        f'Content-Disposition: form-data; name="file"; filename="{filename}"',
        "Content-Type: image/jpeg",
        "",
        jpeg_path.read_bytes().decode("latin-1"),
        f"--{boundary}",
        'Content-Disposition: form-data; name="title"',
        "",
        f"Cover {slug}",
        f"--{boundary}",
        'Content-Disposition: form-data; name="alt_text"',
        "",
        f"Cover image for {slug}",
        f"--{boundary}--",
    ]
    body = "\r\n".join(body_lines).encode("latin-1")

    req = urllib.request.Request(
        f"{base_url}/wp-json/wp/v2/media",
        data=body,
        headers={
            "Authorization": f"Basic {credentials}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            result = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")[:500]
        return {"error": f"HTTP {e.code}: {err}", "url": "", "id": ""}
    except Exception as e:
        return {"error": str(e), "url": "", "id": ""}

    return {
        "url": result.get("source_url", ""),
        "id": str(result.get("id", "")),
        "link": result.get("link", ""),
    }


def remove_znakomo(text: str) -> str:
    """Remove the word 'Знакомо' and its variants from post text.

    The user explicitly banned this word across all platforms.
    """
    # Pattern 1: 'Знакомо?' at the start of a paragraph followed by another paragraph
    text = re.sub(r"\n[Зз]накомо[а-яё]?\?\s*\n", "\n\n", text)
    # Pattern 2: 'Знакомо?' before a capitalized sentence (e.g. 'Знакомо? Это не лень...')
    text = re.sub(r"[Зз]накомо[а-яё]?\?\s+(?=[А-ЯЁ])", "", text)
    # Pattern 3: 'Знакомо?' anywhere else (end of sentence, inline, etc.)
    text = re.sub(r"\s*[Зз]накомо[а-яё]?\?\s*", " ", text)
    # Clean up artifacts
    text = re.sub(r" +", " ", text)
    text = re.sub(r"\n\n+", "\n\n", text)
    return text.strip()


def normalize_typography(text: str) -> str:
    """Replace long dashes (em/en) with safe punctuation before publishing.

    - em dash (—) → comma + single space (with surrounding spaces normalized)
    - en dash (–) → hyphen
    - collapse double commas / hanging spaces from replacement
    """
    # Replace em dash with comma + space, absorbing surrounding spaces
    text = re.sub(r"\s*\u2014\s*", ", ", text)
    text = text.replace("\u2013", "-")
    # Cleanup any artifacts like " ,  " or ",  " → ", "
    text = re.sub(r"\s*,\s+", ", ", text)
    text = re.sub(r",\s+,", ", ", text)
    return text.strip()


def sanitize_post_text(text: str) -> str:
    """Apply all text normalization rules before publishing."""
    text = remove_znakomo(text)
    text = normalize_typography(text)
    return text

# Each .env.local file: list of keys (also read from os.environ in cloud).
ENV_SPECS: dict[str, list[str]] = {
    "max.env.local": ["MAX_BOT_TOKEN", "MAX_CHAT_ID", "MAX_PREVIEW_CHAT_ID"],
    "telegram.env.local": [
        "TELEGRAM_BOT_TOKEN",
        "TELEGRAM_CHANNEL_CHAT_IDS",
        "TELEGRAM_CHANNEL_CHAT_ID",
        "TELEGRAM_CHANNEL_UTM_SOURCES",
        "TELEGRAM_PREVIEW_CHAT_ID",
        "TELEGRAM_CHAT_ID",
    ],
    "vk.env.local": ["VK_ACCESS_TOKEN", "VK_GROUP_ID", "VK_API_VERSION"],
    "zernio.env.local": [
        "ZERNIO_API_KEY",
        "ZERNIO_FACEBOOK_ACCOUNT_ID",
        "ZERNIO_PROFILE_ID",
    ],
    "runware.env.local": [
        "RUNWARE_API_KEY",
        "RUNWARE_COVER_WIDTH",
        "RUNWARE_COVER_HEIGHT",
        "RUNWARE_COVER_QUALITY",
        "RUNWARE_REFERENCE_IMAGE",
    ],
    "kie.env.local": [
        "KIE_API_KEY",
        "KIE_API_BASE",
        "KIE_COVER_ASPECT_RATIO",
        "KIE_COVER_RESOLUTION",
        "KIE_REFERENCE_IMAGE",
    ],
    "ftp.env.local": [
        "FTP_SERVER",
        "FTP_USERNAME",
        "FTP_PASSWORD",
        "FTP_SERVER_DIR",
    ],
    "wordpress.env.local": [
        "WORDPRESS_URL",
        "WORDPRESS_USER",
        "WORDPRESS_APP_PASSWORD",
    ],
    "wordpress.env.local": [
        "WORDPRESS_URL",
        "WORDPRESS_SITE_URL",
        "WORDPRESS_USER",
        "WORDPRESS_APP_PASSWORD",
    ],
    "b17.env.local": [
        "UNDETECTABLE_BASE_URL",
        "UNDETECTABLE_PROFILE_ID",
        "UNDETECTABLE_API_BEARER",
        "B17_COMPOSE_URL",
    ],
    "tenchat.env.local": [
        "UNDETECTABLE_BASE_URL",
        "UNDETECTABLE_PROFILE_ID",
        "UNDETECTABLE_API_BEARER",
        "TENCHAT_COMPOSE_URL",
        "TENCHAT_TOPICS",
        "TENCHAT_USE_CODE_BLOCK",
    ],
    "browser.env.local": [
        "BROWSER_BACKEND",
        "PLAYWRIGHT_STORAGE_STATE",
        "PLAYWRIGHT_HEADLESS",
        "BROWSER_PROXY_SERVER",
        "BROWSER_PROXY_USERNAME",
        "BROWSER_PROXY_PASSWORD",
        "B17_PROXY_SERVER",
        "B17_PROXY_USERNAME",
        "B17_PROXY_PASSWORD",
        "TELEGRAM_PROXY_SERVER",
        "TELEGRAM_PROXY_USERNAME",
        "TELEGRAM_PROXY_PASSWORD",
        "TELEGRAM_PROXY_CONNECT_PORT",
        "TELEGRAM_ASOCKS_PORT_NAME",
        "TELEGRAM_ASOCKS_PORT_ID",
        "ASOCKS_API_BASE",
        "ASOCKS_API_KEY",
        "ASOCKS_PORT_NAME",
        "ASOCKS_PORT_ID",
        "B17_PROXY_CONNECT_PORT",
        "VPS_WEBHOOK_SECRET",
    ],
    "github.env.local": ["GITHUB_TOKEN"],
}

DEFAULT_REFERENCE = MEMORY / "assets" / "reference" / "portrait.jpg"
REFERENCE_DIR = MEMORY / "assets" / "reference"
REFERENCE_MANIFEST = REFERENCE_DIR / "manifest.json"
_TOPIC_NUM_RE = re.compile(r"(?:^|[-_])sb[-_]?(\d+)", re.I)


def _parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.is_file():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def load_env(
    filename: str,
    *,
    required: list[str] | None = None,
    memory_dir: Path | None = None,
) -> dict[str, str]:
    """Load env: file values overridden by os.environ (cloud secrets)."""
    base = memory_dir or MEMORY
    path = base / filename
    data = _parse_env_file(path)

    for key in ENV_SPECS.get(filename, []):
        val = os.environ.get(key, "").strip()
        if val:
            data[key] = val

    # KIE_API_KEY also accepted bare in environ (cloud secrets)
    if filename == "kie.env.local" and not data.get("KIE_API_KEY"):
        bare = os.environ.get("KIE_API_KEY", "").strip()
        if bare:
            data["KIE_API_KEY"] = bare

    # RUNWARE_API_KEY legacy
    if filename == "runware.env.local" and not data.get("RUNWARE_API_KEY"):
        bare = os.environ.get("RUNWARE_API_KEY", "").strip()
        if bare:
            data["RUNWARE_API_KEY"] = bare

    if required:
        missing = [k for k in required if not data.get(k)]
        if missing:
            hint = (
                f"Set in {path} or as environment variables in Cursor Cloud Secrets: "
                + ", ".join(missing)
            )
            raise SystemExit(f"Missing {filename}: {', '.join(missing)}. {hint}")

    return data


def materialize_env_files(*, memory_dir: Path | None = None, force: bool = False) -> list[str]:
    """Write .env.local from os.environ — for Cloud Agent startup."""
    base = memory_dir or MEMORY
    written: list[str] = []
    for filename, keys in ENV_SPECS.items():
        values = {k: os.environ.get(k, "").strip() for k in keys}
        if not any(values.values()):
            continue
        path = base / filename
        if path.exists() and not force:
            existing = _parse_env_file(path)
            merged = {**existing}
            for k, v in values.items():
                if v:
                    merged[k] = v
            values = merged
        else:
            values = {k: v for k, v in values.items() if v}

        if not values:
            continue

        lines = [f"# materialized for cloud — do not commit secrets\n"]
        for key in keys:
            if key in values:
                lines.append(f"{key}={values[key]}")
        for key, val in values.items():
            if key not in keys:
                lines.append(f"{key}={val}")
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        written.append(str(path.relative_to(PROJECT_ROOT)))
    return written


def post_number_from_topic(topic_id: str | None) -> int | None:
    """sb-04-foo → 4; legacy 01-panic-night → 1."""
    if not topic_id:
        return None
    m = _TOPIC_NUM_RE.search(topic_id)
    if m:
        return int(m.group(1))
    m = re.match(r"^(\d+)", topic_id)
    if m:
        return int(m.group(1))
    return None


def reference_slot_count() -> int:
    if not REFERENCE_MANIFEST.is_file():
        return 8
    try:
        data = json.loads(REFERENCE_MANIFEST.read_text(encoding="utf-8"))
        slots = data.get("slots") or []
        return max(len(slots), 1)
    except (json.JSONDecodeError, OSError):
        return 8


def reference_slot_for_topic(topic_id: str | None) -> int:
    """1-based slot for portrait rotation (8 slots by default)."""
    n = post_number_from_topic(topic_id)
    if n is None:
        return 1
    count = reference_slot_count()
    return ((n - 1) % count) + 1


def _reference_from_manifest(slot: int) -> Path | None:
    if not REFERENCE_MANIFEST.is_file():
        return None
    try:
        data = json.loads(REFERENCE_MANIFEST.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    slots = data.get("slots") or []
    for item in slots:
        if int(item.get("n", 0)) == slot:
            path = REFERENCE_DIR / str(item.get("file", ""))
            if path.is_file():
                return path
    fallback_name = data.get("fallback", "portrait.jpg")
    fallback = REFERENCE_DIR / fallback_name
    return fallback if fallback.is_file() else None


def reference_image_path(topic_id: str | None = None) -> Path:
    """Portrait for cover i2i (Kie/Runware). Rotates by topic unless KIE/RUNWARE override set."""
    for env_name, key in (
        ("kie.env.local", "KIE_REFERENCE_IMAGE"),
        ("runware.env.local", "RUNWARE_REFERENCE_IMAGE"),
    ):
        env = load_env(env_name)
        raw = env.get(key, "").strip()
        if raw:
            p = Path(raw)
            if p.is_file():
                return p
    if topic_id:
        rotated = _reference_from_manifest(reference_slot_for_topic(topic_id))
        if rotated is not None:
            return rotated
    if DEFAULT_REFERENCE.is_file():
        return DEFAULT_REFERENCE
    return Path(raw) if raw else DEFAULT_REFERENCE


def has_vk_access_token() -> bool:
    try:
        data = load_env("vk.env.local")
    except SystemExit:
        return False
    return bool(data.get("VK_ACCESS_TOKEN", "").strip())


def vk_group_id() -> str:
    try:
        return load_env("vk.env.local").get("VK_GROUP_ID", "224685309")
    except SystemExit:
        return "224685309"


def is_cloud_runtime() -> bool:
    return bool(
        os.environ.get("CURSOR_CLOUD")
        or os.environ.get("CURSOR_AGENT")
        or os.environ.get("CI")
    )


def undetectable_config() -> dict[str, str]:
    """Merged Undetectable settings from env files + os.environ."""
    data: dict[str, str] = {}
    for name in ("b17.env.local", "tenchat.env.local"):
        try:
            data.update(load_env(name))
        except SystemExit:
            pass
    base = (
        data.get("UNDETECTABLE_BASE_URL")
        or os.environ.get("UNDETECTABLE_BASE_URL")
        or "http://127.0.0.1:25325"
    )
    return {
        "base_url": base.rstrip("/"),
        "profile_id": data.get("UNDETECTABLE_PROFILE_ID", ""),
        "bearer": data.get("UNDETECTABLE_API_BEARER") or os.environ.get("UNDETECTABLE_API_BEARER", ""),
    }


def undetectable_reachable(base_url: str | None = None) -> bool:
    import urllib.error
    import urllib.request

    cfg = undetectable_config()
    url = (base_url or cfg["base_url"]).rstrip("/") + "/status"
    headers = {}
    bearer = cfg.get("bearer", "").strip()
    if bearer:
        headers["Authorization"] = f"Bearer {bearer}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            if resp.status != 200:
                return False
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
            return body.get("code") == 0
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError, ValueError):
        return False


def _browser_env() -> dict[str, str]:
    data: dict[str, str] = {}
    for name in ("browser.env.local", "b17.env.local", "tenchat.env.local"):
        try:
            data.update(load_env(name))
        except SystemExit:
            pass
    for key in ("BROWSER_BACKEND", "PLAYWRIGHT_STORAGE_STATE", "PLAYWRIGHT_HEADLESS"):
        val = os.environ.get(key, "").strip()
        if val:
            data[key] = val
    return data


def browser_backend_name() -> str:
    data = _browser_env()
    backend = (data.get("BROWSER_BACKEND") or os.environ.get("BROWSER_BACKEND") or "undetectable").strip().lower()
    if backend in {"playwright", "pw"}:
        return "playwright"
    return "undetectable"


def browser_headless() -> bool:
    data = _browser_env()
    raw = (data.get("PLAYWRIGHT_HEADLESS") or os.environ.get("PLAYWRIGHT_HEADLESS") or "1").strip().lower()
    return raw not in {"0", "false", "no", "off"}


def playwright_storage_state_path() -> Path:
    data = _browser_env()
    raw = (data.get("PLAYWRIGHT_STORAGE_STATE") or os.environ.get("PLAYWRIGHT_STORAGE_STATE") or "").strip()
    if raw:
        path = Path(raw)
        return path if path.is_absolute() else PROJECT_ROOT / raw
    return MEMORY / "browser" / "linux-storage-state.json"
