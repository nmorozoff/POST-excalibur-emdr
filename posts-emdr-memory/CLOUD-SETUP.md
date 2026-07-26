# Posts EMDR — Cloud Agent setup

Три фазы: см. **`profile/cloud-publish-phases.md`**.

## 1. Cursor Cloud Secrets + MCP

**Secrets:** [cursor.com/dashboard/cloud-agents](https://cursor.com/dashboard/cloud-agents) → Runtime Secrets.

**MCP:** Dashboard → **Integrations & MCP** → добавить **mcp-kv.ru** (как в локальном Cursor).  
`VK_ACCESS_TOKEN` **не нужен** — VK публикуется через MCP на фазе 2.

### Обязательные Secrets (фаза 1 — скрипты)

| Переменная | Назначение |
|------------|------------|
| `MAX_BOT_TOKEN` | API Макс |
| `MAX_CHAT_ID` | ID канала Макс |
| `TELEGRAM_BOT_TOKEN` | Бот Telegram |
| `TELEGRAM_CHANNEL_CHAT_IDS` | Каналы через запятую |
| `TELEGRAM_CHANNEL_UTM_SOURCES` | `tg1,tg2,tg3` |
| `ZERNIO_API_KEY` | Facebook |
| `ZERNIO_FACEBOOK_ACCOUNT_ID` | ID страницы FB |
| `RUNWARE_API_KEY` | Обложки |
| `FTP_SERVER`, `FTP_USERNAME`, `FTP_PASSWORD`, `FTP_SERVER_DIR` | Обложка для VK/TG preview |

Список имён: `cloud-secrets-checklist.txt`

### VK (фаза 2 — MCP, не Secrets)

После `publish-topic.py` агент читает `output/{topic}/vk-mcp-handoff.json` и вызывает `vk_create_post_with_photo` ×2.

### b17 + TenChat (фаза 3 — только Mac)

**Не публикуются из cloud.** Нужен Undetectable на вашем Mac:

```bash
python3 scripts/publish-b17-blog.py --topic {id} --submit
python3 scripts/publish-tenchat-post.py --topic {id} --submit
```

Handoff: `output/{topic}/browser-local-handoff.md`

## 2. Environment install

В репозитории: `.cursor/environment.json`

При старте Cloud Agent:

```bash
python3 scripts/materialize_cloud_env.py --check
```

Скрипт создаёт `posts-emdr-memory/*.env.local` из Secrets и проверяет preflight.

## 3. Публикация одной командой

После генерации контента агентом:

```bash
python3 scripts/publish-topic.py --topic sb-03-body-before-mind
```

Шаги:
1. materialize secrets
2. preflight
3. Runware cover (референс: `posts-emdr-memory/assets/reference/portrait.jpg` в репо)
4. Max → Telegram → VK (API) → Facebook
5. b17/TenChat — если Undetectable доступен

## 4. Референс обложки

В репозитории: `posts-emdr-memory/assets/reference/portrait.jpg`  
Переопределение: `RUNWARE_REFERENCE_IMAGE=/path/to.jpg`

## 5. Промпт для Cloud Agent

```
1. Взять первую pending из topics/short-blog-queue.md
2. Сгенерировать контент всех платформ
3. python3 scripts/materialize_cloud_env.py --check
4. python3 scripts/publish-topic.py --topic {id}
5. Обновить реестры и очередь
```

## 6. Локально vs Cloud

| | Локальный Mac | Cloud pod |
|--|---------------|-----------|
| Секреты | `*.env.local` | Cursor Secrets → materialize |
| VK | `vk_publish.py` (без MCP) | то же |
| FTP | `ftp.env.local` или legacy fallback | Secrets |
| b17/TenChat | Undetectable локально | обычно skip |

## 7. Проверка

```bash
python3 scripts/cloud_preflight.py
python3 scripts/cloud_preflight.py --json
```

Exit `0` = готово к `publish-topic.py`.
