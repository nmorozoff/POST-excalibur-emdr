=== POSTS-EMDR-OTCHETIK ===
topic: sb-19-question-before-sleep
overall: fail
max_report_sent: true
verify_exit_codes:
- attempt_1: 2
polling:
  attempts: 1
  webhook_retrigger: skipped (VPS down on health check)
send_max_report_exit: 0
platforms:
  max: ok
  telegram: fail (VPS phase 3 not started)
  vk_profile: ok
  vk_group: ok
  facebook: ok (published)
  ok: ok (published)
  b17: fail (VPS pending, not draft_saved)
covers:
  local_cover: ok
  site_cover: ok
issues:
- Telegram: не отправлен (VPS webhook Connection reset by peer)
- b17: не published (VPS phase 3 не стартовал)
- Тема всё ещё in_progress в очереди
- VPS phase 3: Telegram ещё не отработал
links:
  max: https://max.ru/se13417616_biz/AaAbGflxdSc
  vk_profile: https://vk.com/wall218367867_693
  vk_group: https://vk.com/wall-224685309_170
  facebook: https://www.facebook.com/632301483303094_122182671764837712
  ok: https://ok.ru/group/70000034253679/topic/161377985065071
incidents_written:
- INC-20260819-1745-sb19-vps-webhook-connection-reset
fixic_needed: true
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260819-1745-sb19-vps-webhook-connection-reset
