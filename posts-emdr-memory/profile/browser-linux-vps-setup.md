# b17 + TenChat на Linux VPS (без Windows / Undetectable)

Используйте **тот же Ubuntu VPS**, что и CRM («CRM и Онлайн запись»): Twenty + docker + nginx уже крутятся — для постов достаточно **cron + Playwright**, отдельный сервер не нужен.

## Схема

```
Cloud Agent (фазы 1–2)  →  git push / handoff
         ↓
Linux VPS (cron 10 мин)  →  git pull → cover → publish-browser-deferred.py
         ↓
Playwright + Chromium (headless)  →  b17.ru + TenChat
```

Mac и Windows **не участвуют**.

## 1. Пакеты на VPS

```bash
sudo apt update
sudo apt install -y python3-venv python3-pip git xvfb

cd ~
git clone https://github.com/nmorozoff/POST-excalibur-emdr.git
cd POST-excalibur-emdr

python3 -m venv .venv-browser
source .venv-browser/bin/activate
pip install -r requirements-browser-linux.txt
playwright install chromium
playwright install-deps chromium
```

## 2. Конфиг

```bash
cp posts-emdr-memory/browser.env.example posts-emdr-memory/browser.env.local
```

`browser.env.local`:

```env
BROWSER_BACKEND=playwright
PLAYWRIGHT_STORAGE_STATE=posts-emdr-memory/browser/linux-storage-state.json
PLAYWRIGHT_HEADLESS=1
```

## 3. Логин b17 + TenChat (один раз)

**Вариант A — экспорт из Undetectable на Mac (рекомендуется, если Profile1 уже залогинен):**

```bash
# Profile1 запущен в Undetectable
source .venv-browser/bin/activate   # Mac: python3 -m venv .venv-browser && pip install -r requirements-browser-linux.txt
python3 scripts/export-playwright-storage-from-undetectable.py
scp posts-emdr-memory/browser/linux-storage-state.json ubuntu@ВАШ_VPS:~/POST-excalibur-emdr/posts-emdr-memory/browser/
```

**Вариант B — ручной bootstrap (headed):**

```bash
pip install -r requirements-browser-linux.txt
playwright install chromium
python3 scripts/browser_bootstrap_sessions.py --headed
scp posts-emdr-memory/browser/linux-storage-state.json ubuntu@ВАШ_VPS:~/POST-excalibur-emdr/posts-emdr-memory/browser/
```

**Вариант C — прямо на VPS (нужен дисплей/xvfb):**

```bash
xvfb-run python3 scripts/browser_bootstrap_sessions.py --headed
```

Файл `linux-storage-state.json` — **секрет** (cookies). В git не коммитить.

### ⚠️ b17.ru блокирует IP VPS

На VPS `195.209.210.45` b17 отдаёт «IP временно заблокирован». **b17 публикуется с Mac** через Undetectable:

```bash
./scripts/run-mac-browser-phase3.sh sb-03-body-before-mind
# или после cloud: ./scripts/run-mac-browser-phase3.sh --pending
```

TenChat с VPS Playwright возможен (после storage state); при сбое тематик — тоже Mac phase 3.

## 4. Проверка

```bash
source .venv-browser/bin/activate
python3 scripts/browser_bridge_health.py
# → "backend": "playwright", "ok": true
```

## 5. Cron (worker)

Скрипт `scripts/run-linux-browser-worker.sh` делает всё:

1. `git pull`
2. `fetch-topic-cover.py` — обложки с сайта
3. `publish-browser-deferred.py --submit --finish --git-push` — b17, TenChat, реестры, очередь

```bash
chmod +x scripts/install-linux-browser-worker.sh scripts/run-linux-browser-worker.sh
./scripts/install-linux-browser-worker.sh ~/POST-excalibur-emdr
```

Cron:

```bash
*/10 * * * * /home/ubuntu/POST-excalibur-emdr/scripts/run-linux-browser-worker.sh >> /var/log/posts-emdr-browser.log 2>&1
```

На VPS нужен `git push` (deploy key или PAT) — чтобы реестры и очередь вернулись в репо.

## 6. Проверка сессий

```bash
python3 scripts/browser_verify_sessions.py
```

1. Cloud: контент + `publish-topic.py` (Макс, TG, FB, VK handoff).
2. Cloud MCP: VK ×2.
3. Commit/push артефактов (`output/{topic}/*.md`, handoff).
4. VPS cron подхватывает `browser-local-handoff.md` и публикует b17/TenChat.

## 7. CRM на том же VPS

- CRM (docker) и Playwright **не конфликтуют**: разные процессы.
- RAM: при 4 GB следите за пиками (Chromium ~300–500 MB). Публикация 1–2 раза в день — нормально.
- Не открывайте Playwright API наружу — только локальный cron.

## 8. Mac локально (fallback)

`BROWSER_BACKEND=undetectable` + Undetectable — как раньше.

## Файлы

| Файл | Роль |
|------|------|
| `browser.env.local` | `BROWSER_BACKEND=playwright` |
| `browser/linux-storage-state.json` | cookies (секрет) |
| `scripts/publish-browser-deferred.py` | cron worker |
| `scripts/fetch-topic-cover.py` | cover с сайта |
| `scripts/browser_bootstrap_sessions.py` | первичный логин |

См. также: `profile/cloud-publish-phases.md` (фаза 3).
