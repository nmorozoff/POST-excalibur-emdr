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

## Фаза 3 — b17 + TenChat (Linux VPS, Playwright)

В cloud pod **нет** браузера с сессиями. Публикация на **вашем Ubuntu VPS** (тот же, что CRM) — см. **`profile/browser-linux-vps-setup.md`**.

### Worker на VPS (рекомендуется)

Cloud пишет `browser-local-handoff.md` → VPS cron:

```bash
git pull --ff-only
python3 scripts/fetch-topic-cover.py --all-pending
python3 scripts/publish-browser-deferred.py --submit
```

`browser.env.local`: `BROWSER_BACKEND=playwright` + `linux-storage-state.json` (логин один раз).

### Fallback: Mac + Undetectable

`BROWSER_BACKEND=undetectable` — как раньше.

### Устарело: Windows + Undetectable

См. `browser-vps-setup.md` — только если нет Linux.

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
