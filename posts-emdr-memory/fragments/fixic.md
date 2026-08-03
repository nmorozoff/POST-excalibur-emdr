=== POSTS-EMDR-FIXIC ===
Статус: fixed
incidents_handled:
- INC-20260803-1030-runware-credits
- INC-20260803-1045-tenchat-session-blocks-vps
files_changed:
- scripts/posts_emdr_env.py
- scripts/browser_worker_finish.py
- scripts/publish-browser-deferred.py
- scripts/publish-topic.py
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/browser_worker_finish.py scripts/publish-browser-deferred.py scripts/publish-topic.py scripts/posts_emdr_env.py
- python3 scripts/incident_queue.py --project-root . → OPEN_INCIDENTS=0
incident_report: none
