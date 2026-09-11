# Локальная автоматизация Posts EMDR (Mac)

**Основной режим** с 2026-09-10. Cloud Automation в Dashboard — **отключить** (дублировала Max/TG).

## Расписание

**12:00 MSK** — `launchd` → `scripts/local-publish-wrapper.sh`

**Сейчас cron выключен** (2026-09-11) — после фикса дублей включить снова: `./deploy/local-cron/install-macos-launchd.sh`

### Установка cron (один раз)

```bash
cd "/Users/natala/Documents/Проекты СURSOR/Посты EMDR"
chmod +x scripts/local-publish-wrapper.sh deploy/local-cron/install-macos-launchd.sh
./deploy/local-cron/install-macos-launchd.sh
```

Требования перед 12:00:
- Mac включён, Undetectable запущен, **Profile1** залогинен (VK, b17, TenChat)
- `b17.env.local` — `UNDETECTABLE_PROFILE_ID`
- `max.env.local`, `telegram.env.local`, Zernio env

## Что делает прогон

1. `flock` (без параллельных прогонов)
2. `git pull origin main`
3. Следующая тема из очереди
4. Grsai контент (+ `tenchat-post.md`)
5. Макс → обложка на сайт → **Telegram** (`link_preview` + morozovanatalia) → Facebook
6. **VK ×2** — Undetectable browser (`publish-vk-browser.py`)
7. **b17** + **TenChat** — Undetectable `--submit`
8. `close-cloud-publish.py`, verify, отчёт в Макс, `git push`

## Идемпотентность

Повторный прогон **не** дублирует пост, если в логах уже `sent`/`published`:
- `publish_idempotency.py` + durable markers в `/tmp/posts-emdr-state/`

Принудительно: `--force` у `send-max-draft.py` / `send-telegram-post.py`.

## OK (Одноклассники)

Пока только через MCP (Cloud). Локальный cron OK не публикует — `verify` может быть `pass_b17_pending` / partial OK.

## Логи

`posts-emdr-memory/logs/local-publish-*.log`

## Ручной прогон

```bash
python3 scripts/vps_publish_guard.py run -- python3 scripts/run-local-publish.py --worker
```

## Telegram без обложки

```bash
python3 scripts/send-telegram-post.py --topic ID --publish --refresh-cover-url --force
```
