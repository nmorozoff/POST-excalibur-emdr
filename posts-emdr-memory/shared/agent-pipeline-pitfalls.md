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

## Zernio Facebook: status scheduled (Meta transient)

**Симптом (2026-08-04, sb-06):** `zernio-publish-log.json` → `status: scheduled`, `platform_post_url: null` после POST; Meta transient error, Zernio auto-retry.

**Причина:** Meta API временно не принял пост; Zernio ставит scheduled и ретраит.

**Правильно:**
- `publish-zernio-post.py`: polling GET `/api/v1/posts/{id}` до 10 мин; при scheduled — exit 3, лог без hard fail.
- `verify-publish-run.py`: `scheduled` без реестра → **partial** (не hard_fail); повторить verify через 10–15 мин.
- Не удалять cover с FTP, пока статус не `published`.

**Не делать:** считать scheduled как терминальный fail в otchetik/verify.

## MCP user-mcp-kv: intermittent auth

**Симптом:** VK publish падает с auth error.

**Правильно:** `mcp_auth` для `user-mcp-kv`, затем повторить вызов. Не логировать токены.

## Обложки (Kie / Runware)

- **Основной генератор:** `scripts/kie-cover.py` — Kie `gpt-image-2-image-to-image`, **5:4, 1K**, ключ `KIE_API_KEY` (Carusel или Cloud Secrets).
- Ротация портрета: `assets/reference/portrait-NN.jpg` по `cover-reference-rotation.md` (sb-05 → portrait-05).
- Одна `cover.png` на тему — только на шаге MAX.
- Ротация одежды: `profile/cover-outfit-rotation.md` (без double-beige).
- Не вызывать генерацию повторно на TG/VK/FB/b17/TenChat.
- **Запрещено:** MCP `nano_banana_2` с референсом = обложка прошлого поста (sb-04 cover → sb-05 выглядит как клон).
- **Запрещено:** `portrait.jpg` как дефолт — это копия `portrait-01.jpg`; при сбое ротации всегда слот 1.

## Runware (legacy)

- MSP short-blog: **только** `scripts/kie-cover.py` (`publish-topic.py` → `ensure_cover`).
- `runware-cover.py` — legacy, только если нет `KIE_API_KEY`. При `insufficientCredits` — не fallback на nano_banana; использовать `kie-cover.py` или пополнить кошелёк Runware (human).

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

## TenChat вне MSP short-blog (VPS phase 3)

**Симптом:** `--finish` / deferred worker блокируются на `tenchat_not_ready` или `tenchat=published`.

**Правильно:** MSP short-blog VPS worker — только Telegram + b17 (`publish-browser-deferred.py`, `browser_worker_finish.py`). TenChat — отдельно (Mac/ручной), не gate для очереди.
