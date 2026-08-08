=== POSTS-EMDR-FIXIC ===
Статус: fixed
incidents_handled:
- INC-20260808-1227-sb11-vps-phase3-pending
files_changed:
- scripts/send-telegram-post.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/send-telegram-post.py
- python3 scripts/trigger-vps-webhook.py --topic sb-11-plant-wrong-pot (202, git_pull 18f3853)
- python3 scripts/verify-publish-run.py --topic sb-11-plant-wrong-pot (pass)
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260808-1227-sb11-vps-phase3-pending
