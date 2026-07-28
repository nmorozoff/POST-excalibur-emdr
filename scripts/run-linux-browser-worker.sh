#!/usr/bin/env bash
# Полный цикл browser worker на Linux VPS (cron).
set -euo pipefail

ROOT="${POSTS_EMDR_ROOT:-$HOME/POST-excalibur-emdr}"
cd "$ROOT"

if [[ -f .venv-browser/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv-browser/bin/activate
fi

if [[ -d .git ]]; then
  git pull --ff-only origin main 2>/dev/null || git pull --ff-only 2>/dev/null || true
fi

python3 scripts/fetch-topic-cover.py --all-pending
python3 scripts/publish-browser-deferred.py --submit --finish --git-push
