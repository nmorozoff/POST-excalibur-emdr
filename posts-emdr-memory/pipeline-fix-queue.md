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
