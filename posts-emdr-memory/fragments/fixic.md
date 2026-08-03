=== POSTS-EMDR-FIXIC ===
Статус: needs-human
incidents_handled:
- INC-20260803-1030-runware-credits (needs-human: Runware wallet; durable: kie-cover primary + runware hint)
- INC-20260803-1045-tenchat-session-blocks-vps (fixed)
files_changed:
- scripts/runware-cover.py
- scripts/publish-browser-deferred.py
- scripts/browser_worker_finish.py
- scripts/vps-webhook-server.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python -m py_compile scripts/runware-cover.py scripts/publish-browser-deferred.py scripts/browser_worker_finish.py scripts/vps-webhook-server.py
incident_report: none
