# Publish log — sb-21-minute-silence

**Date:** 2026-08-21
**Status:** published_scripts_partial

## Steps

### cover
```json
{
  "status": "exists",
  "path": "/workspace/posts-emdr-memory/output/sb-21-minute-silence/cover.png"
}
```

### max
```json
{
  "status": "sent",
  "mode": "publish",
  "chat_id": "[REDACTED]",
  "log": "/workspace/posts-emdr-memory/output/sb-21-minute-silence/max-publish-log.json"
}
```

### telegram
```json
{
  "deferred": true,
  "reason": "vps_asocks_kz",
  "note": "publish-browser-deferred.py на VPS"
}
```

### vk_upload
```json
{
  "topic": "sb-21-minute-silence",
  "profile_chars": 4573,
  "group_chars": 4159,
  "cover_local": "/workspace/posts-emdr-memory/output/sb-21-minute-silence/cover.png",
  "cover_jpeg_bytes": 64575,
  "cover_public_url": "https://morozovanatalia.ru/social-covers/sb-21-minute-silence.jpg",
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
"/workspace/posts-emdr-memory/output/sb-21-minute-silence/vk-mcp-handoff.json"
```

### facebook
```json
{
  "stdout": "{\n  \"topic\": \"sb-21-minute-silence\",\n  \"profile_chars\": 4573,\n  \"group_chars\": 4159,\n  \"cover_local\": \"/workspace/posts-emdr-memory/output/sb-21-minute-silence/cover.png\",\n  \"deleted_remote_files\": [\n    \"sb-21-minute-silence.jpg\",\n    \"sb-21-minute-silence-v2.jpg\"\n  ]\n}\n{\n  \"topic\": \"sb-21-minute-silence\",\n  \"platform\": \"facebook\",\n  \"chars\": 1535,\n  \"cover_url\": \"https://morozovanatalia.ru/social-covers/sb-21-minute-silence.jpg\",\n  \"dry_run\": false,\n  \"zernio_post_id\": \"6a881a529936407f5231fde3\",\n  \"status\": \"published\",\n  \"platform_post_id\": \"632301483303094_122182845002837712\",\n  \"platform_post_url\": \"https://www.facebook.com/632301483303094_122182845002837712\",\n  \"page\": \"Психолог EMDR терапевт Наталья Морозова\"\n}",
  "stderr": ""
}
```

### ok_mode
```json
"mcp_handoff"
```

### ok_mcp_handoff
```json
"/workspace/posts-emdr-memory/output/sb-21-minute-silence/ok-mcp-handoff.json"
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
"/workspace/posts-emdr-memory/output/sb-21-minute-silence/browser-local-handoff.md"
```

**Deferred (no Undetectable):** telegram, b17, vk_mcp, ok_mcp
