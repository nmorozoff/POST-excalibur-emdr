=== POSTS-EMDR-FIXIC ===
Статус: monitoring
incidents_handled:
- INC-20260909-0915-vk-flood-control
files_changed:
- scripts/is-topic-published.py
- scripts/run-cloud-publish.py
- posts-emdr-memory/profile/cloud-automation-runbook.md
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/pipeline-fix-queue.md
checks:
- python3 -m py_compile scripts/is-topic-published.py scripts/run-cloud-publish.py
- python3 scripts/is-topic-published.py --topic sb-28-end-workday-ritual --json (awaiting_mcp, exit 2)
- python3 scripts/run-cloud-publish.py --sync (awaiting_mcp, без publish-topic, 3s)
- MCP VK personal 2026-09-10: Flood control (одна попытка)
incident_report: monitoring — VK flood limit; sb-28 ждёт следующего cron для MCP VK
