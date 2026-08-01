#!/usr/bin/env python3
"""Debug TenChat editor DOM (VPS)."""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_playwright_utils import playwright_session

with playwright_session(headless=True, proxy_prefix="") as (_pw, _b, ctx):
    page = ctx.new_page()
    page.goto("https://tenchat.ru/editor", wait_until="networkidle", timeout=120_000)
    for wait in (5, 10, 15, 25):
        time.sleep(5)
        counts = {
            "tc-editor": page.locator("#tc-editor").count(),
            "ql-editor": page.locator(".ql-editor").count(),
            "iframe": page.locator("iframe").count(),
            "textarea": page.locator("textarea").count(),
            "contenteditable": page.locator("[contenteditable]").count(),
        }
        print(f"after ~{wait}s:", counts, "url:", page.url)
    html = page.content()
    low = html.lower()
    if "500" in html and "ошибка сервера" in low:
        print("SERVER_ERROR_500: TenChat editor SPA не загрузился (500)")
    for kw in ("tc-editor", "ql-editor", "quill", "prosemirror", "editor"):
        print(kw, kw in low)
    ids = set(re.findall(r'id="([^"]{3,60})"', html))
    for i in sorted(x for x in ids if any(k in x.lower() for k in ("edit", "tc", "post", "quill"))):
        print("id:", i)
    page.screenshot(path="/tmp/tenchat-editor.png", full_page=True)
    print("screenshot /tmp/tenchat-editor.png")
