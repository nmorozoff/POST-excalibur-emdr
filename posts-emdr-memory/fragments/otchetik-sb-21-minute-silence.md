=== POSTS-EMDR-OTCHETIK ===
topic: sb-21-minute-silence
overall: fail
max_report_sent: true
incidents_written:
- INC-20260821-0950-telegram-vps-proxy-timeout
fixic_needed: true
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260821-0950-telegram-vps-proxy-timeout

## Итог

Тема `sb-21-minute-silence` — **fail** (2026-08-21).

- Cloud OK: Max, VK×2 (MCP), Facebook, OK
- VPS webhook 202 ×2, но Telegram fail: `URLError timed out` через KZ proxy (asocks ResKazakhstan — Turkestan)
- Нет `telegram-publish-log.json`, нет `browser-worker-finish.json`
- b17 published: https://www.b17.ru/blog/minuta_tishiny_bez_telefona/
- Очередь: тема всё ещё `in_progress`

## Ссылки (опубликованные)

- Max: https://max.ru/se13417616_biz/AaAjnqKxMNY
- VK профиль: https://vk.com/wall218367867_695
- VK группа: https://vk.com/wall-224685309_172
- Facebook: https://www.facebook.com/632301483303094_122182845002837712
- OK: https://ok.ru/group/70000034253679/topic/161383725297775
- b17: https://www.b17.ru/blog/minuta_tishiny_bez_telefona/
- Telegram: не отправлен

## Эскалация

**Task(`posts-emdr-fixic`)** — INC-20260821-0950-telegram-vps-proxy-timeout (open).
