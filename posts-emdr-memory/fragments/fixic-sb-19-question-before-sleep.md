=== POSTS-EMDR-FIXIC ===
topic: sb-19-question-before-sleep
Статус: needs-human
incidents_handled:
- INC-20260819-1745-sb19-vps-webhook-connection-reset (VPS webhook down — connection reset by peer)
files_changed:
- scripts/vps_webhook_client.py
- scripts/trigger-vps-webhook.py
- scripts/verify-vps-webhook-secret.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/profile/browser-autonomous-vps.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/vps_webhook_client.py scripts/trigger-vps-webhook.py scripts/verify-vps-webhook-secret.py
- Fixic probe 17:49 UTC: Connection reset by peer (VPS down)
- Fixic probe 17:52 UTC: health OK; trigger-vps-webhook --topic sb-19 → HTTP 202 (pid 1924)
- verify-publish-run.py (17:54 UTC): still fail — Telegram/b17 pending on VPS worker
human_actions:
- Дождаться завершения VPS worker (pid 1924) или проверить `output/sb-19-question-before-sleep/vps-webhook-run.log` на VPS
- Если через 15 мин всё ещё partial: SSH → journalctl -u posts-emdr-webhook; ручной publish-browser-deferred
- После finish: verify-publish-run.py --topic sb-19-question-before-sleep → pass; mark-short-blog-published
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260819-1745-sb19-vps-webhook-connection-reset
