# Posts EMDR — pipeline fix queue

Durable incident memory. Контракт: `shared/pipeline-incident-fix-contract.md`

**Правило:** open incidents → Director вызывает `posts-emdr-fixic` после `=== POSTS EMDR DONE ===`.

---

## INC-20260723-1430-telegram-photo-then-text
status: fixed
run_date: 2026-07-23
role: script
topic: 03-wb-fire-shock
severity: medium
category: telegram

### What went wrong
- В канале Telegram два сообщения: фото отдельно, текст отдельно.

### How the agent recovered this run
- Пост оставлен как есть; зафиксирован режим доставки.

### Durable fix needed before next run
- Запретить `photo_then_text` при publish; default `link_preview`.

### Suggested files to inspect/change
- `scripts/send-telegram-post.py`
- `.cursor/rules/posts-emdr-orchestrator.mdc`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-07-25
fix_summary:
- Оркестратор и pitfalls: только `link_preview` для каналов.
- Скрипт блокирует `--publish` с `photo_then_text`.
files_changed:
- `.cursor/rules/posts-emdr-orchestrator.mdc`
- `posts-emdr-memory/profile/pipeline-pitfalls.md`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`

---

## INC-20260725-1200-b17-cover-announcement-only
status: fixed
run_date: 2026-07-25
role: script
topic: sb-02-anxiety-as-responsibility
severity: high
category: b17

### What went wrong
- Обложка загружалась в «Картинка для анонса» — читатели не видели в теле заметки.

### How the agent recovered this run
- Пользователь опубликовал вручную после перезаполнения формы.

### Durable fix needed before next run
- Inline JPEG base64 в начало TinyMCE.

### Suggested files to inspect/change
- `scripts/undetectable_browser.py`
- `scripts/publish-b17-blog.py`
- `posts-emdr-memory/profile/b17-blog-post-prompt.md`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-07-25
fix_summary:
- `b17_inline_cover_html()` + `fill_b17_compose(cover_path=...)`.
- Промпт b17: 1000–1600 знаков.
files_changed:
- `scripts/undetectable_browser.py`
- `posts-emdr-memory/profile/b17-blog-post-prompt.md`

---

## INC-20260725-1215-tenchat-text-truncated
status: fixed
run_date: 2026-07-25
role: prompt
topic: sb-02-anxiety-as-responsibility
severity: medium
category: tenchat

### What went wrong
- TenChat-пост слишком короткий; списки из однострочных пунктов.

### How the agent recovered this run
- Переписан `tenchat-post.md`, форма перезаполнена; пользователь опубликовал.

### Durable fix needed before next run
- Промпт 1800–2200 знаков; эвристика списков с `—`.

### Suggested files to inspect/change
- `posts-emdr-memory/profile/tenchat-post-prompt.md`
- `scripts/undetectable_browser.py`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-07-25
fix_summary:
- Объём TenChat 1800–2200; переписан sb-02 tenchat-post.
files_changed:
- `posts-emdr-memory/profile/tenchat-post-prompt.md`
- `posts-emdr-memory/output/sb-02-anxiety-as-responsibility/tenchat-post.md`

---

## INC-20260725-1220-tenchat-cover-paperclip
status: fixed
run_date: 2026-07-25
role: script
topic: sb-02-anxiety-as-responsibility
severity: medium
category: tenchat

### What went wrong
- Обложка не прикреплялась к посту TenChat.

### How the agent recovered this run
- Ручная скрепка пользователем.

### Durable fix needed before next run
- Автоклик скрепки + file input.

### Suggested files to inspect/change
- `scripts/undetectable_browser.py`
- `scripts/publish-tenchat-post.py`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-07-25
fix_summary:
- `tenchat_attach_cover_image()` через paperclip selector.
files_changed:
- `scripts/undetectable_browser.py`
- `scripts/publish-tenchat-post.py`

---

## INC-20260725-1230-undetectable-cyrillic-fill
status: fixed
run_date: 2026-07-25
role: script
topic: sb-02-anxiety-as-responsibility
severity: high
category: undetectable

### What went wrong
- Playwright `/browser/fill` ломает кириллицу в полях b17/TenChat.

### How the agent recovered this run
- JS `evaluate` / `set_field_value_js` для вставки текста.

### Durable fix needed before next run
- Документировать и использовать только JS-путь для кириллицы.

### Suggested files to inspect/change
- `scripts/undetectable_browser.py`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-07-25
fix_summary:
- Workaround в undetectable_browser; пункт в pitfalls.
files_changed:
- `scripts/undetectable_browser.py`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`

---

## INC-20260725-1240-mcp-kv-auth-intermittent
status: fixed
run_date: 2026-07-25
role: director
topic: sb-02-anxiety-as-responsibility
severity: medium
category: api

### What went wrong
- MCP `user-mcp-kv` недоступен / auth error при VK publish.

### How the agent recovered this run
- `mcp_auth` → повтор VK publish OK.

### Durable fix needed before next run
- Pitfall: retry после mcp_auth, без логирования секретов.

### Suggested files to inspect/change
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-07-25
fix_summary:
- Документирован retry flow в pitfalls.
files_changed:
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`

---

## INC-20260725-1250-zernio-409-duplicate
status: fixed
run_date: 2026-07-25
role: script
topic: sb-02-anxiety-as-responsibility
severity: medium
category: zernio

### What went wrong
- Zernio API 409 — duplicate content для Facebook.

### How the agent recovered this run
- Добавлена уникальная строка с URL сайта темы в текст.

### Durable fix needed before next run
- Промпт Facebook: обязательная уникализирующая строка с site_url.

### Suggested files to inspect/change
- `posts-emdr-memory/profile/platform-map.md`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-07-25
fix_summary:
- Pitfall + уникальная строка в facebook-post sb-02.
files_changed:
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`

---

## INC-20260725-1300-b17-tenchat-manual-publish-click
status: fixed
run_date: 2026-07-25
role: script
topic: sb-02-anxiety-as-responsibility
severity: medium
category: undetectable

### What went wrong
- Скрипты заполняют формы b17 и TenChat, но Save/Publish — вручную пользователем.

### How the agent recovered this run
- Пользователь нажал Save / Publish после заполнения.

### Durable fix needed before next run
- Автоклик финальной кнопки публикации с gate (preview OK, no double-submit).

### Suggested files to inspect/change
- `scripts/undetectable_browser.py`
- `scripts/publish-b17-blog.py`
- `scripts/publish-tenchat-post.py`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-07-25
fix_summary:
- `click_button_by_text()` + опциональный `--submit` в publish-b17-blog.py и publish-tenchat-post.py.
- По умолчанию без submit (безопасный preview); полная автоматизация: `--submit`.
files_changed:
- `scripts/undetectable_browser.py`
- `scripts/publish-b17-blog.py`
- `scripts/publish-tenchat-post.py`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`
checks_run:
- `python -m py_compile scripts/undetectable_browser.py scripts/incident_queue.py`

---

## INC-20260725-2155-cloud-missing-secrets-mcp
status: fixed
run_date: 2026-07-25
role: director
topic: sb-03-body-before-mind
severity: blocker
category: env

### What went wrong
- Cloud pod: нет `.env.local`, нет MCP VK/Telegram; публикация невозможна.

### How the agent recovered this run
- Контент sb-03 создан; publish отложен.

### Durable fix needed before next run
- Env из Cursor Secrets + VK API без MCP + publish-topic.py + reference в репо.

### Suggested files to inspect/change
- `scripts/posts_emdr_env.py`
- `scripts/publish-topic.py`
- `scripts/vk_publish.py`
- `posts-emdr-memory/CLOUD-SETUP.md`
- `.cursor/environment.json`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-07-25
fix_summary:
- materialize_cloud_env, cloud_preflight, publish-topic, vk_publish (no MCP).
- CLOUD-SETUP.md + cloud-secrets-checklist.txt + assets/reference/portrait.jpg.
needed_decision_or_secret:
- Владелец добавляет Runtime Secrets в cursor.com/dashboard/cloud-agents (см. checklist).
files_changed:
- scripts/posts_emdr_env.py, materialize_cloud_env.py, cloud_preflight.py, publish-topic.py, vk_publish.py
- .cursor/environment.json
- posts-emdr-memory/CLOUD-SETUP.md
checks_run:
- py_compile all new scripts

---

## INC-20260801-2150-b17-base64-save-rejected
status: fixed
run_date: 2026-08-01
role: script
topic: sb-04-what-if-phrase
severity: high
category: b17

### What went wrong
- Лог писал `status: published` после клика «Сохранить», но заметки на b17 не было.
- Ошибка формы: «Ошибка сохранения встроенного в текст изображения» — из‑за `data:image;base64` в TinyMCE.
- То же ложное `published` у sb-03 (заметки тоже нет в списке).

### How the agent recovered this run
- Обложка через HTTPS `social-covers/{topic}.jpg`.
- Verification: заголовок должен появиться в `my.php?mod=blog`, иначе не `published`.
- sb-04 опубликован: https://www.b17.ru/blog/fraza_a_vdrug_i_kak_ona_zapuskaet_scenariy_v_golove/

### Durable fix needed before next run
- Запретить base64 inline для b17; HTTPS cover URL + post-submit verification.

### Suggested files to inspect/change
- `scripts/undetectable_browser.py`
- `scripts/playwright_browser.py`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`
- `posts-emdr-memory/profile/b17-blog-post-prompt.md`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-08-01
fix_summary:
- `b17_inline_cover_html` → HTTPS URL (не base64).
- TinyMCE `ed.save()` / `triggerSave` перед submit.
- Playwright: fail если title нет в списке публикаций.
files_changed:
- scripts/undetectable_browser.py
- scripts/playwright_browser.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md
- posts-emdr-memory/profile/b17-blog-post-prompt.md
checks_run:
- live publish sb-04 + public URL 200


## INC-20260803-1030-runware-credits
status: fixed
run_date: 2026-08-03
role: cover
topic: sb-05-tolerate-uncertainty
severity: medium
category: runware

### What went wrong
- Runware API HTTP 400 `insufficientCredits` — обложка не сгенерировалась штатным `runware-cover.py`.

### How the agent recovered this run
- MCP `nano_banana_2` i2i (референс: публичная обложка sb-04) → `cover.png` 1280×1024.

### Durable fix needed before next run
- Пополнить баланс Runware (https://my.runware.ai/wallet) или зафиксировать MCP fallback в skill/скрипте.

### Suggested files to inspect/change
- `scripts/runware-cover.py`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-08-03
fix_summary:
- Основной генератор обложек: `scripts/kie-cover.py` (Kie gpt-image-2-image-to-image, 5:4 1K).
- Runware — legacy fallback только при наличии кредитов; при insufficientCredits — kie-cover, не MCP nano_banana с чужой обложкой.
files_changed:
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`
checks_run:
- `python -m py_compile scripts/kie-cover.py scripts/posts_emdr_env.py`

## INC-20260803-1035-cloud-ftp-425
status: fixed
run_date: 2026-08-03
role: cover-upload
topic: sb-05-tolerate-uncertainty
severity: medium
category: ftp

### What went wrong
- Cloud FTP data-channel 425/PORT fail — `send-vk-post --upload-cover` с cloud DC не заливал social-covers.

### How the agent recovered this run
- VK/FB: публичный JPEG (Imgur) для MCP/Zernio.
- VPS `ensure_site_cover` в `publish-browser-deferred.py` — FTP с VPS OK → `social-covers/sb-05-….jpg`.

### Durable fix needed before next run
- Оставить VPS upload-cover перед b17/TG (уже в deferred worker).

### Suggested files to inspect/change
- `scripts/publish-browser-deferred.py`
- `scripts/cover_upload.py`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-08-03
fix_summary:
- deferred worker uploads site cover before platforms
files_changed:
- scripts/publish-browser-deferred.py

## INC-20260803-1040-telegram-asocks-port
status: fixed
run_date: 2026-08-03
role: telegram
topic: sb-05-tolerate-uncertainty
severity: high
category: telegram

### What went wrong
- VPS Telegram: `SSL: UNEXPECTED_EOF_WHILE_READING` через proxy.

### How the agent recovered this run
- Найдено: `asocks_sync_proxy` подставлял `B17_PROXY_CONNECT_PORT=443` вместо template `:9999`.

### Durable fix needed before next run
- Не наследовать B17 CONNECT_PORT для Telegram (сделано).

### Suggested files to inspect/change
- `scripts/asocks_sync_proxy.py`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-08-03
fix_summary:
- Telegram sync uses only TELEGRAM_PROXY_CONNECT_PORT or template port
files_changed:
- scripts/asocks_sync_proxy.py
- posts-emdr-memory/shared/agent-pipeline-pitfalls.md

## INC-20260803-1045-tenchat-session-blocks-vps
status: fixed
run_date: 2026-08-03
role: vps
topic: sb-05-tolerate-uncertainty
severity: high
category: tenchat

### What went wrong
- TenChat session `ok: false` на VPS; `browser_ensure_sessions` + `set -e` в cron worker блокировали весь phase 3.
- Webhook HTTP-поток зависал на sync Playwright (health connection reset).
- `--finish` требует tenchat=published → очередь не закрывается без релогина.

### How the agent recovered this run
- Soft session gate в deferred + cron `|| echo WARN`.
- Webhook → async 202 + background Popen.
- Cloud Max/VK/FB уже опубликованы; site cover залита.

### Durable fix needed before next run
- Релогин TenChat на VPS (`tenchat-vnc-login.sh`).
- Перезапуск systemd webhook после деплоя async-сервера.
- Повтор `/publish` или cron для TG+b17+TenChat.

### Suggested files to inspect/change
- `scripts/vps-webhook-server.py`
- `scripts/run-linux-browser-worker.sh`
- `scripts/publish-browser-deferred.py`
- `posts-emdr-memory/profile/browser-autonomous-vps.md`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-08-03
fix_summary:
- TenChat снят с MSP short-blog: `POSTS_EMDR_SKIP_TENCHAT=1` (default).
- `browser_worker_finish` и `publish-browser-deferred` не требуют tenchat=published.
- VPS phase 3: Telegram + b17 only.
files_changed:
- `scripts/posts_emdr_env.py`
- `scripts/browser_worker_finish.py`
- `scripts/publish-browser-deferred.py`
- `scripts/publish-topic.py`
checks_run:
- `python -m py_compile scripts/browser_worker_finish.py scripts/publish-browser-deferred.py scripts/publish-topic.py scripts/posts_emdr_env.py`
