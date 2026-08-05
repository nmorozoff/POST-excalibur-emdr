=== POSTS-EMDR-OTCHETIK ===
topic: sb-08-anxiety-for-loved-ones
overall: partial
max_report_sent: true
verify_exit_codes:
- first: 3
send_max_report_exit: 0
platforms:
  max: ok
  telegram: fail (VPS pending)
  vk_profile: ok
  vk_group: ok
  facebook: ok (published)
  b17: fail (VPS pending)
covers:
  local_cover: ok
  site_cover: ok
issues:
- Telegram: не отправлен (или VPS ещё не отработал)
- b17: не published (VPS мог ещё не отработать)
- Тема всё ещё in_progress в очереди
- VPS phase 3: нет finish (webhook trigger TimeoutError)
links:
  max: https://max.ru/se13417616_biz/AZ_R6SwWaV4
  vk_profile: https://vk.com/wall218367867_656
  vk_group: https://vk.com/wall-224685309_156
  facebook: https://www.facebook.com/632301483303094_122181226184837712
incidents_written:
- INC-20260805-1240-sb08-vps-pending
fixic_needed: false
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260805-1240-sb08-vps-pending
