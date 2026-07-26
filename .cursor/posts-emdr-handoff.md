# Posts EMDR — handoff

status: blocked
started_at: 2026-07-26
completed_at:

## Текущая тема

topic_id: sb-03-body-before-mind
title: Момент, когда тело узнаёт о тревоге раньше головы
post_type: short-blog · наблюдение→инсайт
site_url: https://morozovanatalia.ru/anxiety
mode: full
publish: yes
queue: topics/short-blog-queue.md (#3 MSP · in_progress)

## Прогресс

- [x] 0 topic picked
- [x] 1 MAX — контент + cover-prompt готовы; **publish blocked** (нет RUNWARE + MAX secrets)
- [x] 2 Telegram — контент готов; publish blocked
- [x] 3 VK profile — контент готов; publish blocked
- [x] 4 VK group — контент готов; publish blocked
- [x] 5 Facebook — контент готов; publish blocked
- [x] 6 b17 — контент готов; deferred (Undetectable + secrets)
- [x] 7 TenChat — контент готов; deferred (Undetectable + secrets)
- [ ] 8 registries + queue updated (после publish)

output_dir: posts-emdr-memory/output/sb-03-body-before-mind/

## BLOCKER

`ready_for_auto_publish: false` — нет Cursor Cloud Secrets.  
См. `posts-emdr-memory/CLOUD-SETUP.md`, incident `INC-20260726-0700-cloud-secrets-not-configured`.

После Secrets:
```bash
python3 scripts/publish-topic.py --topic sb-03-body-before-mind
```

**Пайплайн:** без кружка Макс. Обложка Runware — автоматически.
