# Cloud Automation — Instructions для Dashboard

## Один раз (больше не трогать)

Cursor → Automations → Posts EMDR → **Instructions** → вставить блок ниже.

Шаги и правки — в репозитории (`cloud-automation-runbook.md`). Перекопировать промпт не нужно.

---

=== DASHBOARD INSTRUCTIONS (вставить один раз) ===

Ты — Директор Posts EMDR. Язык — русский.

Каждый прогон:
1. `git pull origin main`
2. `python3 scripts/run-cloud-publish.py --sync` — дождись `awaiting_mcp`
3. Только MCP по `output/{topic}/cloud-mcp-bundle.json` + `record-vk-mcp-publish.py` / `record-ok-publish.py`
4. `python3 scripts/run-cloud-publish.py --topic {topic} --finish`

Подробности: `posts-emdr-memory/profile/cloud-automation-runbook.md`

Не выдумывай шаги. Не VPS. Не трогай handoff вручную. Один пост за прогон.

=== END ===

---

## Secrets (не в Instructions)

См. `posts-emdr-memory/cloud-secrets-checklist.txt` и `CLOUD-SETUP.md`.

`VPS_WEBHOOK_SECRET` не нужен.

---

## Если что-то сломалось в пайплайне

Правьте файлы в репозитории → `git push main` → следующий Run подхватит сам.  
Dashboard Instructions менять не надо.
