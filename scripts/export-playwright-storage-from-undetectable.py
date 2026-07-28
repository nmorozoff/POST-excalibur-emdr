#!/usr/bin/env python3
"""Export Playwright storage state from a running Undetectable profile (CDP).

Usage (Mac, Profile1 already logged in to b17 + TenChat):
  1. Start Profile1 in Undetectable
  2. python3 scripts/export-playwright-storage-from-undetectable.py
  3. scp posts-emdr-memory/browser/linux-storage-state.json → VPS
"""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import playwright_storage_state_path, undetectable_config


def _profile_debug_port() -> str:
    cfg = undetectable_config()
    base = cfg["base_url"].rstrip("/")
    profile_id = cfg.get("profile_id", "")
    if not profile_id:
        raise SystemExit("UNDETECTABLE_PROFILE_ID not set in b17.env.local / tenchat.env.local")
    req = urllib.request.Request(
        f"{base}/profile/start/{profile_id}",
        method="GET",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode())
    except urllib.error.HTTPError as exc:
        body = exc.read().decode(errors="replace")
        raise SystemExit(f"Undetectable start failed: {body}") from exc
    port = (data.get("data") or {}).get("debug_port") or ""
    if not port:
        raise SystemExit(f"No debug_port in Undetectable response: {data}")
    return str(port)


def main() -> None:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("pip install playwright && playwright install chromium") from exc

    port = _profile_debug_port()
    cdp_url = f"http://127.0.0.1:{port}"
    out = playwright_storage_state_path()
    out.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.connect_over_cdp(cdp_url)
        if not browser.contexts:
            raise SystemExit("No browser context in Undetectable profile")
        context = browser.contexts[0]
        pages = context.pages
        if pages:
            for url in (
                "https://www.b17.ru/my_blog.php",
                "https://tenchat.ru/editor",
            ):
                page = pages[0]
                page.goto(url, wait_until="domcontentloaded", timeout=120_000)
                page.wait_for_timeout(1500)
        context.storage_state(path=str(out))
        browser.close()

    print(json.dumps({"ok": True, "storage_state": str(out), "cdp": cdp_url}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
