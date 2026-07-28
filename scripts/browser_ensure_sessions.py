#!/usr/bin/env python3
"""Keep b17 + TenChat cookies alive on VPS (no Mac, no GUI).

Run before publish (cron/worker) or daily:
  python3 scripts/browser_ensure_sessions.py
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_playwright_utils import b17_proxy_configured, playwright_session
from posts_emdr_env import browser_backend_name, load_env, playwright_storage_state_path


def _page_ok(url: str, html: str, final_url: str) -> bool:
    low = (html + final_url).lower()
    if "временно заблокирован" in low or "b17_guard" in low:
        return False
    if "login" in final_url.lower() and "my_blog" not in final_url.lower():
        return False
    if "auth/sign-in" in final_url.lower():
        return False
    if "tenchat.ru/editor" in final_url and "editor" in final_url.lower():
        return True
    if "my_blog.php" in final_url or "mod=edit" in final_url:
        return "#form_name" in html or "tinymce" in low or "my_blog" in final_url
    return "login" not in low


def ensure_sessions(*, refresh: bool = False) -> dict:
    if browser_backend_name() != "playwright":
        return {"ok": False, "error": "BROWSER_BACKEND must be playwright on VPS"}

    try:
        load_env("browser.env.local")
    except SystemExit:
        pass

    state = playwright_storage_state_path()
    if not state.is_file():
        return {
            "ok": False,
            "error": f"missing storage state: {state}",
            "hint": "One-time: export from Undetectable Mac → scp to VPS browser/",
        }

    checks: dict[str, object] = {"storage_state": str(state), "sites": {}}
    b17_blocked_no_proxy = False

    with playwright_session(proxy_prefix="B17_") as (_pw, _browser, context):
        page = context.new_page()
        for key, url, proxy_prefix in (
            ("b17", "https://www.b17.ru/my_blog.php?mod=edit", "B17_"),
            ("tenchat", "https://tenchat.ru/editor", ""),
        ):
            if key == "b17" and not b17_proxy_configured():
                probe = __import__("check_b17_ip_access", fromlist=["check_b17_access"]).check_b17_access()
                if probe.get("blocked"):
                    b17_blocked_no_proxy = True
                    checks["sites"][key] = {
                        "ok": False,
                        "skipped": True,
                        "reason": "datacenter_ip_blocked",
                        "hint": "Set B17_PROXY_SERVER in browser.env.local (residential RU proxy)",
                    }
                    continue
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=120_000)
                time.sleep(2 if not refresh else 4)
                html = page.content()
                ok = _page_ok(url, html, page.url)
                checks["sites"][key] = {"ok": ok, "url": page.url}
            except Exception as exc:
                checks["sites"][key] = {"ok": False, "error": str(exc)}

    all_ok = all(
        v.get("ok") for v in checks["sites"].values() if isinstance(v, dict) and not v.get("skipped")
    )
    checks["ok"] = all_ok and not b17_blocked_no_proxy
    if b17_blocked_no_proxy:
        checks["b17_proxy_required"] = True
    return checks


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh/verify Playwright sessions for b17+TenChat")
    parser.add_argument("--refresh", action="store_true", help="Longer page wait (session keeper)")
    args = parser.parse_args()

    result = ensure_sessions(refresh=args.refresh)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result.get("ok"):
        sys.exit(2)


if __name__ == "__main__":
    main()
