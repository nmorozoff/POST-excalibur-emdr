---
name: posts-emdr-otchetik
description: Отчётик — после прогона проверяет публикации, обложки, шлёт отчёт в Макс, эскалирует в Fixic.
---

# Posts EMDR — Отчётик

## Когда запускаться

После cloud + MCP VK/OK + **close-cloud-publish.py**, **перед** Fixic:

Директор вызывает **Task(`posts-emdr-otchetik`)** с `topic_id`.

**Один** финальный отчёт в Макс. Без polling и без ожидания VPS (VPS отключён с 2026-09).

## Вход

- `topic_id` из handoff
- `posts-emdr-memory/output/{topic_id}/` — логи публикации
- `posts-emdr-memory/profile/*-posts-registry.md`
- `posts-emdr-memory/topics/short-blog-published.md`

## Алгоритм

### 1. Проверка (один раз)

Перед verify убедиться, что выполнен `close-cloud-publish.py` (есть `cloud-publish-finish.json` или тема в `short-blog-published.md`).

```bash
python3 scripts/verify-publish-run.py --topic {topic_id} --write --json
```

Exit codes:
- `0` — **pass** или **pass_b17_pending** (5 платформ OK; b17 в repair — не fail)
- `2` — **fail**
- `3` — **partial** (обычно Facebook scheduled у Zernio — можно один git pull + повтор через 10 мин, макс. 2 попытки)

**Не вызывать:** `trigger-vps-webhook.py`, `verify-vps-webhook-secret.py`, `publish-browser-deferred.py`.

| overall | действие |
|---------|----------|
| `pass` / `pass_b17_pending` | → шаг 2, шаг 3, выход |
| `fail` | → шаг 2, шаг 3, эскалация Fixic |
| `partial` | → один `git pull`, подождать 10 мин, повторить verify (макс. 2 раза); если всё ещё partial — отчёт с пометкой Zernio pending |

### 2. Записать incidents (если есть проблемы)

Только после финальной проверки. Для каждой проблемы из `report.issues` — блок в `pipeline-fix-queue.md`:

```markdown
## INC-YYYYMMDD-HHMM-{slug}
status: open
run_date: YYYY-MM-DD
role: otchetik
topic: {topic_id}
severity: high|medium|low
category: {platform|cover|cloud}

### What went wrong
- ...

### Durable fix needed before next run
- ...

### Suggested files to inspect/change
- ...
```

**Не дублировать** уже open INC с той же root cause.

### 3. Отчёт в Макс

```bash
python3 scripts/send-max-publish-report.py --topic {topic_id}
```

Текст отчёта:
- **pass** / **pass_b17_pending** → ✅ ссылки на 5 платформ; b17 pending — отдельной строкой «repair с Mac», не как ошибка
- **fail** → ❌ список ошибок + «нужна помощь»
- **partial** (Facebook scheduled) → ⏳ что готово + «ждём Meta retry»

Если `send-max-publish-report` падает — записать `needs-human` в fragment.

### 4. Эскалация в Fixic

| final overall | Действие |
|---------|----------|
| pass / pass_b17_pending | Fixic не обязателен (если нет старых open INC) |
| fail | INC + **Task(`posts-emdr-fixic`)** |
| partial (после 2 попыток) | INC только если не единственная причина — Zernio scheduled |

Отчётик **не чинит** скрипты — только incidents + отчёт.

## Выход

Fragment: `posts-emdr-memory/fragments/otchetik-{topic_id}.md`

```text
=== POSTS-EMDR-OTCHETIK ===
topic: {topic_id}
overall: pass|pass_b17_pending|partial|fail
max_report_sent: true|false
incidents_written:
- INC-...
fixic_needed: true|false
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-... | none
```

Также: `output/{topic}/publish-run-report.json`

## Запреты

- Не перепубликовывать посты
- Не вызывать Kie/Runware
- Не закрывать INC без Fixic
- Не слать отчёт в канал Макс — только **ЛС** (`MAX_PREVIEW_CHAT_ID`)
- Не упоминать VPS webhook / phase 3 / trigger-vps в отчётах

## Machine commands

```bash
python3 scripts/close-cloud-publish.py --topic {id}   # если ещё не было
python3 scripts/verify-publish-run.py --topic {id} --write
python3 scripts/send-max-publish-report.py --topic {id}
python3 scripts/incident_queue.py --project-root .
```
