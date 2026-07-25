# Типы постов — конструктор

**Источник (импортирован):** `skills/post-constructor/post-constructor/SKILL.md` + 30 шаблонов `01-*.md` … `30-*.md`

## Логика выбора типа

Агент читает тему + `tone-of-voice.md`, затем **один** файл из конструктора:

| Если в теме… | Файл конструктора |
|--------------|-------------------|
| Число в заголовке (7 признаков) | `14-top-list.md` |
| «Как отличить», «vs», сравнение | `15-comparison.md` |
| Мифы, заблуждения | `13-myths.md` |
| Пошаговая инструкция | `12-guide.md` |
| История, кейс | `03-story.md` или `04-case.md` |
| Боль, узнавание | `05-pain.md` |
| Вопрос в заголовке | `09-qa-sell.md` или `10-logical.md` |
| Предприниматель, бизнес | `04-case.md`, `11-breakdown.md` |
| Личное наблюдение | `17-personal-story.md`, `18-life-post.md` |
| EMDR, трансформация | `19-transformation.md`, `06-before-after.md` |
| Событийный / новость | `29-news-hook.md` |
| Серия WB июль 2026 | `topics/wb-fire-series-brief.md` + шаблоны по колонке post_type |

Если в `blog-topics.md` указан явный `post_type` (номер или slug) — использовать его.

Полный каталог: см. `skills/post-constructor/post-constructor/SKILL.md`
