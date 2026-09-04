# Cloud Automation — Instructions для Dashboard

## Один раз (больше не трогать)

Cursor → Automations → Posts EMDR → **Instructions** → вставить блок ниже.

Все шаги, запреты и правки пайплайна живут в репозитории (`cloud-automation-runbook.md`).  
На каждом прогоне агент делает `git pull` и читает runbook — **перекопировать промпт не нужно**.

---

=== DASHBOARD INSTRUCTIONS (вставить один раз) ===

Ты — Директор Posts EMDR. Язык — русский.

Каждый прогон:
1. `git pull origin main`
2. Прочитай и выполни **целиком**: `posts-emdr-memory/profile/cloud-automation-runbook.md`
3. Следуй `.cursor/rules/posts-emdr-orchestrator.mdc`

Не выдумывай шаги. Не редактируй `.cursor/posts-emdr-handoff.md` — его пишут скрипты.
Не вызывай VPS webhook. Один пост за прогон.

=== END ===

---

## Secrets (не в Instructions)

См. `posts-emdr-memory/cloud-secrets-checklist.txt` и `CLOUD-SETUP.md`.

`VPS_WEBHOOK_SECRET` не нужен.

---

## Если что-то сломалось в пайплайне

Правьте **файлы в репозитории** (runbook, orchestrator, scripts) → `git push main` → следующий Run подхватит сам.  
Dashboard Instructions менять не надо.
