# Posts EMDR — Handoff

=== POSTS EMDR DONE ===

status: partial
updated_at: 2026-08-21
topic_id: sb-21-minute-silence
title: Минута тишины без телефона
post_type: микро-практика
site_url: https://morozovanatalia.ru/anxiety?utm_source=max
mode: full publish
overall: fail (Telegram VPS pending)

## Прогон sb-21-minute-silence (2026-08-21)

Cloud: Max, VK×2, Facebook, OK — OK
VPS: b17 published; Telegram fail (proxy timeout ×3)
Отчётик: fail → отчёт в Макс отправлен
Fixic: INC-20260821-0950 fixed (retry/preflight в scripts), VPS re-trigger 202

## Ссылки
- Max: https://max.ru/se13417616_biz/AaAjnqKxMNY
- VK: https://vk.com/wall218367867_695, https://vk.com/wall-224685309_172
- FB: https://www.facebook.com/632301483303094_122182845002837712
- OK: https://ok.ru/group/70000034253679/topic/161383725297775
- b17: https://www.b17.ru/blog/minuta_tishiny_bez_telefona/
- Telegram: pending (VPS proxy timeout)

## Recovery
На VPS после `git pull origin main`:
`python3 scripts/trigger-vps-webhook.py --topic sb-21-minute-silence`

Gate: telegram-publish-log.json + browser-worker-finish.json

## Следующий прогон

Intake **только** через `python3 scripts/next-short-blog-topic.py --sync --json`.
Не начинать новую тему пока Telegram sb-21 не pass (INC closed, queue published).
