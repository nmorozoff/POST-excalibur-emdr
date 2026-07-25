# Agent pipeline pitfalls — Posts EMDR

Читать **до** генерации и публикации. Fixic дополняет этот файл после run.

## Telegram: два сообщения вместо одного

**Инцидент:** 2026-07-23, тема `03-wb-fire-shock`.

**Симптом:** в канале фото и текст — **два отдельных** сообщения.

**Причина:** `send-telegram-post.py` с `photo_then_text` вместо `link_preview`.

**Правильно:**
- `python scripts/send-telegram-post.py --topic {id} --publish` (default `link_preview`)
- Лог: `"delivery": "link_preview_single_message"`, одно `message_id` на канал

**Запрещено:** `--delivery photo_then_text` при `--publish`.

## b17: обложка только в анонсе

**Симптом:** читатели не видят обложку — она ушла в поле «Картинка для анонса».

**Правильно:** JPEG base64 **в начале TinyMCE** через `b17_inline_cover_html()` в `scripts/undetectable_browser.py`.

**Не делать:** `b17_upload_cover_image()` как единственный способ.

## TenChat: урезанный текст

**Симптом:** пост короче max-post, «кастрированный» список.

**Причина:** промпт допускал слишком короткий диапазон.

**Правильно:** `profile/tenchat-post-prompt.md` — **1800–2200** знаков; списки с маркером `—`.

## TenChat: обложка

**Правильно:** скрепка `.i-fa6-solid:paperclip` → `input[type=file]` → `cover.png` (`tenchat_attach_cover_image()`).

## Undetectable: кириллица в `/browser/fill`

**Симптом:** поля пустые или кракозябры после Playwright fill.

**Правильно:** `set_field_value_js()` / `evaluate` для TinyMCE и текстовых полей.

## Zernio / Facebook: 409 duplicate content

**Симптом:** API отклоняет пост как дубликат.

**Правильно:** уникальная строка с URL сайта темы в тексте Facebook; не копировать Макс дословно.

## MCP user-mcp-kv: intermittent auth

**Симптом:** VK publish падает с auth error.

**Правильно:** `mcp_auth` для `user-mcp-kv`, затем повторить вызов. Не логировать токены.

## Runware / обложки

- Одна `cover.png` на тему — только на шаге MAX.
- Ротация одежды: `profile/cover-outfit-rotation.md` (без double-beige).
- Не вызывать Runware повторно на TG/VK/FB/b17/TenChat.

## b17 / TenChat: публикация

**По умолчанию:** формы заполняются, финальный клик — вручную (preview).

**Полная автоматизация (после проверки превью):**
- b17: `python scripts/publish-b17-blog.py --topic {id} --submit`
- TenChat: `python scripts/publish-tenchat-post.py --topic {id} --submit`

Кнопки ищутся по тексту «Сохранить» / «Опубликовать» через `click_button_by_text()`.

## Реестры и очередь

- После каждой платформы — `scripts/update-post-registry.py`.
- Short-blog очередь: `topics/short-blog-queue.md` → `short-blog-published.md`.
- Не удалять/перепубликовывать без явной просьбы пользователя.

## Fixic gate

После run: `python scripts/incident_queue.py --project-root .`  
Код `2` → **Task(`posts-emdr-fixic`)** до следующей темы.
