#!/usr/bin/env python3
"""Publish VK wall post with photo — no MCP (Cloud-safe).

Usage:
  python3 scripts/vk_publish.py --topic sb-01 --location personal
  python3 scripts/vk_publish.py --topic sb-01 --location group --from-group
"""

from __future__ import annotations

import argparse
import json
import ssl
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import PROJECT_ROOT, extract_post_body_from_md, load_env

VK_API = "https://api.vk.com/method"


def vk_call(method: str, token: str, version: str, params: dict | None = None) -> dict:
    payload = dict(params or {})
    payload["access_token"] = token
    payload["v"] = version
    body = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        f"{VK_API}/{method}",
        data=body,
        method="POST",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if "error" in data:
        raise SystemExit(f"VK {method}: {data['error']}")
    return data["response"]


def download_bytes(url: str) -> bytes:
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(url, timeout=120, context=ctx) as resp:
        return resp.read()


def upload_wall_photo(
    token: str,
    version: str,
    image_bytes: bytes,
    *,
    group_id: str | None = None,
) -> str:
    params: dict[str, str] = {}
    if group_id:
        params["group_id"] = group_id
    upload_info = vk_call("photos.getWallUploadServer", token, version, params)
    upload_url = upload_info["upload_url"]

    boundary = "----VkUpload"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="photo"; filename="cover.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode()
    body += image_bytes + f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        upload_url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST",
    )
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
        upload_result = json.loads(resp.read().decode("utf-8"))

    save_params = {
        "server": upload_result["server"],
        "photo": upload_result["photo"],
        "hash": upload_result["hash"],
    }
    if group_id:
        save_params["group_id"] = group_id
    saved = vk_call("photos.saveWallPhoto", token, version, save_params)
    photo = saved[0]
    return f"photo{photo['owner_id']}_{photo['id']}"


def extract_post(md_path: Path) -> str:
    try:
        return extract_post_body_from_md(md_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def publish(
    *,
    topic: str,
    location: str,
    from_group: bool,
    dry_run: bool,
) -> dict:
    env = load_env(
        "vk.env.local",
        required=["VK_ACCESS_TOKEN", "VK_GROUP_ID"],
    )
    token = env["VK_ACCESS_TOKEN"]
    version = env.get("VK_API_VERSION", "5.199")
    group_id = env["VK_GROUP_ID"]

    topic_dir = PROJECT_ROOT / "posts-emdr-memory" / "output" / topic
    md_name = "vk-group-post.md" if location == "group" else "vk-profile-post.md"
    message = extract_post(topic_dir / md_name)

    prep_path = topic_dir / "vk-publish-prep.json"
    if not prep_path.exists():
        raise SystemExit(f"Missing {prep_path} — run send-vk-post.py --upload-cover first")
    prep = json.loads(prep_path.read_text(encoding="utf-8"))
    photo_url = prep.get("cover_public_url")
    if not photo_url:
        raise SystemExit("cover_public_url missing in vk-publish-prep.json")

    result: dict = {
        "topic": topic,
        "location": location,
        "from_group": from_group,
        "photo_url": photo_url,
        "message_chars": len(message),
        "dry_run": dry_run,
    }

    if dry_run:
        result["status"] = "dry_run"
        return result

    image_bytes = download_bytes(photo_url)
    gid = group_id if location == "group" else None
    attachment = upload_wall_photo(token, version, image_bytes, group_id=gid)

    post_params: dict[str, str | int] = {
        "message": message,
        "attachments": attachment,
    }
    if location == "group":
        post_params["owner_id"] = f"-{group_id}"
        if from_group:
            post_params["from_group"] = 1
    else:
        me = vk_call("users.get", token, version, {})
        post_params["owner_id"] = me[0]["id"]

    wall = vk_call("wall.post", token, version, post_params)
    result["status"] = "published"
    result["post_id"] = wall.get("post_id")
    owner = post_params["owner_id"]
    result["wall_url"] = f"https://vk.com/wall{owner}_{wall.get('post_id')}"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--location", choices=("personal", "group"), default="personal")
    parser.add_argument("--from-group", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = publish(
        topic=args.topic,
        location=args.location,
        from_group=args.from_group,
        dry_run=args.dry_run,
    )
    topic_dir = PROJECT_ROOT / "posts-emdr-memory" / "output" / args.topic
    log_path = topic_dir / "vk-publish-log.json"
    existing = []
    if log_path.exists():
        try:
            existing = json.loads(log_path.read_text(encoding="utf-8"))
            if isinstance(existing, dict):
                existing = [existing]
        except json.JSONDecodeError:
            existing = []
    existing.append(result)
    log_path.write_text(json.dumps(existing, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
