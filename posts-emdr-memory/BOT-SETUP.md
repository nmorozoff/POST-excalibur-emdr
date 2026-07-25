# Настройка доставки в бот

## Файлы для ключей — уже созданы

Ничего копировать не нужно. Откройте и вставьте значения:

| Файл | Назначение |
|------|------------|
| [`max.env.local`](./max.env.local) | Токен бота Макс + chat_id |
| [`runware.env.local`](./runware.env.local) | API Runware для обложек |
| [`telegram.env.local`](./telegram.env.local) | Опционально, если не через mcp-kv |

Карта: [`КУДА-ВСТАВИТЬ-КЛЮЧИ.md`](./КУДА-ВСТАВИТЬ-КЛЮЧИ.md)

**Быстро:** Cmd+P → `max.env.local`  
**Терминал:** `./scripts/open-secrets.sh`

---

## ⚠️ Токен НЕ присылайте в чат Cursor

Только в локальные `.env.local` (в `.gitignore`).

---

## Макс

Файл: **`posts-emdr-memory/max.env.local`** — токен и chat_id уже настроены.

```bash
# Превью в ЛС с ботом (по умолчанию)
python scripts/send-max-draft.py --topic 01-panic-night

# Публикация в канал — только после проверки превью
python scripts/send-max-draft.py --topic 01-panic-night --publish

# chat_id лички с ботом
python scripts/send-max-draft.py --resolve-chat-id
```

Подробнее: [`scripts/send-max-draft.md`](../scripts/send-max-draft.md)

**Важно:** без `--publish` сообщение идёт в **личку**, не в канал.

---

## Telegram (черновики / публикация)

Файл: **`posts-emdr-memory/telegram.env.local`**

```bash
# Превью / публикация — ОДНО сообщение (обложка + текст)
python scripts/send-telegram-post.py --topic 01-panic-night
python scripts/send-telegram-post.py --topic 01-panic-night --publish
```

**Важно:** не использовать `--delivery photo_then_text` для каналов — это два сообщения (фото отдельно, текст отдельно).  
После publish в логе: `"delivery": "link_preview_single_message"`.

Контракт: `profile/telegram-post-prompt.md`

**Альтернатива:** MCP `telegram_send_message` + `telegram_send_photo` — только если осознанно нужен другой формат.

---

## Runware (обложки)

Файл: **`posts-emdr-memory/runware.env.local`**

```env
RUNWARE_API_KEY=   ← ключ с https://runware.ai/
```

Генерация: `python scripts/runware-cover.py ...` (см. `scripts/runware-cover.md`)

---

## Альтернатива без ботов

Тексты и обложки лежат в `posts-emdr-memory/output/{topic_id}/` — копируете вручную.
