# VPS publish — b17 only

Тема: `sb-25-before-saying-yes`

Cloud: Макс, VK, Facebook, OK, **Telegram (MCP mcp-kv)**. На **VPS** остался только:

1. b17 (Playwright + residential RU) — черновик, не блокирует закрытие темы

Telegram **не** на VPS — см. `telegram-mcp-handoff.json` и MCP в Cloud.

## Триггер b17 (опционально)

```bash
curl -fsS -X POST "http://195.209.210.45:8787/publish" \
  -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"topic":"sb-25-before-saying-yes"}'
```

Worker пропустит Telegram, если уже есть `telegram-publish-log.json`.

См. `posts-emdr-memory/profile/cloud-publish-phases.md`
