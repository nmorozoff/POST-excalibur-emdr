# Publish log — sb-03-body-before-mind

**Дата:** 2026-07-26  
**Заголовок:** Момент, когда тело узнаёт о тревоге раньше головы  
**Очередь MSP:** #3 · формат: наблюдение→инсайт  
**Статус:** **BLOCKED** — нет Cursor Cloud Secrets (preflight failed)

## Контент готов

| Артефакт | Статус |
|----------|--------|
| max-post.md | ✅ |
| cover-prompt.txt | ✅ |
| cover.png | ❌ (нет RUNWARE_API_KEY) |
| telegram-post.md | ✅ |
| vk-profile-post.md | ✅ |
| vk-group-post.md | ✅ |
| facebook-post.md | ✅ |
| b17-blog-post.md | ✅ |
| tenchat-post.md | ✅ |

## Публикация

| Платформа | Статус |
|-----------|--------|
| Макс | ⏸ blocked — MAX_BOT_TOKEN, MAX_CHAT_ID |
| Telegram | ⏸ blocked — TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_CHAT_IDS |
| VK профиль | ⏸ blocked — VK_ACCESS_TOKEN, VK_GROUP_ID |
| VK группа | ⏸ blocked — VK_ACCESS_TOKEN, VK_GROUP_ID |
| Facebook | ⏸ blocked — ZERNIO_API_KEY, ZERNIO_FACEBOOK_ACCOUNT_ID |
| b17 | ⏸ deferred — Undetectable недоступен + нет секретов |
| TenChat | ⏸ deferred — Undetectable недоступен + нет секретов |

## Команда после настройки Secrets

```bash
python3 scripts/materialize_cloud_env.py --check
python3 scripts/publish-topic.py --topic sb-03-body-before-mind
```

См. `posts-emdr-memory/CLOUD-SETUP.md` и Environment: https://cursor.com/dashboard/cloud-agents/environments/e/a9b94054-88bf-11f1-b532-320a589b8025
