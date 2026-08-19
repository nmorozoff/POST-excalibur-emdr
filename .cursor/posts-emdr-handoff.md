# Posts EMDR — Handoff

status: in_progress
updated_at: 2026-08-19
topic_id: sb-19-question-before-sleep
title: Один вопрос себе перед сном, который меняет качество утра
post_type: микро-практика
site_url: https://morozovanatalia.ru/anxiety?utm_source=max
mode: full publish
overall: fail (VPS phase 3 blocked)

## Прогон sb-19-question-before-sleep (2026-08-19 cron)

ШАГ 0–4: OK (cloud + MCP + main f6cac0f/1255fb3)
ШАГ 5: VPS webhook FAIL — Connection reset peer 195.209.210.45:8787
ШАГ 6: Отчётик fail, отчёт в Макс отправлен
ШАГ 7: Fixic — INC-20260819-1745-sb19-vps-webhook-connection-reset (open)

## Ссылки (опубликовано)
- Max: https://max.ru/se13417616_biz/AaAbGflxdSc
- VK: https://vk.com/wall218367867_693, https://vk.com/wall-224685309_170
- FB: https://www.facebook.com/632301483303094_122182671764837712
- OK: https://ok.ru/group/70000034253679/topic/161377985065071

## Ожидает VPS
- Telegram @nmorozova_emdr, @natalia_morozova_psy
- b17 черновик/публикация
- После восстановления VPS: `python3 scripts/trigger-vps-webhook.py --topic sb-19-question-before-sleep`

## Следующий запуск
Не начинать sb-20 до закрытия sb-19 (VPS finish + mark-short-blog-published).
