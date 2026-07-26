# Cloud publish — три фазы

Полный цикл MSP-поста в автоматизации **не умещается в один cloud pod**.

## Фаза 1 — Cloud Agent (скрипты)

**Платформы:** Макс, Telegram×3, Facebook, обложка Runware, FTP для VK-превью.

```bash
python3 scripts/materialize_cloud_env.py
python3 scripts/publish-topic.py --topic {topic_id}
```

`VK_ACCESS_TOKEN` **не нужен**. Скрипт заливает обложку на сайт и пишет `output/{topic}/vk-mcp-handoff.json`.

## Фаза 2 — Cloud Agent (MCP mcp-kv)

**Платформа:** VK профиль + VK группа.

В automation **включить MCP** `user-mcp-kv` / mcp-kv.ru (Dashboard → Integrations & MCP).

Агент читает `vk-mcp-handoff.json` и вызывает **дважды** `vk_create_post_with_photo`:

| # | publish_location | from_group | message |
|---|------------------|------------|---------|
| 1 | `personal` | false | из `vk-profile-post.md` |
| 2 | `group` | true | из `vk-group-post.md` |

`photo_url` = поле `cover_public_url` из handoff.  
`group_id` = `224685309`.

Gate: в ответе MCP — `📸 Загружено фото`.  
После обоих постов: `python3 scripts/send-vk-post.py --topic {id} --delete-cover`

Обновить реестры: `vk-profile`, `vk-group`.

## Фаза 3 — Локальный Mac (Undetectable)

**Платформы:** b17.ru, TenChat.

В cloud pod **нет** Undetectable Browser (`127.0.0.1:25325`). Эти площадки **не публикуются из cloud**.

На Mac (Undetectable + Profile1 запущены):

```bash
python3 scripts/publish-b17-blog.py --topic {topic_id} --submit
python3 scripts/publish-tenchat-post.py --topic {topic_id} --submit
```

Или без `--submit` — форма заполнится, Save/Publish вручную.

Handoff-файл: `output/{topic}/browser-local-handoff.md` (создаётся автоматически).

### Вариант: вторая automation «browser-only»

Отдельная automation на **локальной машине** (не cloud), триггер после cloud:

1. Cloud закончил → webhook / ручной запуск
2. Локальный агент: только b17 + TenChat

## Secrets для Cloud (без VK_ACCESS_TOKEN)

См. `cloud-secrets-checklist.txt` — строка `VK_ACCESS_TOKEN` **удалена**.

Обязательно: MCP mcp-kv в настройках automation.

## Промпт automation (полный)

```
1. pending тема из short-blog-queue.md → контент всех платформ
2. python3 scripts/materialize_cloud_env.py
3. python3 scripts/publish-topic.py --topic {id}
4. MCP vk_create_post_with_photo ×2 по vk-mcp-handoff.json
5. send-vk-post.py --delete-cover; update-post-registry
6. Закрыть очередь для платформ 1–5; в handoff: browser-local-handoff для b17/TenChat
```

Фаза 3 — отдельно на Mac или вторая локальная automation.
