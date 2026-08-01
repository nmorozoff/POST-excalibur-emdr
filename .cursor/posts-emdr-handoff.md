# Posts EMDR — Cloud first run (утро)

status: ready_for_cloud_first_run
updated_at: 2026-08-01
next_topic: sb-05-tolerate-uncertainty

## Сделано сегодня (автоматика)

- [x] Telegram только с VPS (ASocks KZ) — Cloud не шлёт TG
- [x] b17 HTTPS cover + verify списка
- [x] Код запушен: `02847aa` → origin/main
- [x] VPS: чистый `git clone`, secrets/venv восстановлены
- [x] Webhook systemd **active** `:8787` (снаружи health OK)
- [x] Cron каждые 10 мин
- [x] b17 session OK
- [ ] **TenChat cookies — нужен один перелогин** (см. ниже)

## Сегодня вечером (обязательно, ~5 мин) — TenChat

Сессия TenChat слетела (`auth_required`). Без этого утренний прогон остановится на TenChat.

```bash
# Терминал 1 — VPS
ssh -i ~/Documents/privatekey-1099880.pem ubuntu@195.209.210.45
cd ~/POST-excalibur-emdr && source .venv-browser/bin/activate
./scripts/tenchat-vnc-login.sh

# Терминал 2 — Mac
ssh -i ~/Documents/privatekey-1099880.pem -L 6080:127.0.0.1:6080 ubuntu@195.209.210.45
# Chrome → http://localhost:6080/vnc.html → Connect → войти в TenChat (SMS)
```

Проверка:
```bash
cd ~/POST-excalibur-emdr && .venv-browser/bin/python scripts/check-tenchat-access.py
# нужно: "ok": true
```

## Утром — Cloud Dashboard (1 мин)

- [ ] Runtime Secrets из `cloud-secrets-checklist.txt`
- [ ] **`VPS_WEBHOOK_SECRET`** = значение из VPS `posts-emdr-memory/browser.env.local`
- [ ] MCP **mcp-kv** включён

## Утром — промпт Cloud Agent

```
Режим: full publish. Тема: первая pending в short-blog-queue.md (sb-05-tolerate-uncertainty).

1. Читать posts-emdr-memory/profile/cloud-publish-phases.md
2. Сгенерировать контент всех платформ
   telegram-post.md: маркер <!-- END_POST --> до ## Мета
3. python3 scripts/materialize_cloud_env.py --check
4. python3 scripts/publish-topic.py --topic sb-05-tolerate-uncertainty
5. MCP vk_create_post_with_photo ×2 по vk-mcp-handoff.json
6. python3 scripts/send-vk-post.py --topic sb-05-tolerate-uncertainty --delete-cover
7. Обновить реестры max / vk-profile / vk-group / facebook
8. git add + commit + push output/sb-05-... и реестры
9. curl -fsS -X POST "http://195.209.210.45:8787/publish" \
     -H "Authorization: Bearer $VPS_WEBHOOK_SECRET" \
     -H "Content-Type: application/json" \
     -d '{"topic":"sb-05-tolerate-uncertainty"}'
10. НЕ помечать published — VPS --finish сделает сам
```

## Кто что публикует

| Платформа | Кто |
|-----------|-----|
| Макс, Facebook | Cloud |
| VK ×2 | Cloud MCP |
| Telegram ×3 | VPS + ASocks KZ |
| b17, TenChat | VPS Playwright |

=== READY FOR CLOUD FIRST RUN ===
(после TenChat re-login)
