# Cloud publish — три фазы

Полный цикл MSP-поста в автоматизации.

## Фаза 1 — Cloud Agent (скрипты)

**Платформы:** Макс, Facebook, обложка Runware, FTP для VK-превью, handoff OK.

**НЕ публикует:** Telegram (блокировка `api.telegram.org` с cloud/VPS DC → только ASocks KZ на VPS).

```bash
python3 scripts/materialize_cloud_env.py
python3 scripts/publish-topic.py --topic {topic_id}
```

`VK_ACCESS_TOKEN` **не нужен**. Скрипт заливает обложку на сайт и пишет `output/{topic}/vk-mcp-handoff.json`, `ok-mcp-handoff.json` (если есть `ok-post.md`) + `browser-local-handoff.md`.

## Фаза 2 — Cloud Agent (MCP mcp-kv)

**Платформы:** VK профиль + VK группа + **Одноклассники (группа)**.

В automation **включить MCP** `user-mcp-kv` / mcp-kv.ru (Dashboard → Integrations & MCP).

### VK

Агент читает `vk-mcp-handoff.json` и вызывает **дважды** `vk_create_post_with_photo`:

| # | publish_location | from_group | message |
|---|------------------|------------|---------|
| 1 | `personal` | false | из `vk-profile-post.md` |
| 2 | `group` | true | из `vk-group-post.md` |

`photo_url` = поле `cover_public_url` из handoff.  
`group_id` = `224685309`.

Gate: в ответе MCP — `📸 Загружено фото`.  
После обоих постов: `python3 scripts/send-vk-post.py --topic {id} --delete-cover`

### OK (группа)

Если есть `ok-mcp-handoff.json`:

1. MCP `ok_create_post_with_photo`:
   - `text` — из handoff
   - `image_url` — из handoff
   - `gid`: `70000034253679` (или `OK_GROUP_GID`)
   - `onBehalfOfGroup`: `true`
2. Записать лог и реестр:

```bash
python3 scripts/record-ok-publish.py --topic {id} \
  --url "https://ok.ru/group/70000034253679/topic/..." \
  --mediatopic-id "..." \
  --title "..." --site-url "https://morozovanatalia.ru/..." --tags "..."
```

Обновить реестры: `vk-profile`, `vk-group`, `max`, `facebook`, **`ok`**.

**Если MCP вернул `Refresh token expired`:** re-auth OK в Dashboard (mcp-kv), затем повторить шаги 1–2 по существующему `ok-mcp-handoff.json` (не перегенерировать контент). См. pitfalls «OK MCP: Refresh token expired».

## Фаза 3 — Telegram + b17 (VPS)

**TenChat снят с пайплайна** (2026-08-03).

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

Или cron на VPS подхватит в **10:00** или **17:00** MSK (fallback).

VPS worker делает:
1. `git pull`
2. `ensure_site_cover` → FTP обложка на `social-covers/{topic}.jpg`
3. `asocks_sync_proxy.py --target telegram` → Telegram ×2 (`@nmorozova_emdr`, `@natalia_morozova_psy`, `link_preview`)
4. b17 (Playwright + RU proxy, HTTPS cover, verify list)
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
5. MCP ok_create_post_with_photo по ok-mcp-handoff.json (если есть); record-ok-publish.py
6. send-vk-post.py --delete-cover; обновить реестры max/vk/fb/ok
7. git add + commit + push output/{id}/ и реестры
8. curl VPS webhook: POST /publish {"topic":"{id}"} с VPS_WEBHOOK_SECRET
9. НЕ помечать published в очереди — это сделает VPS worker (--finish)
```
