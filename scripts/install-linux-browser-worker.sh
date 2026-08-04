#!/usr/bin/env bash
# Установка Playwright browser worker на Ubuntu VPS (рядом с CRM).
set -euo pipefail

ROOT="${1:-$HOME/POST-excalibur-emdr}"
REPO="${POSTS_EMDR_REPO:-https://github.com/nmorozoff/POST-excalibur-emdr.git}"

echo "==> Posts EMDR browser worker → $ROOT"

if [[ ! -d "$ROOT/.git" ]] && [[ ! -f "$ROOT/scripts/publish-topic.py" ]]; then
  git clone "$REPO" "$ROOT"
fi

cd "$ROOT"
if [[ -d .git ]]; then
  git pull --ff-only || true
fi

sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip git xvfb libnss3 libatk-bridge2.0-0 libdrm2 \
  libxkbcommon0 libgbm1 libasound2t64 || \
sudo apt-get install -y -qq python3-venv python3-pip git xvfb libnss3 libatk-bridge2.0-0 libdrm2 \
  libxkbcommon0 libgbm1 libasound2

python3 -m venv .venv-browser
# shellcheck disable=SC1091
source .venv-browser/bin/activate
pip install -q -U pip
pip install -q -r requirements-browser-linux.txt
playwright install chromium
playwright install-deps chromium || true

if [[ ! -f posts-emdr-memory/browser.env.local ]]; then
  cp posts-emdr-memory/browser.env.example posts-emdr-memory/browser.env.local
fi

mkdir -p posts-emdr-memory/browser
chmod +x scripts/run-linux-browser-worker.sh

echo ""
echo "✓ Установлено. Дальше:"
echo "  1) xvfb-run python3 scripts/browser_bootstrap_sessions.py --headed   # логин b17 + TenChat"
echo "  2) python3 scripts/browser_verify_sessions.py"
echo "  3) crontab: 0 10,17 * * * $ROOT/scripts/run-linux-browser-worker.sh >> /var/log/posts-emdr-browser.log 2>&1"
