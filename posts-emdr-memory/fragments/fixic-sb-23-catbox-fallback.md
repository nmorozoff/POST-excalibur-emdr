=== POSTS-EMDR-FIXIC ===
Статус: fixed
incidents_handled:
- INC-20260824-0956-sb23-vps-pending
files_changed:
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/pipeline-fix-queue.md
- posts-emdr-memory/fragments/fixic-sb-23-catbox-fallback.md
checks:
- python3 -m py_compile scripts/send-telegram-post.py
- python3 scripts/incident_queue.py --project-root . → OPEN_INCIDENTS=0
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260824-0956-sb23-vps-pending
