# Полный пайплайн MSP short-blog (cloud + Linux VPS)

## Фаза 1 — Cloud Agent (скрипты)

```bash
python3 scripts/materialize_cloud_env.py
python3 scripts/publish-topic.py --topic {topic_id}
```

Выход: Макс, Telegram, Facebook, `vk-mcp-handoff.json`, при недоступном браузере — `browser-local-handoff.md`.

## Фаза 2 — Cloud Agent (MCP mcp-kv)

`vk_create_post_with_photo` ×2 → `send-vk-post.py --delete-cover`

## Фаза 3 — Linux VPS (Playwright)

Cron `scripts/run-linux-browser-worker.sh`:

1. `fetch-topic-cover.py` — обложка с сайта
2. `publish-browser-deferred.py --submit --finish`
3. опционально `--git-push`

**Один раз на VPS:** `browser_bootstrap_sessions.py` → `linux-storage-state.json`

## Закрытие темы

`browser_worker_finish.py` автоматически:

- реестры `b17-posts-registry.md`, `tenchat-posts-registry.md`
- `short-blog-queue.md` → `short-blog-published.md`
- `browser-local-handoff.md` → `.done.md`

## Деплой на VPS без git

С Mac после cloud:

```bash
./scripts/sync-to-vps.sh
```

## Проверки

| Команда | Где |
|---------|-----|
| `cloud_preflight.py --json` | Cloud |
| `browser_bridge_health.py` | VPS |
| `browser_verify_sessions.py` | VPS после bootstrap |
| `publish-browser-deferred.py --list` | VPS |
