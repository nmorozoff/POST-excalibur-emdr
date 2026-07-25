# Posts EMDR — incident memory и Fixic loop

Контракт: шаги пайплайна фиксируют проблемы → **posts-emdr-fixic** чинит durable layer (skills, scripts, prompts, pitfalls).

## Canonical files

| File | Purpose |
|------|---------|
| `posts-emdr-memory/pipeline-fix-queue.md` | durable incident memory |
| `posts-emdr-memory/fragments/*.md` | runtime handoff per step |
| `.cursor/posts-emdr-handoff.md` | Director exchange |
| `posts-emdr-memory/shared/pipeline-incident-fix-contract.md` | этот контракт |
| `posts-emdr-memory/shared/agent-pipeline-pitfalls.md` | устойчивые уроки (читать до run) |
| `agents/posts-emdr-fixic.md` | Fixic agent |
| `skills/posts-emdr-fixic/SKILL.md` | runbook Fixic |

Runtime artifacts (`output/{topic_id}/`, publish logs) — **не** место для durable fixes.

## Когда писать incident

Каждый шаг **append** в `pipeline-fix-queue.md`, если было:

- blocker, timeout, 401/403 API, schema mismatch;
- retry, workaround, fallback не из документации;
- артефакт переписан из-за неясного контракта;
- устаревший skill/script заставил лишние шаги;
- validation fail + fix «из головы»;
- пользователь поправил то, что контракт не покрывал;
- ручная публикация там, где ожидалась автоматизация.

**Не писать** если всё прошло штатно без corrective action.

## Формат incident

```markdown
## INC-YYYYMMDD-HHMM-<role>-<slug>
status: open
run_date: YYYY-MM-DD
role: posts-emdr-<role> | director | script
topic: <topic_id> | n/a
severity: low | medium | high | blocker
category: prompt | script | docs | env | api | handoff | runware | undetectable | b17 | tenchat | vk | telegram | zernio | qa | other

### What went wrong
- ...

### How the agent recovered this run
- ...

### Durable fix needed before next run
- ...

### Suggested files to inspect/change
- `path/to/file`

### Secrets
- none recorded

### Fixic resolution
- pending
```

**Запрещено** в incident: токены, пароли, приватные URL с секретами.

## Конец каждой задачи

В fragment **обязательно**:

```text
incident_report: none
```

или:

```text
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-YYYYMMDD-HHMM-role-slug
```

Шаблон: `posts-emdr-memory/shared/subagent-fragment-template.md`

## Director

После `=== POSTS EMDR DONE ===` **или** терминального blocker:

1. `python scripts/incident_queue.py --project-root .` — код `2` = есть open incidents
2. Прочитать `posts-emdr-memory/pipeline-fix-queue.md`
3. Если есть `status: open` → **Task(`posts-emdr-fixic`)**  
   Fallback: **Task(`generalPurpose`)** + `agents/posts-emdr-fixic.md` + `skills/posts-emdr-fixic/SKILL.md`
4. Не начинать новую тему с open blocker-incidents без явного OK пользователя

## Fixic

- Читает open incidents
- Правит **durable**: `skills/`, `agents/`, `scripts/`, `posts-emdr-memory/profile/`, `posts-emdr-memory/shared/`, `.cursor/rules/`
- Прогоняет минимальные checks (`py_compile`, JSON parse)
- Помечает incident `fixed` или `needs-human`
- Дополняет `shared/agent-pipeline-pitfalls.md` если урок общий

Fixic **не** публикует посты и **не** перегенерирует контент ради проверки.
