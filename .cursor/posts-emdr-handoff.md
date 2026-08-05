# Posts EMDR — Handoff

status: READY_FOR_CLOUD_AUTOMATION
updated_at: 2026-08-05
next_topic_id: sb-09-one-question-calms
next_title: Один вопрос, который снижает тревогу лучше, чем «успокойся»
post_type: микро-практика
site_url: https://morozovanatalia.ru/anxiety
mode: full publish

## Завтра — только запуск Cloud Automation

Контент **не** готовить заранее. Директор в automation:

1. INTAKE: `incident_queue` → 0; `git pull`; первая `pending` в `short-blog-queue.md` = sb-09
2. КОНТЕНТ через Task (не вручную):
   - max-post.md + cover-prompt.txt — Директор
   - telegram-post.md — Task posts-emdr-telegram-writer
   - vk-profile-post.md / vk-group-post.md — Task posts-emdr-vk-writer
   - facebook-post.md — Task posts-emdr-facebook-writer
   - **ok-post.md** — Task posts-emdr-ok-writer *(новая платформа)*
   - b17-blog-post.md — рерайт по profile/b17-blog-post-prompt.md
   - cover.png — `kie-cover.py`
3. `publish-topic.py` → MCP VK ×2 → **MCP OK** → git push main → VPS webhook
4. Task posts-emdr-otchetik (polling до pass/fail)

## Готово на сегодня

- [x] OK в пайплайне (handoff, record-ok-publish, verify, orchestrator)
- [x] OPEN_INCIDENTS=0
- [x] sb-08 закрыт (pass)
- [x] sb-09 в очереди `pending`, output/ пустой — контент с нуля в automation
- [ ] `git push origin main` — обязательно до запуска automation

## Запреты на automation

- Не публиковать в @morozova_emdr
- Не TenChat / LinkedIn
- Не дублировать TG (link_preview only)
- Не помечать published вручную — VPS --finish
- Не генерировать контент без Task (кроме max + b17 рерайт по промпту)
