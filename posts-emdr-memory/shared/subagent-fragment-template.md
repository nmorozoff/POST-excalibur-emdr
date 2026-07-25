# Шаблон fragment — Posts EMDR

Каждый шаг пишет в `posts-emdr-memory/fragments/<role>.md` и блок в `.cursor/posts-emdr-handoff.md`.

```text
=== POSTS-EMDR-<ROLE> ===
Статус: ✅ OK | ⚠️ WARN | ❌ BLOCKER | ❌ FAIL
topic_id: sb-XX-slug
Кратко: ...

Артефакты:
- posts-emdr-memory/output/{topic_id}/...

incident_report: none
```

Если была проблема — сначала append в `posts-emdr-memory/pipeline-fix-queue.md`, затем:

```text
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-YYYYMMDD-HHMM-role-slug
```

## Обязательно в конце задачи

1. Статус и пути артефактов
2. **incident_report** (none или ссылка на INC)
3. Если BLOCKER — что нужно Директору/пользователю

Без `incident_report` строки fragment **невалиден**.
