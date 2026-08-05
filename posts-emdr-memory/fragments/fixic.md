=== POSTS-EMDR-FIXIC ===
Статус: needs-human
incidents_handled:
- INC-20260805-1240-sb08-vps-phase3-pending
- INC-20260804-1742-sb07-vps-phase3-pending
files_changed:
- scripts/posts_emdr_env.py
- scripts/cover_upload.py
- scripts/send-vk-post.py
- scripts/vk_publish.py
- scripts/publish-zernio-post.py
- scripts/publish-topic.py
- scripts/trigger-vps-webhook.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/posts_emdr_env.py scripts/cover_upload.py scripts/send-vk-post.py scripts/vk_publish.py scripts/publish-zernio-post.py scripts/publish-topic.py scripts/trigger-vps-webhook.py
- python3 scripts/trigger-vps-webhook.py --topic sb-08-anxiety-for-loved-ones --dry-run (200)
- python3 scripts/trigger-vps-webhook.py --topic sb-08-anxiety-for-loved-ones (202, git_pull OK)
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260805-1240-sb08-vps-phase3-pending
