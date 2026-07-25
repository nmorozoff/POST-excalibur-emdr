# Доставка в Макс

## Два режима (важно!)

| Команда | Куда | Текст |
|---------|------|-------|
| `python scripts/send-max-draft.py --topic 01-panic-night` | **ЛС с ботом** (`MAX_PREVIEW_CHAT_ID`) | С шапкой «Черновик» |
| `python scripts/send-max-draft.py --topic 01-panic-night --publish` | **Канал** (`MAX_CHANNEL_CHAT_ID`) | Чистый пост, без шапки |

По умолчанию — **превью в ЛС**, не в канал.

## Настройка

1. `MAX_CHANNEL_CHAT_ID` — ID канала (уже есть)
2. `MAX_PREVIEW_CHAT_ID` — личка с ботом:
   ```bash
   python scripts/send-max-draft.py --resolve-chat-id
   ```
   Напишите боту «старт» в ЛС.

## Обложка

Скрипт берёт `cover-runware.png`, если есть; иначе `cover.png`.

Генерация Runware (с вашим лицом из референса):
```bash
python scripts/runware-cover.py \
  --prompt-file posts-emdr-memory/output/01-panic-night/cover-prompt.txt \
  --reference "/Users/natala/Desktop/РЕФЕРЕНСЫ/0C2A3279.jpg" \
  --output posts-emdr-memory/output/01-panic-night/cover-runware.png
```

Нужен `RUNWARE_API_KEY` в `runware.env.local`.

## Удалить сообщение ботом

```bash
python scripts/send-max-draft.py --delete-mid mid.xxxxx
```
