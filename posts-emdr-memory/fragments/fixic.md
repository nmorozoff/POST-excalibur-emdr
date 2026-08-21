=== POSTS-EMDR-FIXIC ===
Статус: fixed
incidents_handled:
- INC-20260821-0950-telegram-vps-proxy-timeout
files_changed:
- scripts/send-telegram-post.py
- scripts/asocks_sync_proxy.py
- scripts/asocks_check.py
- scripts/publish-browser-deferred.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/browser.env.example
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/send-telegram-post.py scripts/asocks_sync_proxy.py scripts/asocks_check.py scripts/publish-browser-deferred.py
incident_report: none

Human на VPS (sb-21-minute-silence):
1. git pull origin main
2. python3 scripts/asocks_check.py --target telegram --rotate
3. python3 scripts/trigger-vps-webhook.py --topic sb-21-minute-silence
4. verify-publish-run.py --topic sb-21-minute-silence после 10–15 мин
