#!/usr/bin/env bash
# Полный автономный worker на Linux VPS (без Mac).
set -euo pipefail

ROOT="${POSTS_EMDR_ROOT:-$HOME/POST-excalibur-emdr}"
cd "$ROOT"

if [[ -f .venv-browser/bin/activate ]]; then
  # shellcheck disable=SC1091
  source .venv-browser/bin/activate
fi

run_steps() {
  python3 scripts/materialize_vps_env.py || true
  python3 scripts/browser_ensure_sessions.py --refresh || echo "WARN: session refresh failed (continue; per-platform checks apply)"
  python3 scripts/asocks_sync_proxy.py --target telegram || true
  python3 scripts/asocks_sync_proxy.py --target b17 || true
  python3 scripts/fetch-topic-cover.py --all-pending
  python3 scripts/retry-b17-drafts.py --limit 1 || true
  python3 scripts/publish-browser-deferred.py --submit --finish --git-push
}

# Nested call from vps_publish_guard / webhook: lock + git pull already done.
if [[ "${POSTS_EMDR_PUBLISH_LOCKED:-}" == "1" ]]; then
  run_steps
  exit 0
fi

# Exclusive flock + git pull, then same steps (prevents TG double-send vs webhook).
exec python3 scripts/vps_publish_guard.py run -- "$ROOT/scripts/run-linux-browser-worker.sh"