#!/usr/bin/env python3
"""Заполнить b17 для короткого поста (одна команда).

Usage:
  python scripts/publish-sb-platforms.py --topic sb-01-background-anxiety
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser(description="b17 — заполнить форму в Playwright")
    parser.add_argument("--topic", required=True)
    args = parser.parse_args()

    cmd = ["python3", str(PROJECT_ROOT / "scripts" / "publish-b17-blog.py"), "--topic", args.topic]
    proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr, file=sys.stderr)
        raise SystemExit(proc.returncode)
    result = json.loads(proc.stdout)
    print(json.dumps({"topic": args.topic, "platforms": [result]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
