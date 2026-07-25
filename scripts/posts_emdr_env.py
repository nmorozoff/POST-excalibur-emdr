#!/usr/bin/env python3
"""Shared env loader for Posts EMDR — local files + Cloud Agent env vars."""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORY = PROJECT_ROOT / "posts-emdr-memory"

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
    "ftp.env.local": ["FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD", "FTP_SERVER_DIR"],
    "b17.env.local": [
        "UNDETECTABLE_BASE_URL",
        "UNDETECTABLE_PROFILE_ID",
        "B17_COMPOSE_URL",
    ],
    "tenchat.env.local": [
        "UNDETECTABLE_BASE_URL",
        "UNDETECTABLE_PROFILE_ID",
        "TENCHAT_COMPOSE_URL",
        "TENCHAT_TOPICS",
        "TENCHAT_USE_CODE_BLOCK",
    ],
}

DEFAULT_REFERENCE = MEMORY / "assets" / "reference" / "portrait.jpg"


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

    # RUNWARE_API_KEY also accepted bare in environ (runware-cover legacy)
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


def reference_image_path() -> Path:
    env = load_env("runware.env.local")
    raw = env.get("RUNWARE_REFERENCE_IMAGE", "").strip()
    if raw:
        p = Path(raw)
        if p.is_file():
            return p
    if DEFAULT_REFERENCE.is_file():
        return DEFAULT_REFERENCE
    return Path(raw) if raw else DEFAULT_REFERENCE


def is_cloud_runtime() -> bool:
    return bool(
        os.environ.get("CURSOR_CLOUD")
        or os.environ.get("CURSOR_AGENT")
        or os.environ.get("CI")
    )


def undetectable_reachable(base_url: str | None = None) -> bool:
    import urllib.error
    import urllib.request

    url = (base_url or os.environ.get("UNDETECTABLE_BASE_URL") or "http://127.0.0.1:25325").rstrip("/")
    try:
        with urllib.request.urlopen(f"{url}/status", timeout=3) as resp:
            return 200 <= resp.status < 500
    except (urllib.error.URLError, TimeoutError, OSError):
        return False
