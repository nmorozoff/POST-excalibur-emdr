#!/usr/bin/env python3
"""Check TenChat editor reachable via residential proxy (VPS, no Mac)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_playwright_utils import residential_proxy_configured, tenchat_proxy_prefix
from posts_emdr_env import browser_backend_name, playwright_storage_state_path


def check_tenchat_access() -> dict:
    if browser_backend_name() != "playwright":
        return {"ok": False, "error": "BROWSER_BACKEND must be playwright"}

    state = playwright_storage_state_path()
    if not state.is_file():
        return {"ok": False, "error": f"missing storage state: {state}"}

    prefix = tenchat_proxy_prefix()
    if not prefix:
        return {
            "ok": False,
            "error": "no_residential_proxy",
            "hint": "Set B17_PROXY_SERVER (ASocks) — TenChat на VPS только через residential",
        }

    from playwright.sync_api import sync_playwright
    from browser_playwright_utils import _proxy_dict

    proxy = _proxy_dict(prefix)
    result: dict = {"proxy": bool(proxy), "url": "https://tenchat.ru/editor"}

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True, proxy=proxy)
        context = browser.new_context(storage_state=str(state), locale="ru-RU")
        page = context.new_page()
        try:
            page.goto("https://tenchat.ru/editor", wait_until="networkidle", timeout=90_000)
            page.wait_for_timeout(6000)
        except Exception as exc:
            result.update({"ok": False, "error": str(exc)})
            browser.close()
            return result

        html = page.content().lower()
        title = page.title().lower()
        editor_count = page.locator("#tc-editor .ql-editor, #tc-editor [contenteditable='true']").count()

        if "ошибка сервера" in html or "500" in title:
            result.update(
                {
                    "ok": False,
                    "blocked": True,
                    "reason": "server_500",
                    "hint": (
                        "TenChat cookies с Mac несовместимы с VPS. "
                        "Один раз на VPS: xvfb-run python3 scripts/browser_bootstrap_sessions.py "
                        "--headed --tenchat-only --use-proxy"
                    ),
                }
            )
        elif "авториза" in title or "sign-in" in page.url.lower():
            result.update(
                {
                    "ok": False,
                    "blocked": False,
                    "reason": "auth_required",
                    "hint": "Перелогин TenChat на VPS (bootstrap --tenchat-only --use-proxy)",
                }
            )
        elif editor_count > 0:
            result.update({"ok": True, "editor": True, "final_url": page.url})
        else:
            result.update(
                {
                    "ok": False,
                    "reason": "editor_not_found",
                    "final_url": page.url,
                    "hint": "Редактор не загрузился — bootstrap TenChat на VPS",
                }
            )
        browser.close()

    return result


def main() -> None:
    result = check_tenchat_access()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("ok") else 2)


if __name__ == "__main__":
    main()
