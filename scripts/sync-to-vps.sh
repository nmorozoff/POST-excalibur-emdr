#!/usr/bin/env bash
# Синхронизация репо Mac → Linux VPS (пока нет git pull на сервере).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VPS_HOST="${VPS_HOST:-ubuntu@195.209.210.45}"
SSH_KEY="${VPS_SSH_KEY:-$HOME/Documents/privatekey-1099880.pem}"
REMOTE_DIR="${VPS_REMOTE_DIR:-~/POST-excalibur-emdr}"

rsync -az --delete \
  --exclude '.venv-browser' \
  --exclude '__pycache__' \
  --exclude '.git' \
  --exclude 'posts-emdr-memory/browser/*.json' \
  --exclude 'posts-emdr-memory/*.env.local' \
  -e "ssh -i $SSH_KEY -o StrictHostKeyChecking=accept-new" \
  "$ROOT/" "$VPS_HOST:$REMOTE_DIR/"

echo "✓ Synced → $VPS_HOST:$REMOTE_DIR"
echo "  На VPS: source .venv-browser/bin/activate && python3 scripts/publish-browser-deferred.py --list"
