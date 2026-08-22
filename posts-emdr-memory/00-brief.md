# Посты EMDR — brief

## Проект

Локальный профиль на базе плагина **Excalibur**, но **без Ядрышка/Core**.  
Темы — из текстового файла `topics/blog-topics.md` (верхняя неопубликованная строка).

## Автор

**Наталья Морозова** — психолог, EMDR-терапевт, бизнес-психолог.  
Сайт: https://morozovanatalia.ru

## Цель контента

1. Кружок + пост в **Макс** (канал)
2. Рерайт → **Telegram** (пост или статья)
3. Рерайт → **ВК профиль** + **ВК группа** (`scripts/vk_publish.py`, без MCP)
4. ~~LinkedIn~~ отменён
5. Рерайт → **Facebook** (Zernio)
6. **b17** + **TenChat** (Undetectable, локально или в cloud если доступен)

**Cloud Agent:** секреты в [Cursor Dashboard](https://cursor.com/dashboard/cloud-agents) → `CLOUD-SETUP.md` → `publish-topic.py`

Обложка одна — генерируется на этапе Макс, дальше переиспользуется на всех платформах.

## Контакты в постах

| Платформа | Личка |
|-----------|-------|
| Макс | [ЛС](https://max.ru/u/f9LHodD0cOLMWn4dwsfNLXttuTDjJTF4cCK2MJPjCfNpeKrbfQ6RlQy3dLk) |
| Telegram, ВК, LinkedIn, Facebook | ЛС в Telegram @natalyamorozovaa |

## Запись на пробную сессию

В конце каждого поста (перед вопросом):

**Макс / Telegram / Facebook:** якорь «ТУТ» (markdown или HTML).

**ВК:** полный URL — якорь на внешние ссылки недоступен (см. `profile/vk-post-prompt.md`):

```
Записаться на бесплатную пробную сессию можно на моем сайте: {url}?utm_source=vk
или написать мне в ЛС: https://t.me/natalyamorozovaa
```

Сайт — страница темы + `?utm_source` платформы. ЛС — Макс или Telegram.

## Референсы профиля

- `profile/author-profile.md` — распаковка + EMDR
- `profile/tone-of-voice.md` — разбор голоса из Telegram
- `profile/social-cover-prompt-template.md` — обложки каналов (YouTube thumbnail, Runware)
- `profile/cover-prompt-template.md` — обложки статей блога (Artur/zine, другой агент)
- `profile/post-types.md` — типы постов (конструктор)
- `profile/max-post-prompt.md` — контракт поста Макс (3500–3800 знаков)
- `profile/emdr-evidence.md` — факты EMDR/ВОЗ для блока доверия
- `profile/max-posts-registry.md` — реестр постов Макс для перелинковки
- `profile/vk-post-prompt.md` — ссылки ВК: `[wall|здесь]` внутри VK, полный URL на сайт/TG

## Внешние файлы (источники)

| Файл | Назначение |
|------|------------|
| `/Users/natala/Downloads/blog-topics.txt` | мастер-очередь тем (синхронизировать в `topics/blog-topics.md`) |
| `/Users/natala/Desktop/посты из телеграм.txt` | tone of voice (разобран в profile) |
| `/Users/natala/Desktop/Моя распаковка для для ии.txt` | база author-profile |
| `skills/humanizer-ru/` | очеловечивание текста (humanizer-ru) |

## Режимы запуска

- `mode: max-only` — только кружок + пост Макс + обложка
- `mode: full` — полная цепочка до LinkedIn/Facebook
- `publish: no` — черновики без отправки в боты/API

## Секреты (файлы создаёт агент — пользователь только вставляет ключи)

| Файл | Назначение |
|------|------------|
| `posts-emdr-memory/max.env.local` | Макс-бот |
| `posts-emdr-memory/runware.env.local` | Runware обложки |
| `posts-emdr-memory/telegram.env.local` | Telegram fallback |

Карта: `posts-emdr-memory/КУДА-ВСТАВИТЬ-КЛЮЧИ.md`  
Открыть все: `./scripts/open-secrets.sh`

**Правило:** агент **сам создаёт** `.env.local` при первом запуске; пользователь **не копирует** из `.example`.

Папка: `/Users/natala/Desktop/РЕФЕРЕНСЫ/`  
Основные: `DSC01047.JPG`, `DSC01066.JPG`, `0C2A3279.jpg` (портреты)

## Статус

`profile_setup: done` — профиль инициализирован 2026-07-19.
