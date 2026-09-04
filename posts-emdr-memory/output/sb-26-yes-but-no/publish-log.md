# Publish log — sb-26-yes-but-no

**Date:** 2026-09-04
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
  "chat_id": "[REDACTED]",
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
        "chat_id": "[REDACTED]",
        "message_id": 144,
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
  "profile_chars": 5289,
  "group_chars": 4796,
  "cover_local": "/workspace/posts-emdr-memory/output/sb-26-yes-but-no/cover.png",
  "cover_jpeg_bytes": 72660,
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
  "stdout": "{\n  \"topic\": \"sb-26-yes-but-no\",\n  \"profile_chars\": 5289,\n  \"group_chars\": 4796,\n  \"cover_local\": \"/workspace/posts-emdr-memory/output/sb-26-yes-but-no/cover.png\",\n  \"deleted_remote_files\": [\n    \"sb-26-yes-but-no.jpg\",\n    \"sb-26-yes-but-no-v2.jpg\"\n  ]\n}\n{\n  \"topic\": \"sb-26-yes-but-no\",\n  \"platform\": \"facebook\",\n  \"chars\": 5011,\n  \"cover_url\": \"https://morozovanatalia.ru/social-covers/sb-26-yes-but-no.jpg\",\n  \"dry_run\": false,\n  \"zernio_post_id\": \"6a9aa29f51c6e8aa03c929f8\",\n  \"status\": \"published\",\n  \"platform_post_id\": \"632301483303094_122184184904837712\",\n  \"platform_post_url\": \"https://www.facebook.com/632301483303094_122184184904837712\",\n  \"page\": \"Психолог EMDR терапевт Наталья Морозова\"\n}",
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
