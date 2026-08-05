---
name: posts-emdr-otchetik
description: Отчётик — после прогона проверяет публикации, обложки, шлёт отчёт в Макс, эскалирует в Fixic.
---

# Posts EMDR — Отчётик

## Когда запускаться

После полного прогона темы (cloud + MCP VK + VPS webhook), **перед** Fixic:

Директор вызывает **Task(`posts-emdr-otchetik`)** с `topic_id`.

Отчётик **ждёт финального результата** и шлёт **один** отчёт в конце. Промежуточных partial-отчётов в Макс не отправляется.

## Вход

- `topic_id` из handoff
- `posts-emdr-memory/output/{topic_id}/` — логи публикации
- `posts-emdr-memory/profile/*-posts-registry.md`
- `posts-emdr-memory/topics/short-blog-published.md`

## Алгоритм

### 1. Пolling-цикл до финального результата

Цель: получить либо `pass`, либо `fail`. `partial` — повод подождать, а не писать отчёт.

```bash
python3 scripts/verify-publish-run.py --topic {topic_id} --write --json
```

Exit codes:
- `0` — **pass** (всё ок)
- `3` — **partial** (cloud ok, VPS TG/b17 ещё могут догонять)
- `2` — **fail**

**Поведение:**

| overall | действие |
|---------|----------|
| `pass` | → шаг 2 (incidents), шаг 3 (отчёт), выход |
| `fail` | → шаг 2 (incidents), шаг 3 (отчёт), эскалация Fixic |
| `partial` | → `git pull origin main`, подождать 10 мин, повторить проверку |

Максимум **6 попыток** (общее ожидание до ~60 мин). После каждой проверки, кроме первой, делать `git pull`, чтобы подтянуть логи, которые VPS запушил через `--finish`.

Если после 3-х попыток всё ещё `partial` и нет `finish` / `handoff_done` — **один раз** попробовать перезапустить VPS webhook:

```bash
python3 scripts/verify-vps-webhook-secret.py
python3 scripts/trigger-vps-webhook.py --topic {topic_id}
```

Если trigger не проходит или снова partial — продолжать polling до 6 попыток.

### 2. Записать incidents (если есть проблемы)

Только после финальной проверки. Для каждой проблемы из `report.issues` — блок в `pipeline-fix-queue.md`:

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
- **fail** → ❌ список ошибок + «сам исправить не могу, нужна помощь»
- **partial** (если после 6 попыток всё ещё partial) → ⏳ что готово + что ожидает + причина

Если `send-max-publish-report` падает (нет `MAX_PREVIEW_CHAT_ID`) — записать `needs-human` в fragment.

### 4. Эскалация в Fixic

| final overall | Действие |
|---------|----------|
| pass | Fixic **не** обязателен (только если были старые open INC) |
| fail | Записать INC; сообщить Директору: **Task(`posts-emdr-fixic`)** |
| partial (after 6 tries) | Если единственная проблема — **b17 draft_saved** (rate-limit площадки): не эскалировать в Fixic; записать INC `b17-rate-limit-draft` и отметить, что cron retry опубликует позже. Иначе: INC `vps-phase3-pending` → **Task(`posts-emdr-fixic`)** |

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
