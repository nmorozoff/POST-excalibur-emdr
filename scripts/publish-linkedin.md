# Публикация в LinkedIn

## Предусловия

- Готов `posts-emdr-memory/output/{topic_id}/linkedin-post.md`
- Обложка: `posts-emdr-memory/output/{topic_id}/cover.png`

## Вариант A — ручная (пока нет API)

1. Открыть https://www.linkedin.com/feed/
2. «Начать пост» → добавить фото (cover.png)
3. Вставить текст из `linkedin-post.md`
4. Опубликовать
5. Записать URL в `publish-log.md`

## Вариант B — браузерная автоматизация (Cursor browser MCP)

1. `browser_navigate` → LinkedIn feed (сессия залогинена)
2. Клик «Создать пост»
3. Загрузить cover.png
4. `browser_type` текст поста
5. Опубликовать
6. Screenshot evidence → `output/{topic_id}/linkedin-publish.png`

## Вариант C — API (будущее)

LinkedIn Marketing API требует app + OAuth. Добавить в `posts-emdr-memory/site.env.local` когда настроено.

## Чеклист

- [ ] Hook в первой строке
- [ ] 3–5 хештегов в конце
- [ ] CTA: Telegram @natalyamorozovaa
- [ ] Ссылка на morozovanatalia.ru
