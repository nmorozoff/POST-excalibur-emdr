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

## b17: обложка только в анонсе / base64 ломает сохранение

**Симптом A:** читатели не видят обложку — она ушла в поле «Картинка для анонса».  
**Симптом B (2026-08-01):** скрипт кликает «Сохранить», лог пишет `published`, но заметки нет. Ошибка b17: «Ошибка сохранения встроенного в текст изображения».

**Причина B:** `data:image/...;base64` в TinyMCE — b17 отклоняет при сохранении.

**Правильно:** HTTPS URL обложки в начале TinyMCE (`https://morozovanatalia.ru/social-covers/{topic}.jpg` через `b17_inline_cover_html()`). После `--submit` проверять `my.php?mod=blog` и публичный `/blog/...` URL. Не ставить `status: published`, если заголовок не появился в списке.

**Не делать:** base64 inline; `b17_upload_cover_image()` как единственный способ; верить клику «Сохранить» без verification.

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

## Cloud Agent

Секреты → [Cursor Cloud Secrets](https://cursor.com/dashboard/cloud-agents), не в git.  
`python3 scripts/materialize_cloud_env.py` → `publish-topic.py`.  
VK без MCP: `vk_publish.py`. b17/TenChat без Undetectable — skip.  
Полная инструкция: `posts-emdr-memory/CLOUD-SETUP.md`.

## Telegram ASocks: порт 443 вместо 9999

**Симптом:** VPS `URLError: SSL: UNEXPECTED_EOF_WHILE_READING` к `api.telegram.org`.

**Причина:** `asocks_sync_proxy.py --target telegram` подставлял `B17_PROXY_CONNECT_PORT=443` вместо порта из template KZ (`:9999`).

**Правильно:** для Telegram только `TELEGRAM_PROXY_CONNECT_PORT` (если задан); иначе порт из ASocks template.

## VPS webhook hangs (sync Playwright)

**Симптом:** `POST /publish` не отвечает минутами; health connection reset.

**Причина:** webhook ждал `publish-browser-deferred` синхронно в HTTP-потоке.

**Правильно:** принять задачу (202) и гонять publish в background; cron worker не должен падать на `browser_ensure_sessions` из‑за TenChat (`|| true` / soft gate).
