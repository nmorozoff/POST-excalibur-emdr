# Posts EMDR — Cloud Agent setup

Три фазы: см. **`profile/cloud-publish-phases.md`**.  
Утренний прогон: **`.cursor/posts-emdr-handoff.md`**.

## 1. Cursor Cloud Secrets + MCP

**Secrets:** [cursor.com/dashboard/cloud-agents](https://cursor.com/dashboard/cloud-agents) → Runtime Secrets.

**MCP:** Dashboard → **Integrations & MCP** → добавить **mcp-kv.ru** (как в локальном Cursor).  
`VK_ACCESS_TOKEN` **не нужен** — VK публикуется через MCP на фазе 2.

### Обязательные Secrets (фаза 1 — скрипты)

| Переменная | Назначение |
|------------|------------|
| `MAX_BOT_TOKEN` | API Макс |
| `MAX_CHAT_ID` | ID канала Макс |
| `TELEGRAM_BOT_TOKEN` | Бот Telegram (нужен на VPS; в Cloud можно тоже для materialize) |
| `TELEGRAM_CHANNEL_CHAT_IDS` | `@nmorozova_emdr,@natalia_morozova_psy` |
| `TELEGRAM_CHANNEL_UTM_SOURCES` | `tg1,tg2` |
| `ZERNIO_API_KEY` | Facebook |
| `ZERNIO_FACEBOOK_ACCOUNT_ID` | ID страницы FB |
| `RUNWARE_API_KEY` | Обложки (legacy, опционально) |
| `KIE_API_KEY` | Обложки (legacy fallback) |
| `GRSAI_API_KEY` | **Тексты** (`gemini-3.1-pro`, Chat API) + **обложки** (`gpt-image-2`) — один ключ |
| `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`, `FTP_SERVER_DIR` | Обложка для VK/TG preview |
| `VPS_WEBHOOK_SECRET` | Триггер фазы 3 на VPS |

Список имён: `cloud-secrets-checklist.txt`

### VK (фаза 2 — MCP, не Secrets)

После `publish-topic.py` агент читает `output/{topic}/vk-mcp-handoff.json` и вызывает `vk_create_post_with_photo` ×2.

### Telegram + b17 (фаза 3 — Linux VPS)

**TenChat снят с пайплайна** (2026-08-03).

**Не из cloud pod.** Telegram с Cloud/датацентра **не работает** (таймаут `api.telegram.org`).

На Ubuntu VPS: webhook `POST /publish` или cron `run-linux-browser-worker.sh`.

Подробно: **`profile/browser-autonomous-vps.md`**, **`profile/cloud-publish-phases.md`**.

## 2. Environment install

В репозитории: `.cursor/environment.json`

При старте Cloud Agent:

```bash
python3 scripts/materialize_cloud_env.py --check
```

## 3. Публикация

```bash
python3 scripts/publish-topic.py --topic sb-05-tolerate-uncertainty
# → Макс + FB + VK handoff; Telegram/b17 deferred
# затем MCP VK ×2, git push, curl webhook
```

## 4. Референс обложки

Ротация: `posts-emdr-memory/assets/reference/portrait-01.jpg` … `portrait-08.jpg`  
См. `profile/cover-reference-rotation.md`

## 5. Промпт для Cloud Agent

См. `.cursor/posts-emdr-handoff.md` (блок «Запуск Cloud Agent»).

## 6. Проверка

```bash
python3 scripts/cloud_preflight.py
```

Exit `0` = готово к `publish-topic.py` (VK через MCP после скриптов).
