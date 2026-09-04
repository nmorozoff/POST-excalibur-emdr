# Cloud Automation — runbook (живёт в репозитории)

Обновляется через `git pull` — **не** копировать в Dashboard.

---

## Главное

Один пост за прогон. **VPS не вызывать.** Handoff пишут скрипты.

**Оркестратор:** `scripts/run-cloud-publish.py` — скрипты и ретраи; агент только MCP VK/OK.

b17/TenChat не блокируют закрытие темы.

---

## Фаза A — скрипты (автоматически)

```bash
git pull origin main
python3 scripts/run-cloud-publish.py --sync
```

Скрипт сам: intake, grsai (если нет md), `publish-topic.py`, Telegram до 3 попыток, `cloud-mcp-bundle.json`.

Ответ JSON: `"status": "awaiting_mcp"`, `"topic"`, `"mcp_bundle"`.

Если `queue_empty` или `already_published` — стоп, новую тему не начинать.

---

## Фаза B — только MCP (агент)

Открыть `posts-emdr-memory/output/{topic}/cloud-mcp-bundle.json`.

### VK — `vk_create_post_with_photo` ×2

По `calls` из bundle (профиль + группа `224685309`, `from_group: true` для группы).

`photo_url` / `cover_public_url` — **только** из bundle (morozovanatalia.ru/social-covers, не oneme.ru).

После каждого поста:

```bash
python3 scripts/record-vk-mcp-publish.py --topic {id} --location personal \
  --wall-url "https://vk.com/wall..." --title "..." --site-url "..." --tags "..."

python3 scripts/record-vk-mcp-publish.py --topic {id} --location group --from-group \
  --wall-url "https://vk.com/wall-224685309_..." --title "..." --site-url "..." --tags "..."
```

### OK — `ok_create_post_with_photo`

По `ok` в bundle → затем `record-ok-publish.py` из `record_after`.

**Не** `send-vk-post.py --delete-cover`.

---

## Фаза C — закрытие (автоматически)

```bash
python3 scripts/run-cloud-publish.py --topic {id} --finish
```

Скрипт: `close-cloud-publish.py`, `verify-publish-run.py`, отчёт в Макс, `git commit` + `push`.

`pass_b17_pending` = успех.

---

## Если Run «упал»

| Симптом | Действие |
|--------|----------|
| Telegram без обложки | `python3 scripts/send-telegram-post.py --topic {id} --publish --refresh-cover-url` |
| VK/OK не в реестре | повторить MCP + `record-vk-mcp-publish.py` / `record-ok-publish.py` |
| verify fail | смотреть `verify-publish-run.json`, дозаполнить логи, снова `--finish` |
| open incidents | `python3 scripts/incident_queue.py --project-root .` → Fixic |

Не выдумывать шаги. Не редактировать `.cursor/posts-emdr-handoff.md` вручную.

---

## Запреты

- VPS webhook, `publish-browser-deferred`
- `TELEGRAM_CHANNEL_CHAT_IDS=CHANNEL_HANDLE`
- `photo_then_text` в Telegram
- Каналы `@natalia_morozova_psy`, `@morozova_emdr`
- LinkedIn, Ядрышко/Core
- Помечать published вручную — только `close-cloud-publish.py` / `--finish`
