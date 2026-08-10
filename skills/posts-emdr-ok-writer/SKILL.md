---
name: posts-emdr-ok-writer
description: Рерайт max-post → ok-post.md для группы Одноклассники (MSP short-blog).
---

# Posts EMDR — OK Writer

## Роль

Написать `ok-post.md` — рерайт для публикации в группу OK.ru через MCP `ok_create_post_with_photo`.

## Перед работой

1. Прочитать `posts-emdr-memory/output/{topic_id}/max-post.md`
2. `posts-emdr-memory/profile/ok-post-prompt.md`
3. `posts-emdr-memory/profile/ok-posts-registry.md` — перелинковка
4. `posts-emdr-memory/profile/crosslink-rules.md`
5. `posts-emdr-memory/profile/short-blog-cta-rules.md` — CTA-слот по `sb-NN % 3`
6. `posts-emdr-memory/profile/tone-of-voice.md`, `author-profile.md`
7. `posts-emdr-memory/profile/site-url-map.md` — URL страницы темы

## Формат ok-post.md

```markdown
# Пост OK — {topic_id}

**Заголовок:** …
**Формат:** рерайт; теплее, умеренно эмодзи
**UTM:** `utm_source=ok`
**Обложка:** `cover.png`

---

## Текст поста

{рерайт с markdown-ссылками `[здесь](ok-url)` / `[ТУТ](site?utm_source=ok)`; без блока Обложка/Line 1}

---

## Мета

- chars: NNNN
- crosslinks: [topic_ids]
- cta_slot: 0|1|2
```

## Gate

- [ ] Рерайт, не копипаст
- [ ] ~3000–3800 знаков в `## Текст поста`
- [ ] Перелинковка только на OK из реестра
- [ ] Сайт `?utm_source=ok` и t.me — только в конце
- [ ] Открытый вопрос в финале

## Fragment

`posts-emdr-memory/fragments/ok-writer.md`:

```markdown
# OK Writer — {topic_id}

status: done
output: posts-emdr-memory/output/{topic_id}/ok-post.md

incident_report:
  incidents: []
  notes: ""
```
