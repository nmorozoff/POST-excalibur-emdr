---
name: director-posts-emdr
description: Директор Посты EMDR — мультиплатформенный контент из файла тем (без Ядрышка)
---

# Директор Посты EMDR

Расширение Excalibur для соцсетей Натальи Морозовой.

## Отличие от Excalibur Blog

| Excalibur Blog | Посты EMDR |
|----------------|------------|
| Ядрышко → SEO статья 8.5k | Тема из txt → посты |
| WordPress publish | Макс, TG, VK, LI, FB |
| Kie quad cover | Runware 5:4 1280×1024 — **один раз на шаге Макс**, дальше тот же `cover.png` |

## Обязательное чтение перед генерацией

1. `posts-emdr-memory/profile/tone-of-voice.md`
2. `posts-emdr-memory/profile/author-profile.md`
3. `posts-emdr-memory/profile/max-post-prompt.md` — объём 3500–3800, EMDR-блок, CTA
4. `posts-emdr-memory/profile/emdr-evidence.md` — факты ВОЗ 2013, не «признан ВОЗ»
5. Реестры перелинковки (**отдельный файл на платформу**, не общий):
   - `profile/max-posts-registry.md`
   - `profile/telegram-posts-registry.md`
   - `profile/vk-profile-posts-registry.md`
   - `profile/vk-group-posts-registry.md`
   - `profile/facebook-posts-registry.md`
6. `posts-emdr-memory/profile/crosslink-rules.md` — правила: URL только внутри своей сети
7. `posts-emdr-memory/topics/blog-topics.md` — верхняя pending
8. `posts-emdr-memory/profile/site-url-map.md`
9. `posts-emdr-memory/profile/post-types.md`

## Генерация MAX (шаг 1) — контракт выхода

### max-circle-script.md

```markdown
# Кружок Макс — {title}
Длительность: ~{N} сек

## Текст для записи (устно)

[полный текст разбитый на блоки по секундам]

## Заметки
- тон: ...
- не говорить: ...
```

### max-post.md

Пост для канала Макс. **3500–3800 символов.**  
CTA: «на моем сайте [ТУТ]» + `[ЛС](https://max.ru/id771605638595_bot)` отдельной строкой.  
Заголовок: профессиональный термин «паническая атака»; на обложке — 3 строки, без дубля слов.

### cover-prompt.txt + cover.png

По `profile/social-cover-prompt-template.md`. **Генерация один раз здесь** (quality **low**, только с разрешения пользователя).  
Runware → `cover.png` → все остальные платформы без повторного запуска.

## Правила рерайта

| Из → В | Правило |
|--------|---------|
| Макс → Telegram | +20% глубины, можно списки |
| Макс → VK профиль | больше «я», личнее |
| Макс → VK группа | экспертнее, структура |
| Макс → LinkedIn | -мат, +бизнес-угол, хештеги |
| Макс → Facebook | теплее, короче LinkedIn |

Смысл и факты **не менять**. Менять форму и длину.

## CTA шаблон

**Макс / Telegram / Facebook:** якорь «ТУТ» в markdown или HTML.

**ВК:** перелинковка VK→VK — `[https://vk.com/wall…|здесь]`; сайт и ЛС — **полный URL** (см. `profile/vk-post-prompt.md`).

```
…EMDR и страница темы с ?utm_source платформы…

Записаться на бесплатную пробную сессию можно на моем сайте ТУТ или написать мне в ЛС ТУТ.
```

- Сайт «ТУТ» → `{site_url}?utm_source={platform}` (VK: без «ТУТ», строка `на моем сайте: {url}`)
- ЛС «ТУТ» → Макс: `https://max.ru/id771605638595_bot`; остальное: `https://t.me/natalyamorozovaa`

## Telegram publish

```bash
python scripts/send-telegram-post.py --topic {topic_id} --publish
```

**Один пост в канале** (обложка над текстом, `link_preview`). Не использовать `photo_then_text`.  
После publish проверить `telegram-publish-log.json`: `link_preview_single_message`, один `message_id` на канал.

## Закрытие темы

После публикации на каждой платформе — строка в **её** реестр (`scripts/update-post-registry.py --platform …`).  
VK: две строки (профиль и группа — разные файлы). Telegram: до 3 строк (по каналам).

## Incident memory + Fixic

Перед run: `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`  
Контракт: `posts-emdr-memory/shared/pipeline-incident-fix-contract.md`

Каждый шаг пишет fragment с `incident_report: none` или ссылкой на INC в `pipeline-fix-queue.md`.

После `=== POSTS EMDR DONE ===`:

```bash
python scripts/incident_queue.py --project-root .
```

Код `2` → **Task(`posts-emdr-fixic`)** (fallback: `generalPurpose` + `agents/posts-emdr-fixic.md`).
