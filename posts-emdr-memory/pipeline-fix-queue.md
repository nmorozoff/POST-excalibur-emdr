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
status: needs-human
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
- MSP short-blog: primary `kie-cover.py` (уже в `publish-topic.py` / pitfalls).
- `runware-cover.py`: явный exit при `insufficientCredits` → hint на kie-cover.
needed_decision_or_secret:
- Пополнить кошелёк Runware, если нужен legacy `runware-cover.py` без Kie.
files_changed:
- `scripts/runware-cover.py`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`
checks_run:
- `python -m py_compile scripts/runware-cover.py`

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
- ~~Релогин TenChat~~ — платформа снята с пайплайна (2026-08-03).
- Webhook async + git config VPS — сделано.

### Fixic resolution
fixed_at: 2026-08-03
fix_summary:
- TenChat снят с пайплайна; finish/deferred/session gate больше не зависят от TenChat
files_changed:
- scripts/publish-browser-deferred.py
- scripts/browser_worker_finish.py
- .cursor/rules/posts-emdr-orchestrator.mdc
- `posts-emdr-memory/profile/browser-autonomous-vps.md`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-08-03
fix_summary:
- TenChat снят из MSP short-blog VPS gate: deferred worker публикует только TG+b17.
- `browser_worker_finish.py`: finish без tenchat=published; tenchat registry только если уже published.
- Pitfall: TenChat вне MSP phase 3.
files_changed:
- `scripts/publish-browser-deferred.py`
- `scripts/browser_worker_finish.py`
- `scripts/vps-webhook-server.py`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`
checks_run:
- `python -m py_compile scripts/publish-browser-deferred.py scripts/browser_worker_finish.py scripts/vps-webhook-server.py`

---

## INC-20260803-1800-vps-git-pull-dirty-tree
status: fixed
run_date: 2026-08-03
role: vps
topic: sb-05-tolerate-uncertainty
severity: high
category: vps

### What went wrong
- Webhook HTTP 202, но `git_pull` на VPS failed: локальные изменения + untracked `kie-*.py` блокируют merge.
- Phase 3 (Telegram, b17) не завершён; `--finish` не выполнен.

### How the agent recovered this run
- Cloud фазы 1–2 OK (Max, VK×2, Facebook).
- Повторный webhook после fix `stash -u` + `reset --hard FETCH_HEAD` в ветке `cursor/short-blog-end-to-end-dcaa`.
- sb-05 опубликован вручную 2026-08-03; VPS синхронизирован 2026-08-04.

### Durable fix needed before next run
- Merge fix в `main`; на VPS: `systemctl restart posts-emdr-webhook`.
- Повтор `POST /publish` с topic sb-05.

### Fixic resolution
fixed_at: 2026-08-04
fix_summary:
- PR #12: webhook и cron worker делают `git stash -u` + `git fetch origin main` + `git reset --hard FETCH_HEAD`.
- Добавлены скрипты: `trigger-vps-webhook.py`, `verify-vps-webhook-secret.py`, `is-topic-published.py`.
- Cloud prompt обновлён: `git pull` перед чтением очереди + проверка `is-topic-published`.
- VPS синхронизирован до `origin/main`, webhook перезапущен, dry-run 202 OK.
files_changed:
- scripts/vps-webhook-server.py
- scripts/run-linux-browser-worker.sh
- scripts/trigger-vps-webhook.py
- scripts/verify-vps-webhook-secret.py
- scripts/is-topic-published.py
- scripts/publish-topic.py
- posts-emdr-memory/profile/cloud-automation-prompt.md
checks_run:
- python3 -m py_compile scripts/trigger-vps-webhook.py scripts/verify-vps-webhook-secret.py scripts/is-topic-published.py scripts/publish-topic.py scripts/vps-webhook-server.py
- python3 scripts/verify-vps-webhook-secret.py
- python3 scripts/trigger-vps-webhook.py --topic sb-05-tolerate-uncertainty --dry-run

### Secrets
- none recorded

---

## INC-20260804-1405-sb06-vps-phase3-stuck
status: fixed
run_date: 2026-08-04
role: otchetik
topic: sb-06-cant-sleep-anxiety
severity: high
category: vps

### What went wrong
- Webhook HTTP 202 принят, но через 12+ мин нет `browser-worker-finish.json`, `telegram-publish-log.json`, `b17-publish-log.json`.
- Telegram и b17 не опубликованы; тема остаётся `in_progress` в очереди.

### How the agent recovered this run
- Root cause: контент на feature branch, VPS `git pull origin main` не видел output.
- PR #13 merged to main; VPS webhook re-triggered.

### Durable fix needed before next run
- Проверить VPS: `systemctl is-active posts-emdr-webhook`, cron `run-linux-browser-worker.sh`, логи worker.
- Повторить phase 3 для sb-06 или ручная публикация TG+b17.

### Suggested files to inspect/change
- `scripts/vps-webhook-server.py`
- `scripts/publish-browser-deferred.py`
- `scripts/browser_worker_finish.py`
- `scripts/trigger-vps-webhook.py`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-08-04
fix_summary:
- `trigger-vps-webhook.py`: gate — локальная ветка должна быть `main` (обход `--skip-main-check`).
- Pitfalls + cloud-automation-prompt: merge в main до VPS webhook.
- Run recovery: PR #13 merged, webhook re-triggered (ops, не код).
needed_decision_or_secret:
- Подтвердить на VPS завершение phase 3 sb-06 (TG+b17+finish) после re-trigger.
files_changed:
- `scripts/trigger-vps-webhook.py`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`
- `posts-emdr-memory/profile/cloud-automation-prompt.md`
checks_run:
- `python3 -m py_compile scripts/trigger-vps-webhook.py`

---

## INC-20260804-1405-sb06-facebook-zernio-scheduled
status: fixed
run_date: 2026-08-04
role: otchetik
topic: sb-06-cant-sleep-anxiety
severity: medium
category: facebook

### What went wrong
- Zernio `zernio-publish-log.json`: `status: scheduled`, `platform_post_url: null` (Meta transient error, auto-retry ожидается).
- `verify-publish-run.py` считает hard_fail — нет URL в реестре.
- `publish-topic.py` падал раньше: `publish-zernio-post.py` не принимал `--publish`.

### How the agent recovered this run
- Zernio auto-retry ожидается; FB шаг cloud мог быть пропущен из-за `--publish` bug.

### Durable fix needed before next run
- Дождаться Zernio retry или проверить статус поста `6a71ee34db57b077c09c2340` в Meta.
- Опционально: treat `scheduled` как partial в verify (не hard_fail).

### Suggested files to inspect/change
- `scripts/publish-zernio-post.py`
- `scripts/verify-publish-run.py`
- `posts-emdr-memory/profile/facebook-posts-registry.md`

### Secrets
- none recorded

### Fixic resolution
fixed_at: 2026-08-04
fix_summary:
- `publish-zernio-post.py`: `--publish` no-op; `scheduled` не abort (cover не удаляется).
- `verify-publish-run.py`: `scheduled` → partial, не hard_fail; читает `platform_post_url`.
needed_decision_or_secret:
- Проверить в Meta/Zernio, что пост `6a71ee34db57b077c09c2340` перешёл в published и обновить facebook-posts-registry.
files_changed:
- `scripts/publish-zernio-post.py`
- `scripts/verify-publish-run.py`
- `scripts/kie-cover.py`
- `posts-emdr-memory/shared/agent-pipeline-pitfalls.md`
checks_run:
- `python3 -m py_compile scripts/publish-zernio-post.py scripts/verify-publish-run.py scripts/kie-cover.py`

