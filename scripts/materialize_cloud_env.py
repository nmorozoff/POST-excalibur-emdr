#!/usr/bin/env python3
"""Materialize posts-emdr-memory/*.env.local from Cloud Secrets (env vars).

Run at Cloud Agent install / before publish:
  python3 scripts/materialize_cloud_env.py
  python3 scripts/materialize_cloud_env.py --check
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import PROJECT_ROOT, materialize_env_files
from cloud_preflight import run_preflight

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true", help="Overwrite existing .env.local keys from env")
    parser.add_argument("--check", action="store_true", help="Run preflight after materialize")
    args = parser.parse_args()

    written = materialize_env_files(force=args.force)
    out = {"written": written, "project_root": str(PROJECT_ROOT)}
    print(json.dumps(out, ensure_ascii=False, indent=2))

    if args.check:
        report = run_preflight(strict=False)
        print(json.dumps(report, ensure_ascii=False, indent=2))
        if not report.get("ready_for_auto_publish"):
            sys.exit(2)
