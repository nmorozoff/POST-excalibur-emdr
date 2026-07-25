=== POSTS-EMDR-FIXIC ===
Статус: ✅ fixed
Кратко: собран контур Fixic (contract, queue, skill, agent, incident_queue.py); закрыты 8 INC из sb-01/sb-02.

incidents_handled:
- INC-20260723-1430-telegram-photo-then-text (already fixed)
- INC-20260725-1200-b17-cover-announcement-only (already fixed)
- INC-20260725-1215-tenchat-text-truncated (already fixed)
- INC-20260725-1220-tenchat-cover-paperclip (already fixed)
- INC-20260725-1230-undetectable-cyrillic-fill (already fixed)
- INC-20260725-1240-mcp-kv-auth-intermittent (already fixed)
- INC-20260725-1250-zernio-409-duplicate (already fixed)
- INC-20260725-1300-b17-tenchat-manual-publish-click → `--submit` + click_button_by_text

files_changed:
- posts-emdr-memory/shared/*
- posts-emdr-memory/pipeline-fix-queue.md
- skills/posts-emdr-fixic/SKILL.md
- agents/posts-emdr-fixic.md
- scripts/incident_queue.py
- scripts/undetectable_browser.py
- scripts/publish-b17-blog.py
- scripts/publish-tenchat-post.py
- .cursor/rules/posts-emdr-orchestrator.mdc

checks:
- python scripts/incident_queue.py → OPEN_INCIDENTS=0 exit 0
- py_compile incident_queue.py undetectable_browser.py

incident_report: none
