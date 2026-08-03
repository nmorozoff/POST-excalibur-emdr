#!/usr/bin/env bash
# Полный автономный worker на Linux VPS (без Mac).
set -euo pipefail

ROOT="${POSTS_EMDR_ROOT:-$HOME/POST-excalibur-emdr}"
cd "$ROOT"

if [[ -f .venv-browser/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv-browser/bin/activate
fi

# Git pull (private repo — нужен github.env.local с GITHUB_TOKEN)
if [[ -f posts-emdr-memory/github.env.local ]]; then
  # shellcheck disable=SC1091
  set -a
  source posts-emdr-memory/github.env.local
  set +a
fi
if [[ -d .git ]] && [[ -n "${GITHUB_TOKEN:-}" ]]; then
  git pull "https://${GITHUB_TOKEN}@github.com/nmorozoff/POST-excalibur-emdr.git" main 2>/dev/null || \
    git pull --ff-only origin main 2>/dev/null || true
elif [[ -d .git ]]; then
  git pull --ff-only origin main 2>/dev/null || true
fi

python3 scripts/browser_ensure_sessions.py --refresh || echo "WARN: session refresh failed (continue; per-platform checks apply)"
python3 scripts/asocks_sync_proxy.py --target telegram || true
python3 scripts/asocks_sync_proxy.py --target b17 || true
python3 scripts/fetch-topic-cover.py --all-pending
python3 scripts/publish-browser-deferred.py --submit --finish --git-push
