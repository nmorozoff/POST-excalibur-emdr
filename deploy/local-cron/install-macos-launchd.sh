#!/usr/bin/env bash
# Установить launchd: каждый день 12:00 Europe/Moscow
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PLIST_SRC="$ROOT/deploy/local-cron/ru.morozova.posts-emdr.plist"
PLIST_DST="$HOME/Library/LaunchAgents/ru.morozova.posts-emdr.plist"
chmod +x "$ROOT/scripts/local-publish-wrapper.sh"
sed "s|__PROJECT_ROOT__|$ROOT|g" "$PLIST_SRC" > "$PLIST_DST"
launchctl unload "$PLIST_DST" 2>/dev/null || true
launchctl load "$PLIST_DST"
echo "OK: $PLIST_DST"
echo "Логи: $ROOT/posts-emdr-memory/logs/local-publish-*.log"
echo "Проверка: launchctl list | grep morozova.posts-emdr"
