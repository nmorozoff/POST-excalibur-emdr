# Пост Одноклассники (группа) — контракт

Источник: `max-post.md` → **только рерайт** (перефраз, смена ритма). См. `profile/crosslink-rules.md`.

## Куда публикуем

| Поле | Значение |
|------|----------|
| Площадка | **Группа** OK.ru (не личная лента) |
| GID | `70000034253679` (или `OK_GROUP_GID` в env) |
| URL группы | `https://ok.ru/group/70000034253679` |
| MCP | `ok_create_post_with_photo` |
| Файл | `output/{topic_id}/ok-post.md` |

## Форматирование в `ok-post.md` (исходник)

Писать как в редакторе OK — с якорными ссылками и акцентами:

| Нужно | В файле |
|-------|---------|
| Ссылка-слово | `[здесь](https://ok.ru/group/.../topic/...)` |
| CTA / сайт | `читайте [ТУТ](https://morozovanatalia.ru/anxiety?utm_source=ok)` |
| Акцент | `**важная фраза**` |
| Подзаголовок | строка без `##` или короткая строка заголовка |

**Запрещено** в `## Текст поста`: блок `**Обложка:**` / `Line 1:` / `OUTFIT:` — это только для `cover-prompt.txt` / шапки Макс.

### Как уходит в API сейчас

MCP `ok_create_post_with_photo` принимает только plain `text` (без `text_tokens`).  
`publish-topic.py` → `format_ok_publish_text()`: markdown-ссылки → `слово https://url` (OK сам кликабелит URL), снимает `##` и `**`.  
В `ok-mcp-handoff.json` дополнительно пишется `text_tokens` (якоря OK MediaTextToken) — на будущее, когда MCP начнёт принимать tokens.

## Перелинковка

Только `profile/ok-posts-registry.md`. В теле — ссылки на **другие посты OK**.

```
О фоновой тревоге писала [здесь](https://ok.ru/group/70000034253679/topic/XXXXXXXXX).
```

**Не ссылаться** на VK/TG/FB/сайт в середине поста.

## Ссылки в конце (после CTA)

```
Если хотите обсудить это лично, напишите мне в ЛС: https://t.me/natalyamorozovaa

Подробности о проведении сессии, стоимости и записи читайте [ТУТ](https://morozovanatalia.ru/anxiety?utm_source=ok).
```

**Приписка** — последняя строка: `profile/client-story-disclaimer.md` (правописание: **имена**, не «имены»).

UTM: `utm_source=ok` (`profile/utm-sources.md`).

## Объём и тон

| Поле | Правило |
|------|---------|
| Длина | **~3000–3800 знаков** (как TG/VK/FB), не сокращать |
| Тон | Теплее делового, ближе к Facebook; эмодзи умеренно |
| Структура | Заголовок-строка, короткие подзаголовки, списки с `-` |
| EMDR | При тревоге/травме — блок по `profile/emdr-evidence.md` + ссылка на `/emdr-therapy?utm_source=ok` в конце |

## Обложка

Та же, что для VK/FB: `cover_public_url` из `vk-publish-prep.json`  
(`https://morozovanatalia.ru/social-covers/{topic_id}.jpg`).

Gate MCP: в ответе — подтверждение загрузки фото.

## Публикация (фаза 2 Cloud, после VK)

1. `publish-topic.py` пишет `ok-mcp-handoff.json` (если есть `ok-post.md`).
2. MCP `ok_create_post_with_photo`:
   - `text` — из handoff (уже без обложки-меты, plain)
   - `image_url` — `cover_public_url`
   - `gid`: `70000034253679`
   - `onBehalfOfGroup`: `true`
3. Записать результат:

```bash
python3 scripts/record-ok-publish.py --topic {id} \
  --url "https://ok.ru/group/70000034253679/topic/..." \
  --mediatopic-id "..." \
  --title "..." --site-url "https://morozovanatalia.ru/..." --tags "..."
```

## Запреты

- Не копипаст из Макс/TG/VK/FB.
- Не публиковать без `ok-post.md` и `cover_public_url`.
- Не тащить технические строки обложки в текст поста.
- Не использовать `link_url` в MCP для сайта — ссылка на сайт только в тексте в конце.
