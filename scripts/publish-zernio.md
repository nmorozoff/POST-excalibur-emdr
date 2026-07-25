# Публикация Facebook через Zernio API

**Область:** только Facebook Page.  
**LinkedIn:** отменён (блокировка).  
**Не использовать Zernio для:** Макс, Telegram, VK.

## Предусловия

1. `posts-emdr-memory/zernio.env.local`:
   - `ZERNIO_API_KEY`
   - `ZERNIO_PROFILE_ID` (опционально)
   - `ZERNIO_FACEBOOK_ACCOUNT_ID`
2. Готовы `facebook-post.md`, `cover.png`.

## Публикация

```bash
python scripts/publish-zernio-post.py --topic 01-panic-night
```

Скрипт:
1. `--upload-cover` → JPG на morozovanatalia.ru
2. `POST https://zernio.com/api/v1/posts` (`publishNow`, `mediaItems`)
3. gate: `status: published` + `platformPostUrl`
4. `--delete-cover` с FTP

## Gate

- `zernio-publish-log.json` с `platform_post_url`
- Обложка удалена с сайта

## Запреты

- LinkedIn через Zernio не использовать
- Не менять send-telegram / send-vk / send-max
