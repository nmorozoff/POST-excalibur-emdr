# Карта URL сайта по темам

Базовый домен: `https://morozovanatalia.ru`

| # темы | Slug страницы | Полный URL |
|--------|---------------|------------|
| 1 | /panic-attacks | https://morozovanatalia.ru/panic-attacks |
| 2 | /panic-attacks + /phobias | https://morozovanatalia.ru/phobias |
| 3 | /anxiety | https://morozovanatalia.ru/anxiety |
| 4 | /anxiety | https://morozovanatalia.ru/anxiety |
| 5 | /anxiety | https://morozovanatalia.ru/anxiety |
| 6 | /divorce | https://morozovanatalia.ru/divorce |
| 7 | /divorce | https://morozovanatalia.ru/divorce |
| 8 | /emotional-abuse | https://morozovanatalia.ru/emotional-abuse |
| 9 | /emotional-abuse | https://morozovanatalia.ru/emotional-abuse |
| 10 | /psychosomatics | https://morozovanatalia.ru/psychosomatics |
| 11 | /psychosomatics | https://morozovanatalia.ru/psychosomatics |
| 12 | /anxiety | https://morozovanatalia.ru/anxiety |
| 13 | /anxiety | https://morozovanatalia.ru/anxiety |
| 14 | /burnout | https://morozovanatalia.ru/burnout |
| 15 | /business-psychology | https://morozovanatalia.ru/business-psychology |
| 16 | /divorce | https://morozovanatalia.ru/divorce |
| 17 | /business-psychology | https://morozovanatalia.ru/business-psychology |
| 18 | /parents-relationship | https://morozovanatalia.ru/parents-relationship |
| 19 | /anxiety | https://morozovanatalia.ru/anxiety |
| 20 | /business-psychology | https://morozovanatalia.ru/business-psychology |

## EMDR-лендинг (общий)

https://morozovanatalia.ru/emdr-therapy

Использовать, когда тема про метод, скорость результата, «инсайты не работают».

Скрытая ссылка в тексте:
```markdown
Ещё подробнее о методе EMDR можно почитать [ТУТ](https://morozovanatalia.ru/emdr-therapy).
```

Факты для блока доверия: `profile/emdr-evidence.md` (ВОЗ 2013, VA/DoD, NICE — не «признан ВОЗ» одной строкой).

## Личка Макс

https://max.ru/se13417616_biz/AZ9H9rFePFc

В тексте поста (Макс):
```markdown
Записаться на бесплатную пробную сессию можно на моем сайте [ТУТ]({url темы}?utm_source=max) или написать мне в ЛС [ТУТ](https://max.ru/se13417616_biz/AZ9H9rFePFc).
```

## Перелинковка постов Макс

Реестры опубликованных постов (перелинковка — отдельно по платформе):

| Платформа | Файл |
|-----------|------|
| Макс | `profile/max-posts-registry.md` |
| Telegram | `profile/telegram-posts-registry.md` |
| VK профиль | `profile/vk-profile-posts-registry.md` |
| VK группа | `profile/vk-group-posts-registry.md` |
| Facebook | `profile/facebook-posts-registry.md` |

Правила: `profile/crosslink-rules.md`

## Шаблон блока в конце поста (Макс)

```
Подробнее о теме: [URL по таблице]?utm_source=max

Ещё подробнее о методе EMDR можно почитать [ТУТ](https://morozovanatalia.ru/emdr-therapy?utm_source=max).

Записаться на бесплатную пробную сессию можно на моем сайте [ТУТ]({URL по таблице}?utm_source=max) или написать мне в ЛС [ТУТ](https://max.ru/se13417616_biz/AZ9H9rFePFc).
```

## Шаблон блока в конце поста (Telegram / LI / FB)

```
…ссылки EMDR и тема с utm_source платформы…

Записаться на бесплатную пробную сессию можно на моем сайте ТУТ или написать мне в ЛС ТУТ.
```

- Сайт «ТУТ» → страница темы + `?utm_source={платформа}`
- ЛС «ТУТ» → https://t.me/natalyamorozovaa (без UTM)

## Шаблон блока в конце поста (ВК)

ВК не поддерживает якорь на внешние ссылки — только полный URL:

```
…ссылки EMDR и тема с utm_source=vk или vk_group…

Записаться на бесплатную пробную сессию можно на моем сайте: {URL темы}?utm_source=vk
или написать мне в ЛС: https://t.me/natalyamorozovaa
```

Перелинковка на другой пост VK: `[https://vk.com/wall…|здесь]` (см. `profile/vk-post-prompt.md`).

Telegram / др.: @natalyamorozovaa
