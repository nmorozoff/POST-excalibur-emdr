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
- curl http://195.209.210.45:8787/health → Connection reset by peer (VPS still down, 2026-08-19)
- python3 scripts/trigger-vps-webhook.py --topic sb-19-question-before-sleep --dry-run → exit 3, vps_down true, kind connection_reset
human_actions:
- SSH на VPS 195.209.210.45: systemctl status/restart posts-emdr-webhook; curl localhost:8787/health
- После health OK: python3 scripts/trigger-vps-webhook.py --topic sb-19-question-before-sleep → 202
- Дождаться Telegram + b17; verify-publish-run.py --topic sb-19-question-before-sleep
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260819-1745-sb19-vps-webhook-connection-reset
