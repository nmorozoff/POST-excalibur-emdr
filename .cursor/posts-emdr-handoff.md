# Posts EMDR — handoff

status: blocked
started_at: 2026-07-25
blocked_at: 2026-07-25

## Текущая тема

topic_id: sb-03-body-before-mind
title: Момент, когда тело узнаёт о тревоге раньше головы
post_type: short-blog · наблюдение→инсайт
site_url: https://morozovanatalia.ru/anxiety
mode: full
publish: yes (blocked — нет секретов в cloud)
queue: topics/short-blog-queue.md (#3 MSP)

## Прогресс

- [x] 0 topic picked
- [x] 1 MAX — контент + cover.png (публикация ❌ нет max.env.local)
- [x] 2 Telegram — рерайт готов (публикация ❌)
- [x] 3 VK profile — рерайт готов (публикация ❌ нет MCP VK)
- [x] 4 VK group — рерайт готов (публикация ❌)
- [x] 5 Facebook — рерайт готов (публикация ❌ нет zernio.env.local)
- [x] 6 b17 — рерайт готов (публикация ❌ нет b17.env.local)
- [x] 7 TenChat — рерайт готов (публикация ❌ нет tenchat.env.local)
- [ ] 8 registries + queue updated

output_dir: posts-emdr-memory/output/sb-03-body-before-mind/

## BLOCKER

Cloud pod: нет `posts-emdr-memory/*.env.local`, нет MCP VK/Telegram.
INC: `pipeline-fix-queue.md#INC-20260725-1755-cloud-missing-secrets-mcp`

**Для завершения:** запустить публикацию локально или настроить секреты в Cloud Environment, затем:

```bash
python3 scripts/send-max-draft.py --topic sb-03-body-before-mind --publish
python3 scripts/send-telegram-post.py --topic sb-03-body-before-mind --publish
python3 scripts/send-vk-post.py --topic sb-03-body-before-mind --upload-cover
# VK MCP personal + group
python3 scripts/publish-zernio-post.py --topic sb-03-body-before-mind
python3 scripts/publish-b17-blog.py --topic sb-03-body-before-mind
python3 scripts/publish-tenchat-post.py --topic sb-03-body-before-mind
```

**Пайплайн:** без кружка Макс. Обложка — fallback GenerateImage (не Runware i2i).
