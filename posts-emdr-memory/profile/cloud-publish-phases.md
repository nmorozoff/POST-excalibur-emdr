# Cloud publish — три фазы

Полный цикл MSP-поста в автоматизации.

## Фаза 1 — Cloud Agent (скрипты)

**Платформы:** Макс, Facebook, обложка Runware, FTP для VK-превью.

**НЕ публикует:** Telegram (блокировка `api.telegram.org` с cloud/VPS DC → только ASocks KZ на VPS).

```bash
python3 scripts/materialize_cloud_env.py
python3 scripts/publish-topic.py --topic {topic_id}
```

`VK_ACCESS_TOKEN` **не нужен**. Скрипт заливает обложку на сайт и пишет `output/{topic}/vk-mcp-handoff.json` + `browser-local-handoff.md`.

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

Обновить реестры: `vk-profile`, `vk-group`, `max`, `facebook`.

## Фаза 3 — Telegram + b17 + TenChat (VPS)

**Полная инструкция:** `profile/browser-autonomous-vps.md`

Cloud после фаз 1–2:

1. `git add` + `commit` + `push` артефактов (`output/{topic}/`, handoff, реестры)
2. Webhook на VPS:

```bash
curl -fsS -X POST "http://195.209.210.45:8787/publish" \
  -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"topic":"{topic_id}"}'
```

Или cron на VPS подхватит за ≤10 мин.

VPS worker делает:
1. `git pull`
2. `asocks_sync_proxy.py --target telegram` → Telegram ×3 (`link_preview`)
3. b17 (Playwright + RU proxy, HTTPS cover, verify list)
4. TenChat (Playwright)
5. `--finish` (реестры + очередь) + `--git-push`

**На VPS обязательно:**
- `B17_PROXY_*` (ASocks RU)
- `TELEGRAM_PROXY_*` (ASocks KZ `ResKazakhstan - Turkestan`)
- `linux-storage-state.json`
- `github.env.local` (`GITHUB_TOKEN`)
- webhook systemd **или** cron

Mac — **не используем**.

## Secrets для Cloud

См. `cloud-secrets-checklist.txt`.  
`VK_ACCESS_TOKEN` **не нужен** (VK через MCP).  
`VPS_WEBHOOK_SECRET` — в Cloud Secrets, чтобы вызвать webhook.

## Промпт automation (полный)

```
1. pending тема из short-blog-queue.md → контент всех платформ
   (в telegram-post.md обязателен <!-- END_POST --> до ## Мета)
2. python3 scripts/materialize_cloud_env.py --check
3. python3 scripts/publish-topic.py --topic {id}
   (Telegram НЕ публикуется здесь — deferred на VPS)
4. MCP vk_create_post_with_photo ×2 по vk-mcp-handoff.json
5. send-vk-post.py --delete-cover; обновить реестры max/vk/fb
6. git add + commit + push output/{id}/ и реестры
7. curl VPS webhook: POST /publish {"topic":"{id}"} с VPS_WEBHOOK_SECRET
8. НЕ помечать published в очереди — это сделает VPS worker (--finish)
```
