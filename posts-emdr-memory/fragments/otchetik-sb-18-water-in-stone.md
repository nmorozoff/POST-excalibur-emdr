=== POSTS-EMDR-OTCHETIK ===
topic: sb-18-water-in-stone
overall: partial
max_report_sent: true
incidents_written:
- INC-20260816-1030-otchetik-b17-rate-limit-draft (updated, not duplicated)
fixic_needed: false
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260816-1030-otchetik-b17-rate-limit-draft

## Polling summary

- Attempts: 6 (interval ~10 min each)
- Webhook re-trigger: yes (after attempt 3, pid 3336206, 202 accepted)
- Final overall: partial

## Issues

1. b17: сохранено в черновик (rate limit), требуется повторный запуск
2. Тема всё ещё in_progress в очереди
3. VPS phase 3: нет finish (webhook/cron ещё не завершил)

## Platforms OK

Max, Telegram×2, VK profile, VK group, Facebook, OK — все опубликованы.

## Fixic

Не эскалировать: единственная блокирующая причина — b17 rate-limit (`draft_saved`). Cron retry опубликует позже.

incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260816-1030-otchetik-b17-rate-limit-draft
