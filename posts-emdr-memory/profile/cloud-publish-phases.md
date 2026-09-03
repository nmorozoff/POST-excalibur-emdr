# Cloud publish — три фазы

Полный цикл MSP-поста в автоматизации.

## Фаза 1 — Cloud Agent (скрипты)

**Платформы:** Макс, Facebook, обложка Runware, FTP для VK-превью, handoff OK.

**НЕ публикует напрямую:** Telegram (если ASocks в Secrets — `publish-topic.py` вызывает `publish-telegram-from-handoff.py` синхронно; иначе MCP handoff).

```bash
python3 scripts/materialize_cloud_env.py
python3 scripts/publish-topic.py --topic {topic_id}
```

Если `telegram.status != published` → Cloud Agent: `publish-telegram-from-handoff.py` или MCP по `telegram-mcp-handoff.json`.

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

### VK Stories (опционально, после wall-постов)

Когда есть `vk-publish-log.json` с URL постов:

```bash
python3 scripts/publish-vk-story.py --topic {id} --prepare
```

Агент вызывает MCP **`vk_publish_story`** дважды по `vk-story-mcp-handoff.json`:

| # | publish_location | photo_url | link_text | link_url |
|---|------------------|-----------|-----------|----------|
| 1 | `personal` | cover CDN | `Читать пост` | URL wall профиля |
| 2 | `group` | cover CDN | `Читать пост` | URL wall группы |

Запись лога:

```bash
python3 scripts/publish-vk-story.py --topic {id} --record \\
  --profile-story-id ... --group-story-id ...
```

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

## Фаза 3 — Cloud close (без VPS)

**VPS отключён** (2026-09). Закрытие темы только в Cloud:

```bash
python3 scripts/close-cloud-publish.py --topic {topic_id}
```

Делает: `mark-short-blog-published`, `browser-worker-finish.json`, `cloud-publish-finish.json`, b17 → `b17-tenchat-pending-queue.md` если не published.

**b17.ru:** `python3 scripts/repair-b17-tenchat.py --topic {id}` с Mac + Undetectable (не Cloud, не VPS).

Legacy VPS: `profile/browser-autonomous-vps.md` (архив).

## Secrets для Cloud

См. `cloud-secrets-checklist.txt`.  
`VK_ACCESS_TOKEN` **не нужен** (VK через MCP).  
`VPS_WEBHOOK_SECRET` — **не нужен** (VPS отключён).  
`TELEGRAM_CHANNEL_CHAT_IDS` — **только** `@nmorozova_emdr` (не `CHANNEL_HANDLE`).

## Промпт automation (полный)

```
1. pending тема → grsai-generate-topic.py
2. materialize_cloud_env.py --check
3. publish-topic.py --topic {id}
4. publish-telegram-from-handoff.py --topic {id} (если нет telegram-publish-log.json)
5. MCP vk ×2, ok, реестры, send-vk-post --delete-cover
6. git commit + push main
7. close-cloud-publish.py --topic {id}
8. Task posts-emdr-otchetik
```
