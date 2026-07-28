#!/usr/bin/env bash
# Фаза 3 на Mac: b17 + TenChat через Undetectable (Profile1).
# Запускать после cloud publish, когда есть browser-local-handoff.md.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

TOPIC="${1:-}"
if [[ -z "$TOPIC" ]]; then
  echo "Usage: $0 <topic_id>" >&2
  echo "  или: $0 --pending  (первая тема с browser-local-handoff.md)" >&2
  exit 1
fi

if [[ "$TOPIC" == "--pending" ]]; then
  TOPIC="$(python3 scripts/publish-browser-deferred.py --list 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print((d.get('pending') or [''])[0])")"
  if [[ -z "$TOPIC" ]]; then
    echo "Нет pending browser handoff."
    exit 0
  fi
fi

echo "==> Phase 3 (Mac Undetectable): $TOPIC"

python3 scripts/fetch-topic-cover.py --topic "$TOPIC"
python3 scripts/publish-b17-blog.py --topic "$TOPIC" --submit
python3 scripts/publish-tenchat-post.py --topic "$TOPIC" --submit
python3 scripts/browser_worker_finish.py --topic "$TOPIC"

echo "✓ $TOPIC — b17 + TenChat опубликованы, очередь закрыта"
