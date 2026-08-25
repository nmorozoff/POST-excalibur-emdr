=== POSTS-EMDR-OTCHETIK ===
topic: sb-23-grounding-exercise
overall: fail
max_report_sent: true
incidents_written:
- INC-20260824-0956-sb23-vps-pending (updated follow-up 2026-08-25, no duplicate)
fixic_needed: true
incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260824-0956-sb23-vps-pending

## Summary

Cloud phase 1+2: **pass** (Max, VK profile, VK group, Facebook, OK — все published, ссылки в publish-run-report.json).

VPS phase 3: **fail**. Нет `telegram-publish-log.json`, `browser-worker-finish.json`. `publish_lock_held` >45 мин — зависший worker держит flock; повторный webhook → 409.

Root cause worker (`vps-worker-last-run.json`):
- Telegram: proxy timeout → catbox.moe DNS fail (`Could not resolve host`)
- b17: `Page.goto: net::ERR_TIMED_OUT` на b17.ru

Fix e5f52b1 уже в main (site/max mirror перед catbox), но VPS не подтянул из‑за hung lock.

## Published links

- max: https://max.ru/se13417616_biz/AaAzD65TCJg
- vk_profile: https://vk.com/wall218367867_698
- vk_group: https://vk.com/wall-224685309_174
- facebook: https://www.facebook.com/632301483303094_122183148686837712
- ok: https://ok.ru/group/70000034253679/topic/161387583271023

## Pending

- Telegram: @nmorozova_emdr, @natalia_morozova_psy
- b17: draft/publish после VPS recovery
- Тема `in_progress` в short-blog-queue

## VPS infra (needs-human)

- SSH: kill hung worker, освободить flock
- `git pull origin main` (e5f52b1)
- Один deferred run: `vps_publish_guard.py run -- publish-browser-deferred.py --topic sb-23-grounding-exercise --submit --finish --git-push`
- Проверить: `systemctl is-active posts-emdr-webhook`, cron `run-linux-browser-worker.sh`, `asocks_check.py`, `browser_ensure_sessions.py`

incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260824-0956-sb23-vps-pending
