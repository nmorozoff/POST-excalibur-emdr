#!/usr/bin/env python3
"""VK publish prep: upload cover to morozovanatalia.ru for MCP vk_create_post_with_photo.

VK API flow (photos.getWallUploadServer → upload → saveWallPhoto → wall.post)
requires a public HTTPS URL that VK servers can fetch. Catbox/Runware often timeout
from VK; morozovanatalia.ru (Beget) works.

Usage:
  python scripts/send-vk-post.py --topic 01-panic-night --upload-cover
  python scripts/send-vk-post.py --topic 01-panic-night --upload-cover --dry-run

After --upload-cover, publish via MCP user-mcp-kv vk_create_post_with_photo:
  photo_url = output cover_public_url
  publish_location = personal | group (+ from_group=true for group)
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import tempfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SITE_COVER_BASE = "https://morozovanatalia.ru/social-covers"


def load_ftp_env() -> dict[str, str]:
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from posts_emdr_env import MEMORY, load_env as _load

    if (MEMORY / "ftp.env.local").exists() or __import__("os").environ.get("FTP_SERVER"):
        return _load(
            "ftp.env.local",
            required=["FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD"],
        )
    legacy = Path("/Users/natala/Documents/Проекты СURSOR/sessya-morozova/.ftp-deploy.env")
    if legacy.is_file():
        data: dict[str, str] = {}
        for line in legacy.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip().strip('"').strip("'")
        for key in ("FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD"):
            if not data.get(key):
                raise SystemExit(f"Missing {key} in legacy {legacy}")
        return data
    return _load(
        "ftp.env.local",
        required=["FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD"],
    )


def extract_post(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"## Текст поста\n\n(.*)", text, re.S)
    if not m:
        raise SystemExit(f"Cannot parse post from {md_path}")
    return m.group(1).strip()


def prepare_jpeg(cover: Path) -> Path:
    out = Path(tempfile.gettempdir()) / f"{cover.stem}-vk.jpg"
    subprocess.run(
        [
            "sips",
            "-s",
            "format",
            "jpeg",
            "-s",
            "formatOptions",
            "65",
            "--resampleWidth",
            "1024",
            str(cover),
            "--out",
            str(out),
        ],
        check=True,
        capture_output=True,
    )
    return out


def ftp_upload(local: Path, remote_name: str, env: dict[str, str]) -> str:
    server = env["FTP_SERVER"].lstrip("ftp://")
    remote_dir = env.get("FTP_SERVER_DIR", "/public_html/").rstrip("/")
    remote = f"social-covers/{remote_name}"
    url = f"ftp://{server}{remote_dir}/{remote}"
    cmd = [
        "curl",
        "-sS",
        "--fail",
        "--ftp-pasv",
        "-u",
        f"{env['FTP_USERNAME']}:{env['FTP_PASSWORD']}",
        "-T",
        str(local),
        "--ftp-create-dirs",
        url,
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return f"{SITE_COVER_BASE}/{remote_name}"


def ftp_delete(remote_name: str, env: dict[str, str]) -> None:
    server = env["FTP_SERVER"].lstrip("ftp://")
    remote_dir = env.get("FTP_SERVER_DIR", "/public_html/").rstrip("/")
    remote_path = f"social-covers/{remote_name}"
    url = f"ftp://{server}{remote_dir}/{remote_path}"
    cmd = [
        "curl",
        "-sS",
        "--ftp-pasv",
        "-u",
        f"{env['FTP_USERNAME']}:{env['FTP_PASSWORD']}",
        url,
        "-Q",
        f"DELE {remote_path}",
    ]
    subprocess.run(cmd, check=False, capture_output=True, text=True)


def delete_topic_covers(topic_id: str, env: dict[str, str]) -> list[str]:
    deleted = []
    for name in (f"{topic_id}.jpg", f"{topic_id}-v2.jpg"):
        ftp_delete(name, env)
        deleted.append(name)
    return deleted


def verify_url(url: str) -> int:
    r = subprocess.run(
        ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", url],
        capture_output=True,
        text=True,
        check=False,
    )
    return int((r.stdout or "0").strip() or "0")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="01-panic-night")
    parser.add_argument("--upload-cover", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--delete-cover", action="store_true", help="Remove social-covers/{topic}.jpg from site after VK publish")
    args = parser.parse_args()

    topic_dir = PROJECT_ROOT / "posts-emdr-memory" / "output" / args.topic
    cover = topic_dir / "cover.png"
    if not cover.exists():
        raise SystemExit(f"Missing {cover}")

    profile = extract_post(topic_dir / "vk-profile-post.md")
    group = extract_post(topic_dir / "vk-group-post.md")
    remote_name = f"{args.topic}.jpg"

    result: dict = {
        "topic": args.topic,
        "profile_chars": len(profile),
        "group_chars": len(group),
        "cover_local": str(cover),
    }

    if args.upload_cover:
        jpeg = prepare_jpeg(cover)
        result["cover_jpeg_bytes"] = jpeg.stat().st_size
        if args.dry_run:
            result["cover_public_url"] = f"{SITE_COVER_BASE}/{remote_name}"
            result["upload"] = "dry_run"
        else:
            env = load_ftp_env()
            public_url = ftp_upload(jpeg, remote_name, env)
            status = verify_url(public_url)
            if status != 200:
                raise SystemExit(f"Cover URL not reachable: {public_url} (HTTP {status})")
            result["cover_public_url"] = public_url
            result["cover_http_status"] = status
            meta = topic_dir / "vk-cover-public-url.json"
            meta.write_text(json.dumps({"url": public_url, "source": "morozovanatalia-ftp"}, indent=2) + "\n", encoding="utf-8")

    if args.delete_cover and not args.dry_run:
        env = load_ftp_env()
        result["deleted_remote_files"] = delete_topic_covers(args.topic, env)
        meta = topic_dir / "vk-cover-public-url.json"
        if meta.exists():
            meta.unlink()

    log_path = topic_dir / "vk-publish-prep.json"
    log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
