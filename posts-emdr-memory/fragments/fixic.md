=== POSTS-EMDR-FIXIC ===
Статус: fixed
incidents_handled:
- INC-20260804-1405-sb06-vps-phase3-stuck
- INC-20260804-1405-sb06-facebook-zernio-scheduled
files_changed:
- scripts/verify-publish-run.py
- scripts/publish-zernio-post.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/verify-publish-run.py scripts/publish-zernio-post.py
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260804-1405-sb06-facebook-zernio-scheduled
