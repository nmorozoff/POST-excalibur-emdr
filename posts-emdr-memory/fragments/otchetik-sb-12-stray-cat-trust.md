=== POSTS-EMDR-OTCHETIK ===
topic: sb-12-stray-cat-trust
overall: fail
max_report_sent: true
incidents_written:
- INC-20260809-1120-ok-refresh-token-expired
- INC-20260809-1120-sb12-telegram-char-limit
- INC-20260809-1120-sb12-b17-publish-failed
fixic_needed: true
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260809-1120-ok-refresh-token-expired

## Polling
- Попытки verify: 4 (attempt 1 fail; pull main + vps-worker-last-run; attempt 2 fail; re-trigger webhook 202; wait 2min + pull; attempt 3–4 fail — стабильный fail)
- Root causes из `vps-worker-last-run.json`: Telegram 4403>4096; b17 parse error; OK MCP refresh token expired (cloud)

## Опубликовано
- Max: https://max.ru/se13417616_biz/AZ_mOiY1CDE
- VK профиль: https://vk.com/wall218367867_660
- VK группа: https://vk.com/wall-224685309_160
- Facebook: https://www.facebook.com/632301483303094_122181625424837712

## Не опубликовано
- Telegram (char limit)
- OK (refresh token expired)
- b17 (parse / VPS worker failed)

## Эскалация
Task(`posts-emdr-fixic`) — OK token + telegram shorten + b17 re-publish после fix.
