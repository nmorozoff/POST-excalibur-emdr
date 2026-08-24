=== POSTS-EMDR-FIXIC ===
Статус: needs-human
incidents_handled:
- INC-20260824-0956-sb23-vps-pending
files_changed:
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/profile/browser-autonomous-vps.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- incident_queue: OPEN_INCIDENTS=1 (needs-human, не fixed)
- verify-publish-run sb-23: fail (TG+b17 pending)
- VPS /health: ok
- trigger-vps-webhook --dry-run: ok
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260824-0956-sb23-vps-pending
