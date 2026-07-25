# Конец задачи — все шаги Posts EMDR

**Обязательно** перед завершением любого шага пайплайна.

## 1. Прочитать pitfalls

`posts-emdr-memory/shared/agent-pipeline-pitfalls.md` — не повторять известные ошибки.

## 2. Incident memory

Контракт: `posts-emdr-memory/shared/pipeline-incident-fix-contract.md`

Если в задаче был blocker, retry, workaround, несоответствие skill/API — **append** в:

`posts-emdr-memory/pipeline-fix-queue.md`

Формат INC: см. контракт. **Без секретов.**

## 3. Fragment

Путь: `posts-emdr-memory/fragments/<role>.md` + блок в `.cursor/posts-emdr-handoff.md`

Шаблон: `posts-emdr-memory/shared/subagent-fragment-template.md`

**Обязательная строка:**

```text
incident_report: none
```

или:

```text
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-YYYYMMDD-HHMM-<role>-<slug>
```

Fragment **без** `incident_report` — невалиден; Директор не переходит к следующему шагу.

## 4. Fixic (не твоя роль)

После всего run Директор вызывает `posts-emdr-fixic`, если есть open incidents. Субагент Fixic не запускает.
