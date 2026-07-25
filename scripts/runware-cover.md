# Runware GPT Image 2 — обложки постов

Модель: `openai:gpt-image@2`  
Документация: https://runware.ai/docs/models/openai-gpt-image-2

## Стандарт проекта

| Параметр | Значение |
|----------|----------|
| Размер | **1280 × 1024** (5:4) |
| Quality | **low** (достаточно для соцсетей) |
| Формат | PNG |
| Референс | обязателен (`0C2A3279.jpg` или другой портрет) |
| Когда | **один раз на шаге Макс** → `cover.png` |

Дефолты в `posts-emdr-memory/runware.env.local`.

## Правило

**Runware API — только с явного разрешения пользователя.**  
Запрещены тестовые, диагностические и повторные генерации «на всякий случай».

## Генерация

```bash
python scripts/runware-cover.py \
  --prompt-file posts-emdr-memory/output/01-panic-night/cover-prompt.txt \
  --reference "/Users/natala/Desktop/РЕФЕРЕНСЫ/0C2A3279.jpg" \
  --output posts-emdr-memory/output/01-panic-night/cover.png
```

Без `--width/--height/--quality` скрипт читает env; можно переопределить флагами.

**Важно:** `reference` обязателен — без него лицо на обложке будет чужим.

## Параметры API

- `providerSettings.openai.quality`: `low` | `medium` | `high` | `auto` — для постов используем **low**
- `inputs.referenceImages`: data URI или URL референс-портрета
- `includeCost: true` — стоимость в ответе

## Fallback

Если Runware недоступен: Gemini в браузере (`scripts/gemini-cover-browser.md`) или MCP `gpt-image-2` с `input_urls`.
