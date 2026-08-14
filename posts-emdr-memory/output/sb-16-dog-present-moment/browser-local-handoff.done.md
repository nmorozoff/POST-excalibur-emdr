# VPS publish — Telegram + b17

Тема: `sb-16-dog-present-moment`

Cloud опубликовал Макс / VK(MCP) / Facebook / OK(MCP). Осталось на **VPS**:

1. Telegram ×2 (@nmorozova_emdr, @natalia_morozova_psy) — ASocks KZ
2. b17 (Playwright + residential RU)

## Триггер

Webhook (сразу после `git push`):

```bash
curl -fsS -X POST "http://195.209.210.45:8787/publish" \
  -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"topic":"sb-16-dog-present-moment"}'
```

Или cron ≤10 мин: `scripts/run-linux-browser-worker.sh`

## Вручную на VPS

```bash
cd ~/POST-excalibur-emdr
source .venv-browser/bin/activate
python3 scripts/asocks_sync_proxy.py --target telegram
python3 scripts/fetch-topic-cover.py --topic sb-16-dog-present-moment
python3 scripts/publish-browser-deferred.py --topic sb-16-dog-present-moment --submit --finish --git-push
```

См. `posts-emdr-memory/profile/cloud-publish-phases.md`
