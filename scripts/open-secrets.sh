#!/usr/bin/env bash
# Открывает файлы для вставки API-ключей в Cursor (macOS)
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MEMORY="$ROOT/posts-emdr-memory"

for f in max.env.local runware.env.local telegram.env.local КУДА-ВСТАВИТЬ-КЛЮЧИ.md; do
  path="$MEMORY/$f"
  if [[ -f "$path" ]]; then
    if command -v cursor >/dev/null 2>&1; then
      cursor "$path"
    else
      open -a Cursor "$path" 2>/dev/null || open "$path"
    fi
  fi
done

echo "Открыты файлы секретов в posts-emdr-memory/"
