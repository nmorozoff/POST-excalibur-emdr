# Фаза 3 без Mac — полностью автономно на VPS

Цель: после cloud automation (Макс, TG, VK, FB) **b17 + TenChat** публикуются на VPS **без участия Mac** и без GUI-диалогов.

## Архитектура

```
Cloud automation
  → git push (артефакты + browser-local-handoff.md)
  → webhook POST на VPS (мгновенно)  ИЛИ  cron 10:00 и 17:00 MSK
VPS Playwright (headless)
  → b17 через residential proxy
  → TenChat напрямую (cookies)
  → реестры + очередь → git push
```

## Что нужно один раз

### 1. Storage state (cookies b17 + TenChat)

Уже сделано для sb-03. При протухании TenChat (SMS) — повторить экспорт:

```bash
# Mac: Profile1 запущен в Undetectable
source .venv-browser/bin/activate
python3 scripts/export-playwright-storage-from-undetectable.py
scp posts-emdr-memory/browser/linux-storage-state.json ubuntu@195.209.210.45:~/POST-excalibur-emdr/posts-emdr-memory/browser/
```

Дальше VPS **сам продлевает** cookies при каждой публикации (`browser_ensure_sessions.py`).

### 2. Residential proxy для b17 (обязательно)

b17.ru **блокирует IP датацентра** VPS (`195.209.210.45`).

На VPS в `posts-emdr-memory/browser.env.local`:

```env
B17_PROXY_SERVER=http://USER:PASS@host:port
# или отдельно:
# B17_PROXY_SERVER=http://host:port
# B17_PROXY_USERNAME=user
# B17_PROXY_PASSWORD=pass
```

Нужен **резидентский RU proxy** (не datacenter). Без proxy b17 на VPS не работает.

### ASocks (рекомендуется)

1. В `browser.env.local`:
   ```env
   ASOCKS_API_BASE=https://api.asocks.com
   ASOCKS_API_KEY=ваш_ключ
   ASOCKS_PORT_NAME=b17-emdr
   ```
2. Синхронизация логина/хоста/порта из API:
   ```bash
   python3 scripts/asocks_sync_proxy.py
   python3 scripts/asocks_check.py
   ```
3. В кабинете [ASocks](https://docs.asocks.com/ru/):
   - **Whitelist** → IP VPS: `195.209.210.45`
   - Тип авторизации порта: **Password Authorization**
   - Проверить, что есть **трафик** (`all_available_traffic` > 0 в `asocks_check.py`)

Порт ASocks обычно **9999**, не 443. API whitelist в документации может быть недоступен — whitelist только через кабинет.

### 3. GitHub token для `git pull` на VPS

```bash
cp posts-emdr-memory/github.env.example posts-emdr-memory/github.env.local
# GITHUB_TOKEN = fine-grained PAT, read access to POST-excalibur-emdr
```

### 4. Webhook secret (мгновенный запуск после cloud)

```bash
# В browser.env.local или /etc/environment на VPS:
VPS_WEBHOOK_SECRET=длинный-случайный-секрет
```

## Установка на VPS

```bash
cd ~/POST-excalibur-emdr
./scripts/install-linux-browser-worker.sh ~/POST-excalibur-emdr
# Заполнить browser.env.local (proxy!) и github.env.local
python3 scripts/browser_verify_sessions.py
python3 scripts/check-b17-ip-access.py   # ok после настройки proxy
```

### Cron (fallback, если webhook не сработал)

```cron
0 10,17 * * * /home/ubuntu/POST-excalibur-emdr/scripts/run-linux-browser-worker.sh >> /var/log/posts-emdr-browser.log 2>&1
0 4 * * * cd /home/ubuntu/POST-excalibur-emdr && .venv-browser/bin/python3 scripts/browser_ensure_sessions.py --refresh >> /var/log/posts-emdr-sessions.log 2>&1
```

### Webhook-сервер (рекомендуется)

```bash
# systemd или screen:
export VPS_WEBHOOK_SECRET=...
cd ~/POST-excalibur-emdr && source .venv-browser/bin/activate
python3 scripts/vps-webhook-server.py --port 8787
```

Открыть порт 8787 в firewall только для Cursor cloud IPs или через nginx + TLS.

## Cloud automation — последний шаг

После VK MCP и реестров:

```bash
git add posts-emdr-memory/output/{topic}/ posts-emdr-memory/profile/*-posts-registry.md
git commit -m "cloud: {topic} phase 1-2"
git push origin main

curl -fsS -X POST "http://195.209.210.45:8787/publish" \
  -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"topic":"{topic_id}"}'
```

Если webhook недоступен — cron подхватит в **10:00** или **17:00** MSK (ближайший слот).

## Webhook недоступен (Connection reset / refused)

**Симптом с Cloud:** `curl http://195.209.210.45:8787/health` → `Connection reset by peer` или timeout; `trigger-vps-webhook.py` → `vps_down: true`.

**Диагностика на VPS (SSH):**

```bash
sudo systemctl status posts-emdr-webhook
sudo journalctl -u posts-emdr-webhook -n 80 --no-pager
ss -tlnp | grep 8787
curl -fsS http://127.0.0.1:8787/health
```

**Восстановление:**

```bash
cd ~/POST-excalibur-emdr
git fetch origin main && git reset --hard origin/main
sudo systemctl restart posts-emdr-webhook
sleep 2
curl -fsS http://127.0.0.1:8787/health
```

Если health OK локально, но с Cloud — reset: проверить firewall / ufw (порт 8787), conntrack, не занят ли порт другим процессом.

**После восстановления (с Cloud или Mac, один раз на тему):**

```bash
python3 scripts/trigger-vps-webhook.py --topic sb-19-question-before-sleep
# ожидать HTTP 202
python3 scripts/verify-publish-run.py --topic sb-19-question-before-sleep
```

Ручной fallback на VPS (если webhook 202, но worker не завершился):

```bash
cd ~/POST-excalibur-emdr && source .venv-browser/bin/activate
python3 scripts/vps_publish_guard.py run -- \
  python3 scripts/publish-browser-deferred.py --topic sb-19-question-before-sleep --submit --finish --git-push
```

## Почему Mac больше не нужен

| Проблема Mac | Решение VPS |
|--------------|-------------|
| GUI «разрешить доступ» Undetectable | Playwright headless, без GUI |
| Ручной bootstrap | Storage state + auto-refresh |
| b17 timeout с Mac | VPS + residential proxy |
| Нужно быть за компом | cron + webhook 24/7 |

## TenChat и SMS

TenChat логинится по SMS. **Полный re-login без SMS невозможен.**  
Практика: cookies живут месяцами при регулярных визитах (`browser_ensure_sessions`). При редком протухании — один раз экспорт storage с Mac (5 минут).

## Проверка

```bash
python3 scripts/browser_bridge_health.py
python3 scripts/check-b17-ip-access.py
python3 scripts/publish-browser-deferred.py --list
python3 scripts/publish-browser-deferred.py --topic sb-04-... --submit --dry-run
```

## Mac phase 3 — только fallback

`./scripts/run-mac-browser-phase3.sh` — если proxy ещё не настроен.
