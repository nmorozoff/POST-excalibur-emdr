#!/usr/bin/env python3
"""Заполнить b17 + TenChat для короткого поста (одна команда).

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
    parser = argparse.ArgumentParser(description="b17 + TenChat — заполнить формы в Undetectable")
    parser.add_argument("--topic", required=True)
    args = parser.parse_args()

    scripts = [
        ["python3", str(PROJECT_ROOT / "scripts" / "publish-b17-blog.py"), "--topic", args.topic],
        ["python3", str(PROJECT_ROOT / "scripts" / "publish-tenchat-post.py"), "--topic", args.topic],
    ]
    results = []
    for cmd in scripts:
        proc = subprocess.run(cmd, cwd=PROJECT_ROOT, capture_output=True, text=True)
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            raise SystemExit(proc.returncode)
        results.append(json.loads(proc.stdout))

    print(json.dumps({"topic": args.topic, "platforms": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
