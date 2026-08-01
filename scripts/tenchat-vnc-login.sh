#!/usr/bin/env bash
# TenChat login на VPS через браузер в окне на Mac (без XQuartz).
#
# Терминал 1 (VPS):
#   cd ~/POST-excalibur-emdr && source .venv-browser/bin/activate
#   ./scripts/tenchat-vnc-login.sh
#
# Терминал 2 (Mac, natala@192):
#   ssh -i ~/Documents/privatekey-1099880.pem -L 6080:127.0.0.1:6080 ubuntu@195.209.210.45
#
# Chrome на Mac: http://localhost:6080/vnc.html → Connect
# В окне: капча → Продолжить → SMS → в терминале 1 Enter / код в файл
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
DISPLAY_NUM="${DISPLAY_NUM:-99}"
export DISPLAY=":${DISPLAY_NUM}"
VNC_PORT="${VNC_PORT:-5900}"
WEB_PORT="${WEB_PORT:-6080}"

if ! command -v Xvfb >/dev/null; then
  echo "Установите: sudo apt install -y xvfb" >&2
  exit 1
fi

if ! command -v x11vnc >/dev/null; then
  echo "→ Устанавливаю x11vnc novnc…"
  sudo apt-get update -qq
  sudo apt-get install -y x11vnc novnc python3-websockify
fi

cleanup() {
  jobs -p | xargs -r kill 2>/dev/null || true
}
trap cleanup EXIT

if ! xdpyinfo -display "$DISPLAY" >/dev/null 2>&1; then
  echo "→ Xvfb $DISPLAY"
  Xvfb "$DISPLAY" -screen 0 1280x1024x24 &
  sleep 2
fi

echo "→ x11vnc (только localhost)"
x11vnc -display "$DISPLAY" -localhost -nopw -rfbport "$VNC_PORT" -shared -forever -noxdamage &
sleep 1

NOVNC_WEB="/usr/share/novnc"
if [[ ! -d "$NOVNC_WEB" ]]; then
  NOVNC_WEB="/usr/share/novnc"
fi
echo "→ websockify :$WEB_PORT"
websockify --web="$NOVNC_WEB" "$WEB_PORT" "127.0.0.1:$VNC_PORT" &
sleep 1

cat <<EOF

══════════════════════════════════════════════════════════
  На Mac откройте ВТОРОЙ терминал (natala@192):

    ssh -i ~/Documents/privatekey-1099880.pem -L 6080:127.0.0.1:6080 ubuntu@195.209.210.45

  В Chrome на Mac:  http://localhost:6080/vnc.html
  Кнопка Connect → увидите окно браузера на сервере.

  Телефон (опционально): posts-emdr-memory/tenchat-bootstrap.env.local
══════════════════════════════════════════════════════════

EOF

source .venv-browser/bin/activate 2>/dev/null || true

PHONE_FILE="$ROOT/posts-emdr-memory/tenchat-bootstrap.env.local"
if [[ -f "$PHONE_FILE" ]]; then
  # shellcheck disable=SC1090
  source <(grep -E '^TENCHAT_PHONE=' "$PHONE_FILE" | sed 's/^/export /')
fi

cat <<'EOF2'

Сейчас откройте в Chrome на Mac:  http://localhost:6080/vnc.html  → Connect

В окне VNC сделайте ВСЁ сами:
  1) галочки согласия
  2) телефон (может быть уже введён)
  3) капча «Я не робот»
  4) Продолжить → код из SMS → войти
  5) дождитесь ленты TenChat

Только ПОТОМ вернитесь сюда и нажмите Enter.

EOF2

python3 scripts/browser_bootstrap_sessions.py --headed --tenchat-only --use-proxy "$@"

echo ""
echo "Проверка:"
python3 scripts/check-tenchat-access.py
