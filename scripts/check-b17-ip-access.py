#!/usr/bin/env python3
"""Check if b17.ru is reachable (optionally via residential proxy)."""

from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_playwright_utils import b17_proxy_configured, b17_proxy_for_urllib


def b17_ip_blocked(html: str) -> bool:
    low = html.lower()
    return "временно заблокирован" in low or "b17_guard" in low


def check_b17_access() -> dict:
    url = "https://www.b17.ru/my_blog.php?mod=edit"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (compatible; PostsEMDR-b17-check/1.0)"},
    )
    proxies = b17_proxy_for_urllib()
    opener = urllib.request.build_opener()
    if proxies:
        opener = urllib.request.build_opener(urllib.request.ProxyHandler(proxies))
    try:
        with opener.open(req, timeout=45) as resp:
            html = resp.read(8000).decode("utf-8", errors="replace")
    except Exception as exc:
        return {
            "ok": False,
            "blocked": False,
            "error": str(exc),
            "url": url,
            "proxy": bool(proxies),
        }
    blocked = b17_ip_blocked(html)
    hint = None
    if blocked and not b17_proxy_configured():
        hint = "Set B17_PROXY_SERVER in browser.env.local (residential RU proxy)"
    elif blocked:
        hint = "Proxy configured but b17 still blocked — check proxy IP"
    return {
        "ok": not blocked,
        "blocked": blocked,
        "url": url,
        "proxy": bool(proxies),
        "hint": hint,
    }


def main() -> None:
    result = check_b17_access()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("ok") else 2)


if __name__ == "__main__":
    main()
