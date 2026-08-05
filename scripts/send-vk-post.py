#!/usr/bin/env python3
"""VK publish prep: upload cover to morozovanatalia.ru for MCP vk_create_post_with_photo.

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
from pathlib import Path

from cover_upload import (
    delete_remote_cover,
    load_upload_env,
    prepare_jpeg,
    public_cover_url,
    upload_cover,
    verify_cover_url,
)

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def extract_post(md_path: Path) -> str:
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from posts_emdr_env import extract_post_body_from_md

    return extract_post_body_from_md(md_path.read_text(encoding="utf-8"))


def delete_topic_covers(topic_id: str, env: dict[str, str]) -> list[str]:
    deleted = []
    for name in (f"{topic_id}.jpg", f"{topic_id}-v2.jpg"):
        try:
            delete_remote_cover(name, env)
            deleted.append(name)
        except Exception:
            deleted.append(f"{name}:skip")
    return deleted


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="01-panic-night")
    parser.add_argument("--upload-cover", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--delete-cover",
        action="store_true",
        help="Remove social-covers/{topic}.jpg from site after VK publish",
    )
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
            result["cover_public_url"] = public_cover_url(remote_name)
            result["upload"] = "dry_run"
        else:
            env = load_upload_env()
            uploaded = upload_cover(jpeg, remote_name, env)
            public_url = uploaded["url"]
            verified = verify_cover_url(public_url)
            if not verified["ok"]:
                raise SystemExit(
                    f"Cover URL does not serve image/jpeg: {public_url} "
                    f"(HTTP {verified['http_status']})"
                )
            result["cover_public_url"] = public_url
            result["cover_http_status"] = verified["http_status"]
            result["cover_serves_image"] = verified["serves_image"]
            result["cover_upload_method"] = uploaded.get("method")
            meta = topic_dir / "vk-cover-public-url.json"
            meta.write_text(
                json.dumps(
                    {"url": public_url, "source": uploaded.get("method", "upload")},
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )

    if args.delete_cover and not args.dry_run:
        env = load_upload_env()
        result["deleted_remote_files"] = delete_topic_covers(args.topic, env)
        meta = topic_dir / "vk-cover-public-url.json"
        if meta.exists():
            meta.unlink()

    log_path = topic_dir / "vk-publish-prep.json"
    log_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
