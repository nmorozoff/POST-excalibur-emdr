# Publish log — sb-27-breath-before-talk

**Date:** 2026-09-08
**Status:** published_scripts_partial

## Steps

### cover
```json
{
  "status": "exists",
  "path": "/workspace/posts-emdr-memory/output/sb-27-breath-before-talk/cover.png"
}
```

### max
```json
{
  "status": "sent",
  "mode": "publish",
  "chat_id": [REDACTED],
  "log": "/workspace/posts-emdr-memory/output/sb-27-breath-before-talk/max-publish-log.json"
}
```

### telegram
```json
{
  "mode": "mcp_handoff",
  "handoff": "/workspace/posts-emdr-memory/output/sb-27-breath-before-talk/telegram-mcp-handoff.json",
  "channels": 1,
  "publish": {
    "topic": "sb-27-breath-before-talk",
    "via": "direct_bot_api",
    "results": [
      {
        "chat_id": "[REDACTED]",
        "message_id": 147,
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
  "topic": "sb-27-breath-before-talk",
  "profile_chars": 5202,
  "group_chars": 4714,
  "cover_local": "/workspace/posts-emdr-memory/output/sb-27-breath-before-talk/cover.png",
  "cover_jpeg_bytes": 84305,
  "cover_public_url": "[REDACTED]/wp-content/uploads/2026/09/sb-27-breath-before-talk.jpg",
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
"/workspace/posts-emdr-memory/output/sb-27-breath-before-talk/vk-mcp-handoff.json"
```

### facebook
```json
{
  "stdout": "{\n  \"topic\": \"sb-27-breath-before-talk\",\n  \"profile_chars\": 5202,\n  \"group_chars\": 4714,\n  \"cover_local\": \"/workspace/posts-emdr-memory/output/sb-27-breath-before-talk/cover.png\",\n  \"deleted_remote_files\": [\n    \"sb-27-breath-before-talk.jpg\",\n    \"sb-27-breath-before-talk-v2.jpg\"\n  ]\n}\n{\n  \"topic\": \"sb-27-breath-before-talk\",\n  \"platform\": \"facebook\",\n  \"chars\": 5362,\n  \"cover_url\": \"[REDACTED]/wp-content/uploads/2026/09/sb-27-breath-before-talk-1.jpg\",\n  \"dry_run\": false,\n  \"zernio_post_id\": \"6a9fc853afca2973a88fb373\",\n  \"status\": \"published\",\n  \"platform_post_id\": \"632301483303094_122184570620837712\",\n  \"platform_post_url\": \"https://www.facebook.com/632301483303094_122184570620837712\",\n  \"page\": \"Психолог EMDR терапевт Наталья Морозова\"\n}",
  "stderr": ""
}
```

### ok_mode
```json
"mcp_handoff"
```

### ok_mcp_handoff
```json
"/workspace/posts-emdr-memory/output/sb-27-breath-before-talk/ok-mcp-handoff.json"
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
"/workspace/posts-emdr-memory/output/sb-27-breath-before-talk/browser-local-handoff.md"
```

**Deferred (no Undetectable):** b17, vk_mcp, ok_mcp
