# Publish log — sb-28-end-workday-ritual

**Date:** 2026-09-09
**Status:** published_scripts_partial

## Steps

### cover
```json
{
  "status": "exists",
  "path": "/workspace/posts-emdr-memory/output/sb-28-end-workday-ritual/cover.png"
}
```

### max
```json
{
  "status": "sent",
  "mode": "publish",
  "chat_id": "[REDACTED]",
  "log": "/workspace/posts-emdr-memory/output/sb-28-end-workday-ritual/max-publish-log.json"
}
```

### telegram
```json
{
  "mode": "mcp_handoff",
  "handoff": "/workspace/posts-emdr-memory/output/sb-28-end-workday-ritual/telegram-mcp-handoff.json",
  "channels": 1,
  "publish": {
    "topic": "sb-28-end-workday-ritual",
    "via": "direct_bot_api",
    "results": [
      {
        "chat_id": "[REDACTED]",
        "message_id": 149,
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
  "topic": "sb-28-end-workday-ritual",
  "profile_chars": 4735,
  "group_chars": 4795,
  "cover_local": "/workspace/posts-emdr-memory/output/sb-28-end-workday-ritual/cover.png",
  "cover_jpeg_bytes": 70798,
  "cover_public_url": "[REDACTED]/wp-content/uploads/2026/09/sb-28-end-workday-ritual-3.jpg",
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
"/workspace/posts-emdr-memory/output/sb-28-end-workday-ritual/vk-mcp-handoff.json"
```

### facebook
```json
{
  "stdout": "{\n  \"topic\": \"sb-28-end-workday-ritual\",\n  \"profile_chars\": 4735,\n  \"group_chars\": 4795,\n  \"cover_local\": \"/workspace/posts-emdr-memory/output/sb-28-end-workday-ritual/cover.png\",\n  \"deleted_remote_files\": [\n    \"sb-28-end-workday-ritual.jpg\",\n    \"sb-28-end-workday-ritual-v2.jpg\"\n  ]\n}\n{\n  \"topic\": \"sb-28-end-workday-ritual\",\n  \"platform\": \"facebook\",\n  \"chars\": 4969,\n  \"cover_url\": \"[REDACTED]/wp-content/uploads/2026/09/sb-28-end-workday-ritual-6.jpg\",\n  \"dry_run\": false,\n  \"zernio_post_id\": \"6aa11e630fdc6f1f88900e44\",\n  \"status\": \"published\",\n  \"platform_post_id\": \"632301483303094_122184666512837712\",\n  \"platform_post_url\": \"https://www.facebook.com/632301483303094_122184666512837712\",\n  \"page\": \"Психолог EMDR терапевт Наталья Морозова\"\n}",
  "stderr": ""
}
```

### ok_mode
```json
"mcp_handoff"
```

### ok_mcp_handoff
```json
"/workspace/posts-emdr-memory/output/sb-28-end-workday-ritual/ok-mcp-handoff.json"
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
"/workspace/posts-emdr-memory/output/sb-28-end-workday-ritual/browser-local-handoff.md"
```

**Deferred (no Undetectable):** b17, vk_mcp, ok_mcp
