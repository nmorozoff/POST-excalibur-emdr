#!/usr/bin/env python3
"""Check browser backend (Playwright on Linux or Undetectable on Mac)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_backend import browser_health


def main() -> None:
    report = browser_health()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report.get("ok"):
        print(f"Browser bridge ({report.get('backend')}): OK", file=sys.stderr)
        sys.exit(0)
    print(
        "Browser bridge: FAIL — Linux: browser-linux-vps-setup.md | Mac: Undetectable",
        file=sys.stderr,
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
