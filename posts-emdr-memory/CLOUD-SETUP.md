# Posts EMDR — Cloud Agent setup

Три фазы: см. **`profile/cloud-publish-phases.md`**.  
Утренний прогон: **`.cursor/posts-emdr-handoff.md`**.

## 0. Automation repository (критично)

Cursor automation для **Posts EMDR** MUST использовать репозиторий:

**`nmorozoff/POST-excalibur-emdr`**

Не **`nmorozoff/STATYA-excalibur-emdr`** (Excalibur BLOG): там другие Telegram/MAX каналы, нет `ZERNIO_*` для Facebook MSP, и `MAX_NOTIFY_CHAT_ID` — это ЛС Отчётика, не канал.

При install: `scripts/materialize_cloud_env.py` подставляет алиасы из общих Excalibur/React secrets — см. **`cloud-secrets-checklist.txt`**.

## 1. Cursor Cloud Secrets + MCP

**Secrets:** [cursor.com/dashboard/cloud-agents](https://cursor.com/dashboard/cloud-agents) → Runtime Secrets.

**MCP:** Dashboard → **Integrations & MCP** → добавить **mcp-kv.ru** (как в локальном Cursor).  
`VK_ACCESS_TOKEN` **не нужен** — VK публикуется через MCP на фазе 2.

### Обязательные Secrets (фаза 1 — скрипты)

| Переменная | Назначение |
|------------|------------|
| `MAX_BOT_TOKEN` | API Макс |
| `MAX_CHAT_ID` | ID **канала** Макс (алиас `MAX_CHANNEL_CHAT_ID` / `EXCALIBUR_MAX_CHANNEL_CHAT_ID`; не `MAX_NOTIFY_CHAT_ID`) |
| `TELEGRAM_BOT_TOKEN` | Бот Telegram (Cloud: шаг 2b; VPS: materialize) |
| `TELEGRAM_CHANNEL_CHAT_IDS` | `@nmorozova_emdr` (один канал) |
| `TELEGRAM_CHANNEL_UTM_SOURCES` | `tg1` |
| `ASOCKS_API_KEY` | Telegram из Cloud (прокси к api.telegram.org) |
| `ZERNIO_API_KEY` | Facebook — **только** в automation `POST-excalibur-emdr` (не алиас) |
| `ZERNIO_FACEBOOK_ACCOUNT_ID` | ID страницы FB — **только** в automation `POST-excalibur-emdr` |
| `RUNWARE_API_KEY` | Обложки (legacy, опционально) |
| `KIE_API_KEY` | Обложки (legacy fallback) |
| `GRSAI_API_KEY` | **Тексты** (`gemini-3.1-pro`, Chat API) + **обложки** (`gpt-image-2`) — один ключ |
| `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`, `FTP_SERVER_DIR` | Обложка для VK/TG preview (или алиас `REACT_FTP_*`) |
| `VPS_WEBHOOK_SECRET` | _(не нужен — VPS отключён)_ |

Список имён и alias mapping: `cloud-secrets-checklist.txt`

### Alias mapping (общие secrets → Posts EMDR)

`materialize_cloud_env.py` вызывает `apply_cloud_secret_aliases()`:

| Posts EMDR | Источник (если целевой пуст) |
|------------|------------------------------|
| `MAX_CHAT_ID` | `MAX_CHANNEL_CHAT_ID`, `EXCALIBUR_MAX_CHANNEL_CHAT_ID` |
| `TELEGRAM_BOT_TOKEN` | `EXCALIBUR_TELEGRAM_BOT_TOKEN` |
| `TELEGRAM_CHANNEL_CHAT_IDS` | valid list или `EXCALIBUR_TELEGRAM_CHANNEL_CHAT_IDS`; default `@nmorozova_emdr` |
| `FTP_*` | `REACT_FTP_*` |
| `WORDPRESS_URL` | `WP_HOME`, `WP_SITE_URL`, `PUBLIC_SITE_URL` |
| `WORDPRESS_USER` | `WP_USER`, `WP_ADMIN_USER` |
| `WORDPRESS_APP_PASSWORD` | `WP_APP_PASSWORD` |
| `VPS_WEBHOOK_SECRET` | _(deprecated, не добавлять)_ |

`ZERNIO_*` не алиасится — добавить в Secrets automation `POST-excalibur-emdr`. Preflight: явный `BLOCKER` если Zernio missing.

### VK (фаза 2 — MCP, не Secrets)

После `publish-topic.py` агент читает `output/{topic}/vk-mcp-handoff.json` и вызывает `vk_create_post_with_photo` ×2.

### Telegram (фаза 1b — Cloud, синхронно)

После `publish-topic.py` агент запускает `publish-telegram-from-handoff.py` (нужен `ASOCKS_API_KEY` + `TELEGRAM_BOT_TOKEN` в Secrets).  
Канал: только `@nmorozova_emdr`. VPS для Telegram **не ждать**.

### b17 (repair — Mac + Undetectable, не Cloud)

**VPS отключён** (2026-09). b17 не в автоматическом прогоне.

```bash
python3 scripts/repair-b17-tenchat.py --topic {topic_id}
```

Legacy VPS: `profile/browser-autonomous-vps.md` (архив).

## 2. Environment install

В репозитории: `.cursor/environment.json`

При старте Cloud Agent:

```bash
python3 scripts/materialize_cloud_env.py --check
```

## 3. Публикация

```bash
python3 scripts/publish-topic.py --topic {topic_id}
# → MCP VK/OK, close-cloud-publish.py — см. cloud-automation-runbook.md
```

## 4. Референс обложки

Ротация: `posts-emdr-memory/assets/reference/portrait-01.jpg` … `portrait-08.jpg`  
См. `profile/cover-reference-rotation.md`

## 5. Instructions для Automations (один раз)

Файл: **`profile/cloud-automation-prompt.md`** — блок `=== DASHBOARD INSTRUCTIONS ===` (6 строк).

Runbook на каждый прогон: **`profile/cloud-automation-runbook.md`** (подтягивается `git pull`, в Dashboard не копировать).

## 6. Проверка

```bash
python3 scripts/cloud_preflight.py
```

Exit `0` = готово к `publish-topic.py` (VK через MCP после скриптов).
