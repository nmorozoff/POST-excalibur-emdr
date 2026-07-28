#!/usr/bin/env python3
"""Check if b17.ru is reachable from current host (VPS IP may be blocked)."""

from __future__ import annotations

import json
import sys
import urllib.request


def b17_ip_blocked(html: str) -> bool:
    low = html.lower()
    return "временно заблокирован" in low or "b17_guard" in low


def check_b17_access() -> dict:
    url = "https://www.b17.ru/my_blog.php?mod=edit"
    req = urllib.request.Request(url, headers={"User-Agent": "PostsEMDR-b17-check/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            html = resp.read(4000).decode("utf-8", errors="replace")
    except Exception as exc:
        return {"ok": False, "blocked": False, "error": str(exc), "url": url}
    blocked = b17_ip_blocked(html)
    return {"ok": not blocked, "blocked": blocked, "url": url, "hint": "use Mac run-mac-browser-phase3.sh" if blocked else None}


def main() -> None:
    result = check_b17_access()
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("ok") else 2)


if __name__ == "__main__":
    main()
