# Publish log — sb-26-yes-but-no

**Date:** 2026-09-07
**Status:** published_scripts_partial

## Steps

### cover
```json
{
  "status": "exists",
  "path": "/workspace/posts-emdr-memory/output/sb-26-yes-but-no/cover.png"
}
```

### max
```json
{
  "status": "sent",
  "mode": "publish",
  "chat_id": "CHANNEL_HANDLE",
  "log": "/workspace/posts-emdr-memory/output/sb-26-yes-but-no/max-publish-log.json"
}
```

### telegram
```json
{
  "mode": "mcp_handoff",
  "handoff": "/workspace/posts-emdr-memory/output/sb-26-yes-but-no/telegram-mcp-handoff.json",
  "channels": 1,
  "publish": {
    "topic": "sb-26-yes-but-no",
    "via": "direct_bot_api",
    "results": [
      {
        "chat_id": "TG_CHANNEL",
        "message_id": 146,
        "ok": true
      }
    ]
  },
  "status": "published"
}
```

### vk_upload
```json
{
  "topic": "sb-26-yes-but-no",
  "profile_chars": 4843,
  "group_chars": 4311,
  "cover_local": "/workspace/posts-emdr-memory/output/sb-26-yes-but-no/cover.png",
  "cover_jpeg_bytes": 74692,
  "cover_public_url": "https://morozovanatalia.ru/social-covers/sb-26-yes-but-no.jpg",
  "cover_http_status": 200,
  "cover_serves_image": true,
  "cover_upload_method": "wordpress_media"
}
```

### vk_mode
```json
"mcp_handoff"
```

### vk_mcp_handoff
```json
"/workspace/posts-emdr-memory/output/sb-26-yes-but-no/vk-mcp-handoff.json"
```

### facebook
```json
{
  "stdout": "{\n  \"topic\": \"sb-26-yes-but-no\",\n  \"profile_chars\": 4843,\n  \"group_chars\": 4311,\n  \"cover_local\": \"/workspace/posts-emdr-memory/output/sb-26-yes-but-no/cover.png\",\n  \"deleted_remote_files\": [\n    \"sb-26-yes-but-no.jpg\",\n    \"sb-26-yes-but-no-v2.jpg\"\n  ]\n}\n{\n  \"topic\": \"sb-26-yes-but-no\",\n  \"platform\": \"facebook\",\n  \"chars\": 5161,\n  \"cover_url\": \"https://morozovanatalia.ru/social-covers/sb-26-yes-but-no.jpg\",\n  \"dry_run\": false,\n  \"zernio_post_id\": \"6a9ef47da8f73687d34d0fd5\",\n  \"status\": \"published\",\n  \"platform_post_id\": \"632301483303094_122184508334837712\",\n  \"platform_post_url\": \"https://www.facebook.com/632301483303094_122184508334837712\",\n  \"page\": \"Психолог EMDR терапевт Наталья Морозова\"\n}",
  "stderr": ""
}
```

### ok_mode
```json
"mcp_handoff"
```

### ok_mcp_handoff
```json
"/workspace/posts-emdr-memory/output/sb-26-yes-but-no/ok-mcp-handoff.json"
```

### browser_platforms
```json
{
  "ready": false,
  "skipped": true
}
```

### browser_local_handoff
```json
"/workspace/posts-emdr-memory/output/sb-26-yes-but-no/browser-local-handoff.md"
```

**Deferred (no Undetectable):** b17, vk_mcp, ok_mcp
