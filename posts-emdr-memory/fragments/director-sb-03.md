# Fragment — director sb-03-body-before-mind

**role:** director  
**topic:** sb-03-body-before-mind  
**date:** 2026-07-26

## Done

- Тема `sb-03-body-before-mind` взята из очереди (#3 MSP), помечена `in_progress`
- Сгенерирован полный контент: max, telegram, vk×2, facebook, b17, tenchat
- cover-prompt.txt с outfit #3 (warm grey cardigan + white shirt)
- handoff обновлён

## Blocked

- `materialize_cloud_env.py --check` → `ready_for_auto_publish: false`
- Нет Runtime Secrets в Cloud Environment (MAX, Telegram, VK, Zernio, Runware, FTP)
- `runware-cover.py` и `publish-topic.py` не запускаются

## Next

1. Владелец добавляет Secrets в Cursor Cloud Environment
2. `python3 scripts/publish-topic.py --topic sb-03-body-before-mind`
3. После publish: обновить реестры, перенести тему в short-blog-published.md

incident_report: posts-emdr-memory/pipeline-fix-queue.md#INC-20260726-0700-cloud-secrets-not-configured
