# Пост VK — контракт

Источник: `max-post.md` → **только рерайт** (перефраз, смена ритма). См. `profile/crosslink-rules.md`.

## Перелинковка

| Файл | Куда ссылаться |
|------|----------------|
| `vk-profile-posts-registry.md` | только в `vk-profile-post.md` |
| `vk-group-posts-registry.md` | только в `vk-group-post.md` |

**Не смешивать** URL профиля и группы.

## Ссылки во ВКонтакте (важно)

ВК **не поддерживает** markdown `[текст](url)` и HTML `<a href>`. Поведение разное для внутренних и внешних ссылок.

### Перелинковка на другой пост VK — якорь в буквы ✅

Формат: `[полный_url|текст]`. URL **с https://**.

```
О ночных панических атаках мы уже говорили [https://vk.com/wall218367867_641|здесь].
```

- В **профиле** — URL только из `vk-profile-posts-registry.md`
- В **группе** — URL только из `vk-group-posts-registry.md`

### Внешние ссылки (сайт, Telegram) — только полный URL ❌

Анкор «ТУТ» внутри слова **нельзя**. Пишем слово + URL на той же строке:

```
Ещё подробнее о методе EMDR на моем сайте: https://morozovanatalia.ru/emdr-therapy?utm_source=vk

Записаться на бесплатную пробную сессию можно на моем сайте: https://morozovanatalia.ru/phobias?utm_source=vk
или написать мне в ЛС: https://t.me/natalyamorozovaa
```

**Не писать** `ТУТ: https://...` — слово «ТУТ» не станет кликабельным, это вводит в заблуждение.

UTM: `utm_source=vk` (профиль) / `utm_source=vk_group` (группа). ЛС → `https://t.me/natalyamorozovaa` без UTM.

## Запреты

- **Не сокращать** относительно TG/Макс. Целевой объём: **~3000–3800 знаков** (как TG/Макс).
- **Не выкидывать** блоки: история клиентки, 4 шага, EMDR/ВОЗ, CTA, вопрос в конце.
- **Не писать «до 2000 знаков»** — это устаревшее правило.

## Две версии

| Файл | Отличие | UTM |
|------|---------|-----|
| `vk-profile-post.md` | чуть больше «я» (можно 2–3 фразы от первого лица) | `utm_source=vk` |
| `vk-group-post.md` | тот же объём и смысл; можно чуть больше списков | `utm_source=vk_group` |

Смысл, факты, примеры — **те же**, что в TG. Меняется формулировка, не содержание.

## Обложка — обязательна

Gate: в ответе MCP есть `📸 Загружено фото`.

```bash
python scripts/send-vk-post.py --topic 01-panic-night --upload-cover
# после успешной публикации в VK:
python scripts/send-vk-post.py --topic 01-panic-night --delete-cover
```

Временный URL: `https://morozovanatalia.ru/social-covers/{topic_id}.jpg` — **удалять после publish**.

Catbox/Runware для VK **не использовать** (таймаут на стороне VK).

## Публикация (MCP `vk_create_post_with_photo`)

**Профиль:**
- `publish_location: personal`
- без `group_id`

**Группа** (обязательно явный ID, иначе уйдёт в профиль):
- `publish_location: group`
- `from_group: true`
- `group_id: "224685309"` — https://vk.com/natalyamorozovapsy

Проверка группы: пост должен появиться на стене сообщества, не на личной странице.
