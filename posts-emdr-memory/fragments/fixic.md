=== POSTS-EMDR-FIXIC ===
Статус: fixed
incidents_handled:
- INC-20260804-1405-sb06-vps-phase3-stuck
- INC-20260804-1405-sb06-facebook-zernio-scheduled
files_changed:
- scripts/publish-zernio-post.py
- scripts/verify-publish-run.py
- scripts/kie-cover.py
- scripts/trigger-vps-webhook.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/profile/cloud-automation-prompt.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/publish-zernio-post.py scripts/verify-publish-run.py scripts/kie-cover.py scripts/trigger-vps-webhook.py
incident_report: none
