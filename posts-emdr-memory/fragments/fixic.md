=== POSTS-EMDR-FIXIC ===
Статус: needs-human
incidents_handled:
- INC-20260819-1745-sb19-vps-webhook-connection-reset (needs-human: VPS webhook down, connection reset)
files_changed:
- scripts/vps_webhook_client.py
- scripts/trigger-vps-webhook.py
- scripts/verify-vps-webhook-secret.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/profile/browser-autonomous-vps.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/vps_webhook_client.py scripts/trigger-vps-webhook.py scripts/verify-vps-webhook-secret.py
- curl http://195.209.210.45:8787/health → Connection reset by peer (VPS still down)
- python3 scripts/trigger-vps-webhook.py --topic sb-19-question-before-sleep --dry-run → exit 3, vps_down true
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260819-1745-sb19-vps-webhook-connection-reset
