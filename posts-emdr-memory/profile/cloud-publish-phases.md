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

## Фаза 3 — b17 + TenChat (VPS, без Mac)

**Полная инструкция:** `profile/browser-autonomous-vps.md`

Cloud после фаз 1–2:

1. `git push` артефактов (`output/{topic}/`, handoff, реестры)
2. Webhook на VPS:

```bash
curl -fsS -X POST "http://195.209.210.45:8787/publish" \
  -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"topic":"{topic_id}"}'
```

Или cron на VPS подхватит за ≤10 мин.

**На VPS обязательно:** `B17_PROXY_SERVER` (residential RU) — иначе b17 заблокирован.

Mac (`run-mac-browser-phase3.sh`) — только fallback.

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
2. python3 scripts/materialize_cloud_env.py --check
3. python3 scripts/publish-topic.py --topic {id}
4. MCP vk_create_post_with_photo ×2 по vk-mcp-handoff.json
5. send-vk-post.py --delete-cover; update-post-registry (max/tg/vk/fb)
6. git add + commit + push output/{id}/ и реестры
7. curl VPS webhook: POST /publish {"topic":"{id}"} с VPS_WEBHOOK_SECRET
   (или VPS cron подхватит за 10 мин)
8. НЕ помечать published в очереди — это сделает VPS worker (--finish)
```
