# Posts EMDR — Cloud first run (утро)

status: ready_for_cloud_first_run
updated_at: 2026-08-01
next_topic: sb-05-tolerate-uncertainty

## Что уже готово сегодня

- Telegram **только с VPS** (ASocks KZ) — Cloud больше не шлёт в TG
- b17: HTTPS cover + verify списка (не base64)
- TenChat: session OK на VPS
- Webhook + cron worker
- `publish-topic.py` пишет `browser-local-handoff.md` и откладывает TG/b17/TenChat

## Утром — чеклист (5 мин)

### 1. Cursor Cloud Dashboard
- [ ] Runtime Secrets из `posts-emdr-memory/cloud-secrets-checklist.txt`
- [ ] **`VPS_WEBHOOK_SECRET`** = тот же, что в VPS `browser.env.local`
- [ ] MCP **mcp-kv** включён для Cloud Agent

### 2. VPS (если ночь всё ещё up)
```bash
ssh -i ~/Documents/privatekey-1099880.pem ubuntu@195.209.210.45
curl -sS http://127.0.0.1:8787/health
cd ~/POST-excalibur-emdr && .venv-browser/bin/python scripts/check-tenchat-access.py
```

### 3. Запуск Cloud Agent — промпт

```
Режим: full publish, тема sb-05-tolerate-uncertainty (первая pending в short-blog-queue.md).

1. Прочитать posts-emdr-memory/profile/cloud-publish-phases.md
2. Сгенерировать контент всех платформ (Макс→TG→VK×2→FB→b17→TenChat)
   В telegram-post.md обязателен маркер <!-- END_POST --> до ## Мета
3. python3 scripts/materialize_cloud_env.py --check
4. python3 scripts/publish-topic.py --topic sb-05-tolerate-uncertainty
5. MCP vk_create_post_with_photo ×2 по output/.../vk-mcp-handoff.json
6. python3 scripts/send-vk-post.py --topic sb-05-tolerate-uncertainty --delete-cover
7. Обновить реестры max / vk-profile / vk-group / facebook
8. git add + commit + push output/sb-05-... и реестры
9. curl webhook:
   curl -fsS -X POST "http://195.209.210.45:8787/publish" \
     -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \
     -H "Content-Type: application/json" \
     -d '{"topic":"sb-05-tolerate-uncertainty"}'
10. НЕ помечать published в очереди — VPS --finish сделает сам
```

## Ожидаемый результат

| Платформа | Кто |
|-----------|-----|
| Макс, Facebook | Cloud scripts |
| VK ×2 | Cloud MCP |
| Telegram ×3 | VPS + ASocks KZ |
| b17, TenChat | VPS Playwright |

## Если webhook 500

На VPS смотреть stdout в ответе; fallback:
```bash
cd ~/POST-excalibur-emdr && source .venv-browser/bin/activate
git pull
python3 scripts/publish-browser-deferred.py --topic sb-05-tolerate-uncertainty --submit --finish --git-push
```

=== READY FOR CLOUD FIRST RUN ===
