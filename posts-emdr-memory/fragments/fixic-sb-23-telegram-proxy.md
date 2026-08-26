=== POSTS-EMDR-FIXIC ===
Статус: fixed
incidents_handled:
- INC-20260826-0948-sb23-telegram-proxy-no-rotate
files_changed:
- scripts/asocks_sync_proxy.py
- scripts/publish-browser-deferred.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/asocks_sync_proxy.py scripts/publish-browser-deferred.py
incident_report: none

Root cause: один KZ ASocks port (231489552). После timeout Bot API `exclude_port_ids` исключал порт → preflight sync не пробовал candidates → AssertionError → fallback subprocess без `--preflight`/`exclude` → тот же sticky port на attempts 2–3.

Fix: ASocks `/v2/proxy/refresh/{portId}` когда все candidates excluded; убран subprocess-fallback; CLI `--exclude-port-ids` для preflight.

VPS recovery (владелец): git pull → kill hung worker если lock >45 мин → один trigger-vps-webhook sb-23 → verify.
