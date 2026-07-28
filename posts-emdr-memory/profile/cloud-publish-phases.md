# Cloud publish — три фазы

Полный цикл MSP-поста в автоматизации.

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

## Фаза 3 — b17 + TenChat (гибрид Mac + VPS)

**b17.ru блокирует IP VPS** (датацентр). **b17 + TenChat** — с Mac через Undetectable:

```bash
./scripts/run-mac-browser-phase3.sh --pending
```

После cloud automation: в `output/{topic}/browser-local-handoff.md` — запустить скрипт на Mac (Profile1 в Undetectable).

### VPS (Playwright, опционально)

Storage state: `export-playwright-storage-from-undetectable.py` → scp на VPS.  
Cron TenChat: `scripts/run-linux-browser-worker.sh` (b17 на VPS пропускается при блокировке IP).

См. **`profile/browser-linux-vps-setup.md`**.

### Fallback: Mac + Undetectable (основной путь фазы 3)

`BROWSER_BACKEND=undetectable` в `b17.env.local` / `tenchat.env.local`.

## Secrets для Cloud

См. `cloud-secrets-checklist.txt`.  
`VK_ACCESS_TOKEN` **не нужен** (VK через MCP).

Для фазы 3 режима A добавить:

- `UNDETECTABLE_BASE_URL`
- `UNDETECTABLE_PROFILE_ID`
- `UNDETECTABLE_API_BEARER`

## Промпт automation (полный)

```
1. pending тема из short-blog-queue.md → контент всех платформ
2. python3 scripts/materialize_cloud_env.py
3. python3 scripts/publish-topic.py --topic {id} [--submit если remote Undetectable OK]
4. MCP vk_create_post_with_photo ×2 по vk-mcp-handoff.json
5. send-vk-post.py --delete-cover; update-post-registry
6. Если browser-local-handoff.md — VPS worker или ручной Mac для b17/TenChat
7. Закрыть очередь; обновить реестры b17/tenchat после VPS
```
