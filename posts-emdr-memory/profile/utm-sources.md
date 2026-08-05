# UTM — переходы на сайт с соцсетей

Базовый домен: `https://morozovanatalia.ru`

| Платформа | `utm_source` | Пример |
|-----------|--------------|--------|
| Instagram | `insta` | `https://morozovanatalia.ru/panic-attacks?utm_source=insta` |
| Макс | `max` | `https://morozovanatalia.ru/panic-attacks?utm_source=max` |
| Telegram — основной `@morozova_emdr` | `tg1` | `?utm_source=tg1` |
| Telegram — дубль `@nmorozova_emdr` | `tg2` | `?utm_source=tg2` |
| Telegram — группа `@natalia_morozova_psy` | `tg3` | `?utm_source=tg3` |
| VK (профиль) | `vk` | `?utm_source=vk` |
| VK (группа) | `vk_group` | `?utm_source=vk_group` |
| LinkedIn | `linkedin` | `?utm_source=linkedin` |
| Facebook | `fb` | `?utm_source=fb` |
| Одноклассники (группа) | `ok` | `?utm_source=ok` |
| TenChat | `tenchat` | `?utm_source=tenchat` |
| b17 блог | `b17` | `?utm_source=b17` |

## Telegram — три канала

Порядок публикации = порядок в `TELEGRAM_CHANNEL_CHAT_IDS`:

| # | Канал | `utm_source` |
|---|-------|--------------|
| 1 | `@morozova_emdr` (основной) | `tg1` |
| 2 | `@nmorozova_emdr` (дубль) | `tg2` |
| 3 | `@natalia_morozova_psy` (группа) | `tg3` |

В `telegram-post.md` пишите ссылки с **`utm_source=tg1`** (канон основного канала).  
При `--publish` скрипт подставляет `tg2` / `tg3` для остальных каналов автоматически.

Старую метку `utm_source=tg` **не использовать** в новых постах.

## Правило

Все ссылки «ТУТ» на сайт в посте платформы **обязаны** содержать `utm_source` этой платформы.

ЛС / Telegram / Макс — без UTM (это не переход на сайт).

**На обложке URL не печатать** — только подпись «Морозова Наталья / Психолог, EMDR терапевт».
