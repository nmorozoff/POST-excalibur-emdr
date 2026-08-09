=== POSTS-EMDR-FIXIC ===
Статус: needs-human
incidents_handled:
- INC-20260809-1118-ok-mcp-token-expired (needs-human: Dashboard re-auth OK mcp-kv)
- INC-20260809-1120-grsai-telegram-b17-gate (fixed)
files_changed:
- scripts/grsai-generate-topic.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/profile/cloud-publish-phases.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/grsai-generate-topic.py
- smoke: ensure_b17_blank_lines, truncate_telegram_html, ensure_platform_contract(b17)
incident_report: none
