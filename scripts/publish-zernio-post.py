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
import re
import ssl
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
    text = md_path.read_text(encoding="utf-8")
    m = re.search(r"## Текст поста\n\n(.*)", text, re.S)
    if not m:
        raise SystemExit(f"Cannot parse post from {md_path}")
    return m.group(1).strip()


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
    req = urllib.request.Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {env['ZERNIO_API_KEY']}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = e.read().decode()
        raise SystemExit(f"Zernio API HTTP {e.code}: {err}") from e


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", default="01-panic-night")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--skip-cover-cleanup", action="store_true")
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

    if not args.dry_run:
        post = result.get("post", {})
        plat = (post.get("platforms") or [{}])[0]
        log.update(
            {
                "zernio_post_id": post.get("_id"),
                "status": post.get("status") or plat.get("status"),
                "platform_post_id": plat.get("platformPostId"),
                "platform_post_url": plat.get("platformPostUrl"),
                "page": plat.get("accountId", {}).get("displayName") if isinstance(plat.get("accountId"), dict) else None,
            }
        )
        if log.get("status") != "published":
            raise SystemExit(f"Zernio gate failed: {json.dumps(result, ensure_ascii=False)}")
        if not args.skip_cover_cleanup:
            delete_cover(args.topic)

    log_path = topic_dir / "zernio-publish-log.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(log, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
