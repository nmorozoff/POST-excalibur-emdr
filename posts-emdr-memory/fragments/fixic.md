=== POSTS-EMDR-FIXIC ===
Статус: fixed
incidents_handled:
- INC-20260806-1300-grsai-missing-post-sections
- INC-20260806-1345-telegram-vps-not-published
files_changed:
- scripts/grsai-generate-topic.py
- scripts/posts_emdr_env.py
- scripts/cloud_preflight.py
- scripts/send-telegram-post.py
- posts-emdr-memory/cloud-secrets-checklist.txt
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/grsai-generate-topic.py scripts/posts_emdr_env.py scripts/cloud_preflight.py scripts/send-telegram-post.py
incident_report: none
