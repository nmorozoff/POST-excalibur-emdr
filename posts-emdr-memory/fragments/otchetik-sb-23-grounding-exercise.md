=== POSTS-EMDR-OTCHETIK ===
topic: sb-23-grounding-exercise
overall: fail
operational_note: partial (VPS phase 3 pending — webhook HTTP 202 принят, TG/b17 ещё не отработали)
max_report_sent: true
incidents_written:
- INC-20260824-0956-sb23-vps-pending
fixic_needed: false
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260824-0956-sb23-vps-pending

## Verify summary

- Attempts: 1 (single check per director request)
- verify exit: 2 (fail)
- VPS webhook: HTTP 202 (принят до verify)

## Platforms OK

Max, VK profile, VK group, Facebook, OK — опубликованы.

## Pending (VPS phase 3)

- Telegram: нет `telegram-publish-log.json` (каналы nmorozova_emdr, natalia_morozova_psy)
- b17: нет `b17-publish-log.json` (prep готов)
- Нет `browser-worker-finish.json`, тема `in_progress` в очереди

## Fixic

Не эскалировать: cloud OK, VPS webhook принят; ожидаем phase 3. b17 draft_saved не применимо.

incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260824-0956-sb23-vps-pending
