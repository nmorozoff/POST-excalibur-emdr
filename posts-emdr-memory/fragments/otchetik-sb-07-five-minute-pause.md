=== POSTS-EMDR-OTCHETIK ===
topic: sb-07-five-minute-pause
overall: partial
max_report_sent: true
verify_exit_codes:
- first: 3
- retry_after_10min: 3
send_max_report_exit: 0
platforms:
  max: ok
  telegram: fail
  vk_profile: ok
  vk_group: ok
  facebook: ok (status publishing, Zernio pending URL)
  b17: fail
covers:
  local_cover: ok
  site_cover: ok (retry)
issues:
- Telegram: не отправлен (или VPS ещё не отработал)
- b17: не published (VPS мог ещё не отработать)
- Тема всё ещё in_progress в очереди
- VPS phase 3: нет finish (webhook/cron ещё не завершил)
links:
  max: https://max.ru/se13417616_biz/AZ_NyT26TP0
  vk_profile: https://vk.com/wall218367867_655
  vk_group: https://vk.com/wall-224685309_155
  facebook: https://www.facebook.com/632301483303094_122181144110837712
incidents_written:
- INC-20260804-1742-sb07-vps-phase3-pending
fixic_needed: true
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260804-1742-sb07-vps-phase3-pending
