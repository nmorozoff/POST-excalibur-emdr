#!/usr/bin/env python3
"""Проверка: сессии b17 + TenChat живы (Playwright storage state)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import browser_backend_name, browser_headless, playwright_storage_state_path


def main() -> None:
    if browser_backend_name() != "playwright":
        print(json.dumps({"ok": False, "error": "BROWSER_BACKEND is not playwright"}, indent=2))
        sys.exit(1)

    state = playwright_storage_state_path()
    if not state.is_file():
        print(json.dumps({"ok": False, "error": f"missing storage state: {state}"}, indent=2))
        sys.exit(1)

    from playwright.sync_api import sync_playwright

    checks: dict[str, object] = {"storage_state": str(state), "sites": {}}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=browser_headless())
        context = browser.new_context(storage_state=str(state))
        page = context.new_page()
        for key, url, must_not_contain in (
            ("b17", "https://www.b17.ru/my_blog.php", "login"),
            ("tenchat", "https://tenchat.ru/editor", "login"),
        ):
            page.goto(url, wait_until="domcontentloaded", timeout=90_000)
            page.wait_for_timeout(2000)
            final = page.url.lower()
            ok = must_not_contain not in final and "auth" not in final
            checks["sites"][key] = {"ok": ok, "url": page.url}
        browser.close()

    all_ok = all(v.get("ok") for v in checks["sites"].values())  # type: ignore[union-attr]
    checks["ok"] = all_ok
    print(json.dumps(checks, ensure_ascii=False, indent=2))
    if not all_ok:
        print("Сессия протухла — заново: python3 scripts/browser_bootstrap_sessions.py --headed", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
