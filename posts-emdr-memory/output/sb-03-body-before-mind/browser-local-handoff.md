# Browser publish — b17 + TenChat (Linux VPS)

Тема: `sb-03-body-before-mind`

Cloud не опубликовал b17/TenChat — на VPS должен отработать **Playwright worker**.

## Linux VPS (рекомендуется)

См. `posts-emdr-memory/profile/browser-linux-vps-setup.md`

```bash
cd ~/POST-excalibur-emdr
git pull --ff-only
source .venv-browser/bin/activate
python3 scripts/fetch-topic-cover.py --topic sb-03-body-before-mind
python3 scripts/publish-browser-deferred.py --topic sb-03-body-before-mind --submit
```

Или дождаться cron (~10 мин).

## Mac (fallback, Undetectable)

```bash
cd "/workspace"
python3 scripts/publish-b17-blog.py --topic sb-03-body-before-mind --submit
python3 scripts/publish-tenchat-post.py --topic sb-03-body-before-mind --submit
```

## После публикации

Обновить реестры b17/tenchat и `short-blog-queue.md`.
