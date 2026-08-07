=== POSTS-EMDR-OTCHETIK ===
topic: sb-10-phrase-when-anxiety
overall: partial
max_report_sent: true
verify_exit_codes:
- polls: 6× exit 3 (partial)
- final_exit: 3
send_max_report_exit: 0
webhook_retrigger: true (attempt 3, HTTP 202 pid 1777788)
platforms:
  max: ok
  telegram: fail (VPS pending, missing nmorozova_emdr + natalia_morozova_psy)
  vk_profile: ok
  vk_group: ok
  facebook: ok (published)
  ok: ok (published)
  b17: ok (published, draft_saved: false)
covers:
  local_cover: ok
  site_cover: ok
vps:
  finish_json: false
  handoff_done: false
issues:
- Telegram: не отправлен (VPS phase 3 не завершил)
- Тема всё ещё in_progress в очереди
- VPS phase 3: нет finish
links:
  max: https://max.ru/se13417616_biz/AZ_XBdn_Rvg
  vk_profile: https://vk.com/wall218367867_658
  vk_group: https://vk.com/wall-224685309_158
  facebook: https://www.facebook.com/632301483303094_122181324560837712
  ok: https://ok.ru/group/70000034253679/topic/161356610105455
  b17: https://www.b17.ru/blog/chto_ya_govoryu_sebe_kogda_trevoga_zashkalivaet/
incidents_written:
- INC-20260807-1256-sb10-telegram-vps-recurrence
fixic_needed: true
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260807-1256-sb10-telegram-vps-recurrence
