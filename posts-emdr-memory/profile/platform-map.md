# Карта платформ и адаптации

## Порядок пайплайна (одна тема)

```
1. TOPIC     ← первая строка topics/short-blog-queue.md (или blog-topics.md для длинных)
2. MAX       ← кружок + пост + обложка (Runware, один раз → cover.png)
3. TELEGRAM  ← рерайт поста; обложка = cover.png из MAX
4. VK×2      ← профиль + группа; обложка = cover.png
5. FACEBOOK  ← рерайт; обложка = cover.png; Zernio API
6. OK        ← рерайт `ok-post.md`; обложка = cover.png; MCP `ok_create_post_with_photo` (группа)
7. B17       ← рерайт `b17-blog-post.md` + **обложка cover.png**; `publish-b17-blog.py`
```

TenChat снят с пайплайна (2026-08-03). LinkedIn отменён.

Обложка: **одна** `cover.png`, генерируется **только на шаге MAX**, дальше переиспользуется везде — **включая b17 (анонс) и OK/VK/FB**.

---

## 1. Макс (канал)

| Поле | Правило |
|------|---------|
| Кружок | 30–60 сек устного текста, разговорно, как в TG; без чтения с листа |
| Пост | **3500–3800 символов**; промпт `profile/max-post-prompt.md`; абзацы 1–3 строки |
| CTA | [ЛС](https://max.ru/se13417616_biz/AZ9H9rFePFc) + сайт с `?utm_source=max` + [ТУТ](https://morozovanatalia.ru/emdr-therapy?utm_source=max) при темах тревоги/травмы |
| Доставка | Текст кружка + пост + обложка → **бот в Макс** (ручная запись пользователем) |

### Структура текста для кружка

```
[0–5 сек] Крючок — боль/вопрос
[5–40 сек] 1 история или 1 механизм простыми словами
[40–55 сек] Что можно сделать / EMDR как опция
[55–60 сек] «Напишите в личку в Макс — разберём»
```

---

## 2. Telegram

| Поле | Правило |
|------|---------|
| Формат | Пост (до ~4000 знаков) ИЛИ длинная статья (если тема требует) |
| Тон | Ближе к оригиналу Макс, можно чуть длиннее и глубже |
| CTA | @natalyamorozovaa + сайт с `?utm_source=tg1` / `tg2` / `tg3` по каналу + пробная сессия |
| Доставка | MCP `telegram_send_message` + `telegram_send_photo` (обложка) |

### Когда статья, а не пост

- Тема с чеклистом (7 признаков, шаги)
- Сравнение (тревога vs фобия)
- Нужны подзаголовки и списки

---

## 3. ВКонтакте

| Поле | Правило |
|------|---------|
| Профиль | Личный тон, «я», истории, мягче деловой лексики |
| Группа | Чуть более экспертный тон, можно структуру списком |
| Длина | ~3000–3800 знаков (как TG/Макс), не сокращать |
| Ссылки | Перелинковка VK→VK: `[url\|здесь]`. Сайт/TG: полный URL (см. `vk-post-prompt.md`) |
| CTA | Сайт + UTM, ЛС → https://t.me/natalyamorozovaa |
| Публикация | `scripts/send-vk-post.py --upload-cover` + MCP `vk_create_post_with_photo` × 2 |

---

## 4. Facebook (Zernio)

| Поле | Правило |
|------|---------|
| Тон | Теплее делового, ближе к TG |
| Длина | Средняя, с эмодзи умеренно |
| CTA | Telegram + сайт с `utm_source=fb` |
| Публикация | `scripts/publish-zernio-post.py` — только **Facebook Page** |

**LinkedIn:** отменён (блокировка аккаунта). Файл `linkedin-post.md` не генерировать.

---

## 5. Одноклассники (группа)

| Поле | Правило |
|------|---------|
| Площадка | Группа `70000034253679` |
| Тон | Как Facebook — теплее, умеренно эмодзи |
| Длина | ~3000–3800 знаков |
| Ссылки | Перелинковка OK→OK: полный URL топика. Сайт/TG — только в конце |
| CTA | Telegram + сайт с `utm_source=ok` |
| Публикация | MCP `ok_create_post_with_photo` (фаза 2 Cloud) |
| Промпт | `profile/ok-post-prompt.md` |

---

## 6. b17.ru (блог)

| Поле | Правило |
|------|---------|
| Тон | чуть более профессиональный, чем TG; «в практике вижу» |
| Длина | **1000–1600** знаков (полный смысл max-post) |
| Ссылки | **запрещены** в тексте заметки |
| CTA | ЛС на b17 + открытый вопрос (`short-blog-cta-rules.md`) |
| Раздел | **Мысли о психологии** |
| Авторство | **Я — автор текста заметки** |
| Обложка | **`cover.png` в тексте заметки** (TinyMCE, скрипт) — не только анонс |
| Промпт | `profile/b17-blog-post-prompt.md` |
| Публикация | `scripts/publish-b17-blog.py` + Undetectable |

---

## ~~6. TenChat~~ (снят с пайплайна 2026-08-03)

| Поле | Правило |
|------|---------|
| Аудитория | предприниматели, эксперты, B2B |
| Заголовок | до **80 символов** |
| Текст | оптимум **1800–2200**; подзаголовки, списки с `—`, короткие блоки |
| Тон | экспертность + личный опыт; без продажи в каждом абзаце |
| CTA | открытый вопрос; ссылка в слове с `utm_source=tenchat` |
| Обложка | **`cover.png`** — **скрепка** в редакторе (скрипт) |
| Темы | **Саморазвитие** (одна тематика по умолчанию) |
| Промпт | `profile/tenchat-post-prompt.md` |
| Публикация | `scripts/publish-tenchat-post.py` + Undetectable |
| HTML | сырой HTML в пост **не** поддерживается — редактор или HTML через скрипт |

---

## Файлы выхода (на тему)

```
posts-emdr-memory/output/{topic_id}/
  max-circle-script.md
  max-post.md
  telegram-post.md          # или telegram-article.md
  vk-profile-post.md
  vk-group-post.md
  facebook-post.md
  ok-post.md
  b17-blog-post.md
  cover.png
  publish-log.md
```

---

## MCP инструменты

| Действие | MCP / скрипт |
|----------|----------------|
| Макс | `scripts/send-max-draft.py` (не Zernio) |
| Telegram текст/фото | MCP KV `telegram_send_*` (не Zernio) |
| VK пост+фото | `send-vk-post.py` + MCP `vk_create_post_with_photo` (не Zernio) |
| Facebook | `scripts/publish-zernio-post.py` (Zernio API, не MCP KV) |
| OK группа | MCP `ok_create_post_with_photo` + `record-ok-publish.py` |
| b17 блог | `scripts/publish-b17-blog.py` + Undetectable; **обложка в тексте** TinyMCE |
| Обложка MAX (генерация) | Runware `scripts/runware-cover.py` |
