=== POSTS-EMDR-FIXIC ===
Статус: fixed
incidents_handled:
- INC-20260807-1220-sb10-telegram-vps-pending
files_changed:
- scripts/posts_emdr_env.py
- scripts/publish-browser-deferred.py
- scripts/vps-webhook-server.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/cloud-secrets-checklist.txt
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/posts_emdr_env.py scripts/publish-browser-deferred.py scripts/vps-webhook-server.py
incident_report: none
