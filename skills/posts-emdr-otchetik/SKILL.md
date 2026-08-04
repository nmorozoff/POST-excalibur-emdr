---
name: posts-emdr-otchetik
description: Отчётик — после прогона проверяет публикации, обложки, шлёт отчёт в Макс, эскалирует в Fixic.
---

# Posts EMDR — Отчётик

## Когда запускаться

После полного прогона темы (cloud + MCP VK + VPS webhook), **перед** Fixic:

1. Директор вызывает **Task(`posts-emdr-otchetik`)** с `topic_id`.
2. Если VPS ещё мог не отработать — подождать 10–15 мин и повторить проверку **один раз**.

Отчётик **не** заменяет Fixic — он QA + уведомление пользователя.

## Вход

- `topic_id` из handoff
- `posts-emdr-memory/output/{topic_id}/` — логи публикации
- `posts-emdr-memory/profile/*-posts-registry.md`
- `posts-emdr-memory/topics/short-blog-published.md`

## Алгоритм

### 1. Машинная проверка

```bash
python3 scripts/verify-publish-run.py --topic {topic_id} --write --json
```

Exit codes:
- `0` — **pass** (всё ок)
- `3` — **partial** (cloud ok, VPS TG/b17 ещё могут догонять)
- `2` — **fail**

### 2. Записать incidents (если есть проблемы)

Для каждой проблемы из `report.issues` — блок в `pipeline-fix-queue.md`:

```markdown
## INC-YYYYMMDD-HHMM-{slug}
status: open
run_date: YYYY-MM-DD
role: otchetik
topic: {topic_id}
severity: high|medium|low
category: {platform|cover|vps|webhook}

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
- **pass** → ✅ ссылки на все платформы
- **partial** → ⏳ что готово + что ждём от VPS
- **fail** → ❌ список ошибок + «сам исправить не могу, нужна помощь»

Если `send-max-publish-report` падает (нет `MAX_PREVIEW_CHAT_ID`) — записать `needs-human` в fragment.

### 4. Эскалация в Fixic

| overall | Действие |
|---------|----------|
| pass | Fixic **не** обязателен (только если были старые open INC) |
| partial | Записать INC `vps-pending`; **не** вызывать Fixic до повторной проверки |
| partial (после retry) | INC `vps-phase3-pending` → **Task(`posts-emdr-fixic`)**; Fixic документирует recovery (pitfalls), может один раз `trigger-vps-webhook.py` |
| fail | Записать INC; сообщить Директору: **Task(`posts-emdr-fixic`)** |

Отчётик **сам не чинит** скрипты — только incidents + отчёт. Чинит **Fixic**.

### 5. VPS infra checks (раз в прогон, если fail/partial)

При проблемах VPS — напомнить в отчёте проверить:
- `systemctl is-active posts-emdr-webhook`
- cron `run-linux-browser-worker.sh`
- `python3 scripts/asocks_check.py`
- `python3 scripts/browser_ensure_sessions.py`

## Выход

Fragment: `posts-emdr-memory/fragments/otchetik-{topic_id}.md`

```text
=== POSTS-EMDR-OTCHETIK ===
topic: {topic_id}
overall: pass|partial|fail
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

## Machine commands

```bash
python3 scripts/verify-publish-run.py --topic {id} --write
python3 scripts/send-max-publish-report.py --topic {id}
python3 scripts/incident_queue.py --project-root .
```
