#!/usr/bin/env bash
# Локальный cron Posts EMDR — 12:00 MSK (launchd).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
export BROWSER_BACKEND=undetectable
export PATH="/usr/local/bin:/opt/homebrew/bin:${PATH:-/usr/bin:/bin}"
LOG_DIR="${POSTS_EMDR_LOG_DIR:-$ROOT/posts-emdr-memory/logs}"
mkdir -p "$LOG_DIR"
STAMP="$(date +%Y%m%d-%H%M%S)"
LOG="$LOG_DIR/local-publish-$STAMP.log"
exec >>"$LOG" 2>&1
echo "=== local-publish $STAMP ==="
python3 scripts/vps_publish_guard.py run -- \
  python3 scripts/run-local-publish.py --worker
echo "=== done exit $? ==="
