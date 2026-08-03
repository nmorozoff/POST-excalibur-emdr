# VPS publish — Telegram + b17 + TenChat

Тема: `sb-03-body-before-mind`

Cloud опубликовал Макс / VK(MCP) / Facebook. Осталось на **VPS**:

1. Telegram ×3 (ASocks KZ → `api.telegram.org`)
2. b17 (Playwright + residential RU)
3. TenChat (Playwright)

## Триггер

Webhook (сразу после `git push`):

```bash
curl -fsS -X POST "http://195.209.210.45:8787/publish" \
  -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"topic":"sb-03-body-before-mind"}'
```

Или cron ≤10 мин: `scripts/run-linux-browser-worker.sh`

## Вручную на VPS

```bash
cd ~/POST-excalibur-emdr
source .venv-browser/bin/activate
python3 scripts/asocks_sync_proxy.py --target telegram
python3 scripts/fetch-topic-cover.py --topic sb-03-body-before-mind
python3 scripts/publish-browser-deferred.py --topic sb-03-body-before-mind --submit --finish --git-push
```

См. `posts-emdr-memory/profile/cloud-publish-phases.md`
