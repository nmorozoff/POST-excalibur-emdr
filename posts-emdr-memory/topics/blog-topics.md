# Очередь тем

Источник: `/Users/natala/Downloads/blog-topics.txt`  
Сайт: https://morozovanatalia.ru

**Правило:** брать **верхнюю** тему со статусом `pending`. После публикации — `published` + дата.

Формат строки: `номер | статус | заголовок | кластер/URL | тип поста`

---

## 🔥 Серия P0 — склады WB (июль 2026)

**campaign:** `wb-fire-july-2026`  
**Brief:** `topics/wb-fire-series-brief.md` · **Research + исходный текст автора:** `topics/wb-fire-july-2026-research.md`  
**Порядок:** публиковать **#3 → #7 подряд**, пока тема в новостях.  
**Правило:** в каждый пост — **все обязательные тезисы** из brief (рерайт, не копипаст).

| topic_id | # | status | Заголовок | post_type |
|----------|---|--------|-----------|-----------|
| `03-wb-fire-shock` | 3 | published 2026-07-23 | Склады Wildberries сгорели за одну ночь - и вот что происходит с психикой предпринимателя в такой момент | 29-news-hook · cta:sos |
| `04-wb-fire-story` | 4 | published 2026-07-23 | Я тоже теряла бизнес за один день — и знаю это состояние изнутри | 17-personal-story · cta:bridge |
| `05-wb-sellers-pain` | 5 | pending | «Ещё вчера я была предпринимателем, а сегодня банкрот» — и это не про товар | 05-pain · cta:sos |
| `06-wb-sos-offer` | 6 | pending | Что такое бесплатная SOS-встреча для селлеров, у которых сгорел товар — и как она устроена | 08-value-offer · cta:sos |
| `07-wb-help-confession` | 7 | pending | Признаюсь: я не могла пройти мимо этого поста в ленте | 21-confession · cta:soft |

Все → `/business-psychology`

---

## Очередь (остальное)

| # | status | Заголовок | Кластер / URL | post_type |
|---|--------|-----------|---------------|-----------|
| 1 | published 2026-07-19 | Паническая атака: почему она будит среди ночи и что делать | /panic-attacks | 16-emotional + 12-guide |
| 2 | published 2026-07-22 | Паническая атака в самолёте: как пережить перелёт | /panic-attacks, /phobias | auto |
| 8 | pending | Тревожность у ребёнка: как распознать и когда вести к специалисту | /anxiety | auto |
| 9 | pending | Синдром самозванца: почему успех не ощущается заслуженным | /anxiety | auto |
| 10 | pending | Как понять, что вы сравниваете себя с другими слишком часто | /anxiety | auto |
| 11 | pending | Доверие после измены: можно ли его восстановить | /divorce | auto |
| 12 | pending | Ревность в отношениях: где грань между нормой и разрушением | /divorce | auto |
| 13 | pending | Созависимые отношения: 7 признаков, что вы в них находитесь | /emotional-abuse | auto |
| 14 | pending | Как научиться говорить «нет» без чувства вины | /emotional-abuse | auto |
| 15 | pending | Подавленный гнев: почему он превращается в раздражительность | /psychosomatics | auto |
| 16 | pending | Как отличить здоровое недовольство от накопленного напряжения | /psychosomatics | auto |
| 17 | pending | Бессонница из-за тревожных мыслей: что делать, когда не спится | /anxiety | auto |
| 18 | pending | Прокручивание одних и тех же мыслей перед сном: как остановить | /anxiety | auto |
| 19 | pending | Прокрастинация как страх ошибки, а не лень | /burnout | auto |
| 20 | pending | Перфекционизм предпринимателя: когда высокая планка мешает бизнесу | /business-psychology | auto |
| 21 | pending | Одиночество в браке: когда рядом есть человек, а близости нет | /divorce | auto |
| 22 | pending | Кризис 40 лет у предпринимателя: что делать, когда всё есть, а смысла нет | /business-psychology | auto |
| 23 | pending | Отношения со взрослыми детьми: как пережить синдром опустевшего гнезда | /parents-relationship | auto |
| 24 | pending | Тревога о деньгах, которая не зависит от реального дохода | /anxiety | auto |
| 25 | pending | Почему мужчинам сложно обращаться к психологу | /business-psychology | auto |

## Уже опубликованные кластеры (не дублировать отдельными статьями)

/panic-attacks, /anxiety, /phobias, /psychosomatics, /business-psychology, /divorce, /emotional-abuse, /sexual-abuse, /emdr-therapy, /psychological-trauma, /grief, /eating-disorders, /ptsd, /ocd, /burnout, /dissociation, /complex-ptsd, /parents-relationship, /emigration-stress

## post_type

- `auto` — агент выбирает тип по `profile/post-types.md` и конструктору
- Или явно: `история`, `список`, `миф-факт`, `диалог`, `кейс`, `вопрос-ответ`
- `wb-series` — серия про склады WB; читать `topics/wb-fire-series-brief.md`
- `cta:none` | `cta:sos` | `cta:soft` — правило CTA для серии
