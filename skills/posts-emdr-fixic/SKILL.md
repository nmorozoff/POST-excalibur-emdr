---
name: posts-emdr-fixic
description: Fixic — после run читает incidents, правит пайплайн Posts EMDR (skills, scripts, prompts, pitfalls).
---

# Posts EMDR Fixic

## Когда запускаться

После `=== POSTS EMDR DONE ===` **или** терминального blocker, если:

- `python scripts/incident_queue.py --project-root .` → код `2`, или
- в `posts-emdr-memory/pipeline-fix-queue.md` есть `status: open`.

Fixic **не** в production-path публикации — только post-run улучшение.

## Вход

- `posts-emdr-memory/pipeline-fix-queue.md`
- `posts-emdr-memory/shared/pipeline-incident-fix-contract.md`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`
- Пути из `Suggested files to inspect/change` в каждом INC
- git status / diff (если доступен)

Workspace: `{PROJECT_ROOT}` = корень `Посты EMDR`.

## Алгоритм

1. Прочитать весь `pipeline-fix-queue.md`.
2. Выбрать open-инциденты (строка `status: open` в блоке INC).
3. Сгруппировать по root cause.
4. Для каждого INC определить тип fix:
   - prompt → `posts-emdr-memory/profile/*-prompt.md`
   - script → `scripts/`
   - orchestrator → `.cursor/rules/posts-emdr-orchestrator.mdc`
   - docs → `posts-emdr-memory/shared/`
5. Внести **минимальный** durable diff.
6. Если урок общий — пункт в `shared/agent-pipeline-pitfalls.md`.
7. Проверки:
   - `python -m py_compile` на изменённых `.py`
   - JSON parse на изменённых `.json` в output **только если** менялся schema contract
8. Обновить каждый INC:

```markdown
status: fixed
fixed_at: YYYY-MM-DD
fix_summary:
- ...
files_changed:
- `...`
checks_run:
- ...
```

Или `status: needs-human` с `needed_decision_or_secret`.

**VPS phase 3 pending:** после otchetik retry — один probe `trigger-vps-webhook.py --topic {id}` (202 OK). Если через 10–15 мин всё ещё partial → `needs-human` + пункт в pitfalls (recovery playbook). Не публиковать из cloud напрямую (`send-telegram-post.py` / `publish-b17-blog.py`).

## Что править

| Можно | Нельзя |
|-------|--------|
| `skills/`, `agents/`, `scripts/`, `profile/`, `shared/`, `.cursor/rules/` | `posts-emdr-memory/output/*` как fix |
| `agent-pipeline-pitfalls.md` | secrets в memory |
| `*.env.example` | `*.env.local` пользователя |

## Выход

Fragment: `posts-emdr-memory/fragments/fixic.md`

```text
=== POSTS-EMDR-FIXIC ===
Статус: fixed | needs-human | no-open-incidents
incidents_handled:
- INC-...
files_changed:
- ...
checks:
- ...
incident_report: none
```

## Запреты

- Не закрывать INC без реального fix или `needs-human`
- Не публиковать посты в соцсети
- Не перегенерировать Runware/контент ради проверки
- Не дублировать секреты в queue/pitfalls

## Machine check

```bash
python scripts/incident_queue.py --project-root .
# OPEN_INCIDENTS=0 → exit 0
# OPEN_INCIDENTS=1 → exit 2 → нужен Fixic или needs-human resolution
```
