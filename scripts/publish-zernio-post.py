#!/usr/bin/env python3
"""Publish Facebook post via Zernio API.

LinkedIn отменён (блокировка). Zernio — только Facebook Page.

Usage:
  python scripts/publish-zernio-post.py --topic 01-panic-night
  python scripts/publish-zernio-post.py --topic 01-panic-night --dry-run
"""

from __future__ import annotations

import argparse
import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE = PROJECT_ROOT / "posts-emdr-memory" / "zernio.env.local"
API_URL = "https://zernio.com/api/v1/posts"


def load_env() -> dict[str, str]:
    import sys

    sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
    from posts_emdr_env import load_env as _load

    return _load(
        "zernio.env.local",
        required=["ZERNIO_API_KEY", "ZERNIO_FACEBOOK_ACCOUNT_ID"],
    )


def extract_post(md_path: Path) -> str:
    try:
        return extract_post_body_from_md(md_path.read_text(encoding="utf-8"))
    except ValueError as exc:
        raise SystemExit(str(exc)) from exc


def upload_cover(topic: str) -> str:
    import subprocess

    r = subprocess.run(
        ["python3", str(PROJECT_ROOT / "scripts" / "send-vk-post.py"), "--topic", topic, "--upload-cover"],
        capture_output=True,
        text=True,
        check=False,
    )
    if r.returncode != 0:
        raise SystemExit(r.stderr or r.stdout or "cover upload failed")
    data = json.loads(r.stdout)
    url = data.get("cover_public_url")
    if not url:
        raise SystemExit("No cover_public_url from upload-cover")
    return url


def delete_cover(topic: str) -> None:
    import subprocess

    subprocess.run(
        ["python3", str(PROJECT_ROOT / "scripts" / "send-vk-post.py"), "--topic", topic, "--delete-cover"],
        check=False,
    )


def zernio_request(env: dict[str, str], method: str, url: str, body: bytes | None = None) -> dict:
    headers = {"Authorization": f"Bearer {env['ZERNIO_API_KEY']}"}
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        raise SystemExit(f"Zernio API HTTP {e.code}: {err}") from e


def fetch_zernio_post(env: dict[str, str], post_id: str) -> dict:
    return zernio_request(env, "GET", f"{API_URL}/{post_id}")


def wait_for_published(
    env: dict[str, str],
    post_id: str,
    *,
    max_wait: int = 600,
    interval: int = 30,
) -> dict:
    deadline = time.time() + max_wait
    last = fetch_zernio_post(env, post_id)
    while time.time() < deadline:
        post = last.get("post", last)
        plat = (post.get("platforms") or [{}])[0]
        status = post.get("status") or plat.get("status")
        if status == "published" or plat.get("platformPostUrl"):
            return last
        if status not in {"scheduled", "publishing", "pending", None}:
            return last
        time.sleep(interval)
        last = fetch_zernio_post(env, post_id)
    return last


def publish_facebook(env: dict[str, str], content: str, cover_url: str, dry_run: bool) -> dict:
    payload: dict = {
        "content": content,
        "platforms": [{"platform": "facebook", "accountId": env["ZERNIO_FACEBOOK_ACCOUNT_ID"]}],
        "publishNow": True,
        "mediaItems": [{"url": cover_url, "type": "image"}],
    }
    if env.get("ZERNIO_PROFILE_ID"):
        payload["profileId"] = env["ZERNIO_PROFILE_ID"]

    if dry_run:
        return {"dry_run": True, "payload": payload}

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    return zernio_request(env, "POST", API_URL, body)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="01-panic-night")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--delete-cover",
        action="store_true",
        help="Remove social-covers/{topic}.jpg after Facebook publish (default: keep for VK MCP)",
    )
    args = parser.parse_args()

    topic_dir = PROJECT_ROOT / "posts-emdr-memory" / "output" / args.topic
    md_path = topic_dir / "facebook-post.md"
    if not md_path.exists():
        raise SystemExit(f"Missing {md_path}")

    env = load_env()
    content = extract_post(md_path)
    cover_url = upload_cover(args.topic)

    result = publish_facebook(env, content, cover_url, args.dry_run)

    log: dict = {
        "topic": args.topic,
        "platform": "facebook",
        "chars": len(content),
        "cover_url": cover_url,
        "dry_run": args.dry_run,
    }

    exit_code = 0
    if not args.dry_run:
        post = result.get("post", {})
        plat = (post.get("platforms") or [{}])[0]
        post_id = post.get("_id")
        status = post.get("status") or plat.get("status")
        if status == "scheduled" and post_id:
            result = wait_for_published(env, post_id)
            post = result.get("post", result)
            plat = (post.get("platforms") or [{}])[0]
            status = post.get("status") or plat.get("status")
        log.update(
            {
                "zernio_post_id": post.get("_id") or post_id,
                "status": status,
                "platform_post_id": plat.get("platformPostId"),
                "platform_post_url": plat.get("platformPostUrl"),
                "page": plat.get("accountId", {}).get("displayName") if isinstance(plat.get("accountId"), dict) else None,
            }
        )
        if log.get("status") == "published":
            if args.delete_cover:
                delete_cover(args.topic)
        elif log.get("status") == "scheduled":
            log["note"] = "Meta transient error — Zernio auto-retry expected; verify-publish-run treats as partial"
            exit_code = 3
        else:
            raise SystemExit(f"Zernio gate failed: {json.dumps(result, ensure_ascii=False)}")

    log_path = topic_dir / "zernio-publish-log.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=2))
    if exit_code:
        raise SystemExit(exit_code)


if __name__ == "__main__":
    main()
