# Posts EMDR — Cloud Agent setup

Полная автоматизация в изолированной среде **без MCP** и **без локальных `.env.local` в git**.

## 1. Cursor Cloud Secrets

Откройте [cursor.com/dashboard/cloud-agents](https://cursor.com/dashboard/cloud-agents) → ваш Environment → **Secrets**.

Добавьте переменные как **Runtime Secrets** (тип `Runtime Secret` — не попадут в логи агента).

### Обязательные (автопубликация Макс → TG → VK → Facebook)

| Переменная | Назначение |
|------------|------------|
| `MAX_BOT_TOKEN` | API Макс |
| `MAX_CHAT_ID` | ID канала Макс |
| `TELEGRAM_BOT_TOKEN` | Бот Telegram |
| `TELEGRAM_CHANNEL_CHAT_IDS` | ID каналов через запятую |
| `TELEGRAM_CHANNEL_UTM_SOURCES` | `tg1,tg2,tg3` |
| `VK_ACCESS_TOKEN` | VK API (wall, photos) |
| `VK_GROUP_ID` | `224685309` |
| `ZERNIO_API_KEY` | Facebook через Zernio |
| `ZERNIO_FACEBOOK_ACCOUNT_ID` | ID страницы FB |
| `RUNWARE_API_KEY` | Обложки Runware i2i |
| `FTP_SERVER` | FTP Beget |
| `FTP_USERNAME` | FTP логин |
| `FTP_PASSWORD` | FTP пароль |
| `FTP_SERVER_DIR` | `/public_html/` |

Шаблоны значений: `posts-emdr-memory/*.env.example`

### Опционально (b17 + TenChat)

Только если в cloud pod доступен **Undetectable Browser** (обычно нет):

| Переменная | Назначение |
|------------|------------|
| `UNDETECTABLE_BASE_URL` | `http://127.0.0.1:25325` |
| `UNDETECTABLE_PROFILE_ID` | ID профиля |
| `B17_COMPOSE_URL` | URL формы b17 |
| `TENCHAT_COMPOSE_URL` | URL редактора TenChat |

Без Undetectable: публикуются **5 платформ**, b17/TenChat — `deferred`.

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
