# POST-excalibur-emdr

Мультиплатформенный пайплайн контента для Натальи Морозовой (EMDR):  
**Макс → Telegram → VK×2 → Facebook → b17 → TenChat**.

## Структура

- `posts-emdr-memory/` — brief, очередь тем, профиль, output, incidents
- `scripts/` — публикация и автоматизация
- `skills/` — директор и Fixic
- `.cursor/rules/` — оркестратор

## Секреты

Скопируйте `*.env.example` → `*.env.local` в `posts-emdr-memory/` (не коммитятся).

## Проверка incidents перед run

```bash
python scripts/incident_queue.py --project-root .
```

## Очередь short-blog

`posts-emdr-memory/topics/short-blog-queue.md`
