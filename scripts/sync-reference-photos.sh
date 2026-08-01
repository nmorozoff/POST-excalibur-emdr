#!/usr/bin/env bash
# Копирует 8 портретов из ~/Desktop/РЕФЕРЕНСЫ → assets/reference/portrait-01…08.jpg
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${REFERENCE_SOURCE_DIR:-$HOME/Desktop/РЕФЕРЕНСЫ}"
DST="$ROOT/posts-emdr-memory/assets/reference"
MAX_EDGE="${REFERENCE_MAX_EDGE:-1600}"

mkdir -p "$DST"
python3 -c "
import json
from pathlib import Path
m = json.loads(Path('$DST/manifest.json').read_text())
for s in m['slots']:
    print(s['source_hint'] + '|' + s['file'])
" | while IFS='|' read -r src_name dst_name; do
  src="$SRC/$src_name"
  dst="$DST/$dst_name"
  if [[ ! -f "$src" ]]; then
    echo "⚠ skip (нет файла): $src" >&2
    continue
  fi
  if command -v sips >/dev/null 2>&1; then
    sips -Z "$MAX_EDGE" "$src" --out "$dst" >/dev/null
  else
    cp "$src" "$dst"
  fi
  echo "✓ $dst_name ← $src_name"
done

if [[ -f "$DST/portrait-01.jpg" ]]; then
  cp "$DST/portrait-01.jpg" "$DST/portrait.jpg"
fi
echo "✓ Готово: $DST"
