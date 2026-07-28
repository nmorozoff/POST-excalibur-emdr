#!/usr/bin/env python3
"""One-time login → save Playwright storage state (cookies b17 + TenChat).

Mac (headed):
  pip install -r requirements-browser-linux.txt
  playwright install chromium
  python3 scripts/browser_bootstrap_sessions.py --headed

Linux VPS (xvfb):
  xvfb-run python3 scripts/browser_bootstrap_sessions.py --headed

Then copy linux-storage-state.json to VPS (or save directly on VPS).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import playwright_storage_state_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Playwright sessions for b17 + TenChat")
    parser.add_argument("--headed", action="store_true", help="Visible browser (needed for login)")
    parser.add_argument("--output", help="Override storage state path")
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("pip install playwright && playwright install chromium") from exc

    out = Path(args.output) if args.output else playwright_storage_state_path()
    out.parent.mkdir(parents=True, exist_ok=True)

    steps = [
        ("https://www.b17.ru/login.php", "b17.ru — войдите в аккаунт"),
        ("https://tenchat.ru/", "TenChat — войдите в аккаунт"),
    ]

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=not args.headed)
        context = browser.new_context()
        page = context.new_page()
        for url, prompt in steps:
            print(f"\n→ {prompt}\n  URL: {url}\n")
            page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            input("Когда залогинены, нажмите Enter… ")
        context.storage_state(path=str(out))
        browser.close()

    print(f"\n✓ Storage state saved: {out}")
    print("На VPS: scp этот файл в posts-emdr-memory/browser/ (файл в .gitignore — не коммитить)")


if __name__ == "__main__":
    main()
