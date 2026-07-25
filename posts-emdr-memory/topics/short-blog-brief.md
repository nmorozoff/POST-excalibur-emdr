# Короткие посты — бриф и промпт

**Источник:** `topics/short-blog-msp-source.txt` (копия MSP Этап-2)  
**Очередь:** `topics/short-blog-queue.md` — брать **первую** тему; после публикации удалить из очереди.  
**CTA:** `profile/short-blog-cta-rules.md` — гибрид MSP + EMDR (не как в MSP «без CTA почти всегда»).

## Отличие от длинных постов (серия WB и т.п.)

| | Длинный пост | Короткий (эта очередь) |
|--|--------------|------------------------|
| Объём Макс | 3500–3800 | **600–1200** |
| Тон | экспертный лонгрид | дневник, одна мысль |
| CTA | полный блок сессии **в каждом** | вопрос + **мягкий контакт всегда**; полный CTA — **каждый 4-й** (#04, #08…) |
| Структура | шаблоны post-types | 6 форматов из брифа MSP |

## 6 форматов (чередовать)

1. Бытовое наблюдение → инсайт  
2. Метафора из жизни  
3. Реакция на новость/исследование  
4. Личная уязвимость / серия с хэштегом  
5. Микро-практика  
6. Книга/фильм/цитата  

## Пайплайн

```
Макс (+ cover) → Telegram → VK×2 → Facebook → b17-блог (+ cover) → TenChat (+ cover)
```

| Шаг | Артефакт | Скрипт |
|-----|----------|--------|
| b17 | `b17-blog-post.md` + **`cover.png` в тексте заметки** | `python scripts/publish-b17-blog.py --topic {id}` |
| TenChat | `tenchat-post.md` + **`cover.png` через скрепку** | `python scripts/publish-tenchat-post.py --topic {id}` |

Промпты: `profile/b17-blog-post-prompt.md`, `profile/tenchat-post-prompt.md`.

## topic_id

`sb-{NN}-{slug}` — NN = номер из очереди MSP (01–100).

## Файлы выхода (на тему)

```
output/{topic_id}/
  max-post.md, telegram-post.md, vk-*-post.md, facebook-post.md
  b17-blog-post.md
  tenchat-post.md
  cover.png                 ← на b17 (анонс) и TenChat (медиа) — тот же файл
  cover-prompt.txt          ← OUTFIT из profile/cover-outfit-rotation.md (слот = номер sb-NN)
```

**Кружок Макс:** не генерировать (вне scope).
