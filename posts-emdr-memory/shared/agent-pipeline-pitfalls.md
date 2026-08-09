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

## Обложки (Grsai / Kie / Runware)

- **Основной генератор:** `scripts/grsai-cover.py` — Grsai `gpt-image-2`, **1280×1024 (5:4)**, `quality=low`, ключ `GRSAI_API_KEY` (`grsai.env.local` или Cloud Secrets).
- **Fallback:** `scripts/kie-cover.py` (если нет `GRSAI_API_KEY`), затем `runware-cover.py` (legacy).
- Ротация портрета: `assets/reference/portrait-NN.jpg` по `cover-reference-rotation.md` (sb-05 → portrait-05).
- Одна `cover.png` на тему — только на шаге MAX.
- Ротация одежды: `profile/cover-outfit-rotation.md` (без double-beige).
- Не вызывать генерацию повторно на TG/VK/FB/b17/OK.
- **Запрещено:** локальные тестовые прогоны `grsai-cover.py` / `kie-cover.py` / `runware-cover.py` — обложка только live в Cloud Agent (`publish-topic.py`).
- **Запрещено:** класть `GRSAI_API_KEY` в `grsai.env.example` (файл в git).
- **Запрещено:** MCP `nano_banana_2` с референсом = обложка прошлого поста (sb-04 cover → sb-05 выглядит как клон).
- **Запрещено:** `portrait.jpg` как дефолт — это копия `portrait-01.jpg`; при сбое ротации всегда слот 1.

## Runware / Kie (legacy)

- MSP short-blog: `publish-topic.py` → `ensure_cover` выбирает Grsai при наличии `GRSAI_API_KEY`.
- `kie-cover.py` — fallback при отсутствии Grsai. `runware-cover.py` — только если нет Grsai/Kie.

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

## VPS: Telegram не публикуется (browser gate / proxy / env)

**Симптом:** webhook HTTP 202, но нет `telegram-publish-log.json`; в логе «Browser backend недоступен».

**Причины:** Playwright gate при уже опубликованном b17; выход при сбое ASocks до send-telegram; устаревший `telegram.env.local` на VPS.

**Правильно:** `materialize_vps_env.py` + systemd `EnvironmentFile` для telegram; Playwright только если b17 pending; proxy fail → всё равно send-telegram. Gate: `vps-worker-last-run.json`.

## TenChat вне MSP short-blog (VPS phase 3)

**Симптом:** `--finish` / deferred worker блокируются на `tenchat_not_ready` или `tenchat=published`.

**Правильно:** MSP short-blog VPS worker — только Telegram + b17 (`publish-browser-deferred.py`, `browser_worker_finish.py`). TenChat — отдельно (Mac/ручной), не gate для очереди.

## VPS phase 3 partial после retry otchetik

**Симптом:** Отчётик ×2 (initial + 10–15 мин) → `overall: partial`; нет `browser-worker-finish.json`, `telegram-publish-log.json`, `b17-publish-log.json` в `output/{topic}/` (после `git pull`).

**Возможные причины:** webhook не вызван после `git push`; background worker на VPS упал (Telegram env, ASocks, b17 session); cron не подхватил.

**Правильно (recovery, один раз на тему):**

1. `python3 scripts/trigger-vps-webhook.py --topic {id}` — ожидать HTTP **202** (не dry-run).
2. Подождать 10–15 мин → `git pull origin main` → `python3 scripts/verify-publish-run.py --topic {id}`.
3. Если всё ещё partial — на VPS: `systemctl is-active posts-emdr-webhook`, лог `output/{topic}/vps-webhook-run.log`, `journalctl -u posts-emdr-webhook`, ручной `publish-browser-deferred.py --topic {id} --submit --finish --git-push`.
4. Проверить `telegram.env.local` на VPS: только `@nmorozova_emdr` и `@natalia_morozova_psy` (не `@morozova_emdr`).

**Gate:** commit `browser-worker: published {topic}` на `main` + `browser-worker-finish.json` в output.

## Cloud → VPS webhook TimeoutError

**Симптом (2026-08-05, sb-08):** `trigger-vps-webhook.py` → `TimeoutError` (20s) с Cloud pod; phase 3 не стартовал.

**Причина:** короткий timeout клиента; transient недоступность VPS:8787 или медленный `git pull` в webhook.

**Правильно:**
- `trigger-vps-webhook.py`: GET `/health` (10s), POST `/publish` timeout **90s** (флаг `--timeout 120` при повторе).
- При TimeoutError — один повтор через 10–15 мин; не публиковать TG/b17 из Cloud напрямую.
- Recovery playbook: см. «VPS phase 3 partial после retry otchetik» выше.

**Gate:** HTTP **202** + позже `browser-worker-finish.json` в output.

## Обложка: wp-content URL отдаёт HTML, не image/jpeg

**Симптом (2026-08-05, sb-08):** WordPress media URL (HTTP 200) → `Content-Type: text/html`; VK MCP `vk_create_post_with_photo` падает.

**Причина:** WordPress upload возвращает `wp-content/uploads/…`, но hotlink/redirect отдаёт HTML-страницу ботам.

**Правильно:**
- `cover_upload.py`: **FTP → social-covers/{topic}.jpg** первым; WordPress — fallback только если `url_serves_image()` OK.
- `send-vk-post.py --upload-cover`: gate `cover_serves_image: true` в `vk-publish-prep.json`.
- Workaround run: Kie `cover.url` tempfile (не durable).

**Не делать:** брать первый HTTP 200 без проверки Content-Type.

## Zernio удаляет обложку до VK MCP

**Симптом (2026-08-05, sb-08):** `publish-zernio-post.py` после Facebook вызывал `--delete-cover` → FTP social-covers удалён до фазы 2 MCP VK.

**Правильно:**
- Порядок cloud: VK upload → **MCP VK** → Facebook → `send-vk-post --delete-cover` после обоих VK-постов.
- `publish-zernio-post.py`: **не** удалять cover по умолчанию; только явный `--delete-cover` (legacy VK API path).
- `publish-topic.py`: Facebook после MCP handoff; cleanup — `send-vk-post.py --delete-cover`.

## extract_post / normalize_typography

**Симптом (2026-08-05):** `NameError: normalize_typography`; VK MCP message включал блок `## Мета`.

**Правильно:**
- Единая функция `posts_emdr_env.extract_post_body_from_md()` — стоп перед `---` / `## Мета`.
- Использовать в `send-vk-post.py`, `vk_publish.py`, `publish-zernio-post.py`, `publish-topic.py`.

## Grsai: нет секций `## Текст поста` / `## Мета`

**Симптом (2026-08-06, sb-10):** `grsai-generate-topic.py` (gemini-3.1-pro) вернул max/vk/facebook/ok без обязательных markdown-секций; `send-max-draft.py` и `publish-zernio-post.py` упали на парсинге.

**Причина:** модель иногда выводит «голый» текст без контракта файла.

**Правильно:**
- После генерации: `ensure_platform_contract()` в `grsai-generate-topic.py` — auto-wrap в `## Текст поста` + `## Мета`, gate `extract_post_body_from_md()`.
- max-post: проверка длины 3500–3800 (hard max 4000, auto-truncate по абзацу).
- telegram: обязательны `## Текст поста (HTML для Telegram)` и `<!-- END_POST -->`.
- Лог: `grsai-content-log.json` → `platforms.*.contract_fixes`.

**Не делать:** вручную править формат в output как постоянный workaround; не публиковать, если после auto-wrap gate всё ещё `missing ## Текст поста`.

## Telegram Cloud Secrets: неверный список каналов

**Симптом (2026-08-06, sb-10):** VPS webhook 202, b17 OK, но `telegram-publish-log.json` не появился; Cloud Secrets `TELEGRAM_CHANNEL_CHAT_IDS` содержали снятый канал вместо пары `@nmorozova_emdr` + `@natalia_morozova_psy`.

**Причина:** `send-telegram-post.py` hard guard блокирует publish; worker молча не создаёт лог.

**Правильно:**
- Cloud Secrets и VPS `telegram.env.local`: только согласованная пара каналов + `TELEGRAM_CHANNEL_UTM_SOURCES=tg1,tg2` (см. `cloud-secrets-checklist.txt`, `profile/telegram-posts-registry.md`).
- Gate до publish: `materialize_cloud_env.py` / `cloud_preflight.py` → `validate_telegram_channels(require_two=True)`.
- После исправления env на VPS: один `trigger-vps-webhook.py --topic {id}` (не публиковать из Cloud).

**Не делать:** включать `@morozova_emdr`; не дублировать секреты в pitfalls/queue.

## VPS telegram.env.local drift (rsync / git exclude)

**Симптом (2026-08-07, sb-10 recurrence):** Cloud phase 1+2 OK, VPS webhook HTTP 202, b17 может опубликоваться, но `telegram-publish-log.json` не появляется; тема остаётся `in_progress`.

**Причина:** `sync-to-vps.sh` и `git pull` **не** обновляют `posts-emdr-memory/*.env.local`; на VPS остаётся устаревший `telegram.env.local` (один канал или снятый `@morozova_emdr`), хотя Cloud Secrets уже валидны.

**Правильно:**
- На VPS в **systemd EnvironmentFile** (или `/etc/posts-emdr/telegram.env`): `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHANNEL_CHAT_IDS`, `TELEGRAM_CHANNEL_UTM_SOURCES` — та же пара, что в `cloud-secrets-checklist.txt`.
- При старте `vps-webhook-server.py` и `publish-browser-deferred.py` → `materialize_telegram_env_from_os()` перезаписывает `telegram.env.local` из окружения.
- После первого деплоя fix: один `trigger-vps-webhook.py --topic {id}` (не публиковать из Cloud).

**Gate:** `materialize_telegram_env_from_os` + `validate_telegram_channels(require_two=True)`; в логе webhook — `telegram_env.written: true`.

**Не делать:** полагаться на ручной rsync `telegram.env.local` с Mac; не коммитить секреты в репо.

## Telegram VPS: NameError ensure_client_story_disclaimer

**Симптом (2026-08-08, sb-11):** VPS webhook 202, `vps-worker-last-run.json` → `telegram.exit_code: 1`, `NameError: ensure_client_story_disclaimer is not defined`; b17 может быть `already_published`, но нет `telegram-publish-log.json` и `--finish`.

**Причина:** вызов `ensure_client_story_disclaimer()` в `main()`, импорт только внутри `load_env()` (scope).

**Правильно:**
- Импорт в `main()` перед вызовом (или module-level).
- Gate: `python3 -m py_compile scripts/send-telegram-post.py`; dry-run не должен падать с NameError.
- После fix на `main`: один `trigger-vps-webhook.py --topic {id}` (Telegram retry; b17 skip если уже published).

**Не делать:** считать partial только «env drift» — смотреть `vps-worker-last-run.json` на VPS.

## OK MCP: Refresh token expired

**Симптом (2026-08-09, sb-12):** MCP `ok_create_post_with_photo` ×2 → `Refresh token expired` (mcp-kv); нет `ok-publish-log.json` и строки в `ok-posts-registry.md`. Остальные платформы (Max, TG, VK, Facebook, b17) — OK.

**Причина:** истёк refresh token интеграции OK в Dashboard automation (mcp-kv). Fixic и скрипты **не** могут обновить токен.

**Правильно (recovery после re-auth):**

1. Владелец: Cursor Dashboard → Integrations & MCP → mcp-kv → **re-auth OK** (обновить refresh token).
2. Убедиться, что `output/{topic}/ok-mcp-handoff.json` на месте (создаётся `publish-topic.py` на фазе 1; для sb-12 уже готов).
3. Повторить MCP **один раз** (не перегенерировать контент):
   - `ok_create_post_with_photo`: `text`, `image_url`, `gid: 70000034253679`, `onBehalfOfGroup: true` — из handoff.
4. Записать результат:
   ```bash
   python3 scripts/record-ok-publish.py --topic {id} \
     --url \"https://ok.ru/group/70000034253679/topic/...\" \
     --mediatopic-id \"...\" --title \"...\" \
     --site-url \"https://morozovanatalia.ru/...\" --tags \"...\"
   ```
5. `git add` + commit `ok-publish-log.json` и обновлённый `ok-posts-registry.md`.

**Gate:** `ok-publish-log.json` со `status: published` + строка в `profile/ok-posts-registry.md`.

**Не делать:** перегенерировать `ok-post.md` или обложку; не публиковать OK из VPS; не коммитить токены.

## Grsai: telegram >4096 и b17 без blank line после headers

**Симптом (2026-08-09, sb-12):** `telegram-post.md` от Grsai — 4403 символа (лимит TG API 4096) → VPS `send-telegram-post.py` fail. `b17-blog-post.md` без пустой строки после `## Заголовок` / `## Текст поста` → `publish-b17-blog.py` parse fail.

**Причина:** `ensure_platform_contract()` не проверял длину HTML telegram и формат b17 headers при уже существующих секциях.

**Правильно:**
- `grsai-generate-topic.py` postprocess:
  - telegram: `truncate_telegram_html()` — hard max **4096** по HTML-телу (как `send-telegram-post.py` `MESSAGE_LIMIT`), обрезка по абзацу.
  - b17: `ensure_b17_blank_lines()` — `\n\n` после `## Заголовок` и `## Текст поста` (контракт `publish-b17-blog.py`).
- Лог: `grsai-content-log.json` → `contract_fixes` с `truncated telegram HTML` / `fixed b17 blank lines`.

**Не делать:** вручную править output как постоянный workaround; не публиковать TG/b17 до gate.
