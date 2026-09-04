# Cloud Automation — runbook (живёт в репозитории)

Обновляется через `git pull` — **не** копировать в Dashboard.

Агент читает этот файл на каждом прогоне. См. `cloud-automation-prompt.md` (стабильные Instructions).

---

## Задача

Опубликовать **одну** тему MSP short-blog за прогон.

**Главное:** b17 и TenChat не блокируют закрытие и следующую тему. Основной прогон: Макс, Telegram, VK, Facebook, OK → `close-cloud-publish.py`. b17/TenChat — repair с Mac.

**Handoff:** пишут скрипты (`next-short-blog-topic.py`, `close-cloud-publish.py`). Агент **не** редактирует `.cursor/posts-emdr-handoff.md` вручную.

---

## ШАГ 0 — INTAKE

```bash
git pull origin main
python3 scripts/incident_queue.py --project-root .
```

Exit `2` → Task(`posts-emdr-fixic`), новую тему не начинать.

```bash
python3 scripts/next-short-blog-topic.py --sync --json
```

- `topic_id` **только** из этого JSON (не из handoff, если расходится).
- `queue_empty` → стоп.
- `already_published_still_in_queue` → повторить `--sync`.

Читать: `shared/agent-pipeline-pitfalls.md`, `profile/tone-of-voice.md`, `profile/author-profile.md`, `profile/site-url-map.md`.

---

## ШАГ 1 — КОНТЕНТ (Grsai)

```bash
python3 scripts/is-topic-published.py --topic {id}
```

Exit `0` → тема уже закрыта, к следующей.

```bash
python3 scripts/grsai-generate-topic.py --topic {id}
```

Gate: `max-post.md`, `cover-prompt.txt`, все platform md, `grsai-content-log.json`.  
Обложка PNG — только в шаге 2 (`publish-topic.py`), не отдельными cover-скриптами.

---

## ШАГ 2 — CLOUD PUBLISH (фаза 1)

```bash
python3 scripts/materialize_cloud_env.py --check
python3 scripts/publish-topic.py --topic {id}
```

---

## ШАГ 2b — TELEGRAM

Если `telegram-publish-log.json` с `cover_source` morozovanatalia/vk — пропустить.

Иначе:

```bash
python3 scripts/publish-telegram-from-handoff.py --topic {id}
```

MCP `telegram_send_message` — только если скрипт упал дважды (обложка может пропасть).

Gate: `delivery: link_preview_single_message`, канал `@nmorozova_emdr`.

---

## ШАГ 3 — VK MCP

По `vk-mcp-handoff.json`: `vk_create_post_with_photo` ×2 (профиль + группа `224685309`).

**Не** `send-vk-post.py --delete-cover` — URL нужен для b17.

Обновить реестры max, vk-profile, vk-group, facebook, ok.

---

## ШАГ 3b — OK MCP

По `ok-mcp-handoff.json` → `ok_create_post_with_photo` → `record-ok-publish.py`.

---

## ШАГ 4 — GIT PUSH

```bash
git add posts-emdr-memory/output/{id}/ posts-emdr-memory/profile/*-posts-registry.md
git commit -m "publish: {id}"
git push
```

Если push на `cursor/*` — слить PR в `main`.

---

## ШАГ 5 — CLOUD CLOSE

```bash
python3 scripts/close-cloud-publish.py --topic {id}
```

Пишет `cloud-publish-finish.json`, очередь published, **`=== POSTS EMDR DONE ===`** в handoff.

---

## ШАГ 6 — ОТЧЁТИК

Task(`posts-emdr-otchetik`) с `topic_id`. Один отчёт в Макс. `pass_b17_pending` = OK.

---

## ШАГ 7 — FIXIC

При fail verify или open incidents → Task(`posts-emdr-fixic`).

---

## ЗАПРЕТЫ

- VPS: не `trigger-vps-webhook`, не `publish-browser-deferred`
- Не `TELEGRAM_CHANNEL_CHAT_IDS=CHANNEL_HANDLE`
- Не `photo_then_text` в Telegram
- Не `@natalia_morozova_psy` / `@morozova_emdr`
- Не LinkedIn, не Ядрышко/Core
- Не помечать published вручную — только `close-cloud-publish.py`
