# Publish log — sb-19-question-before-sleep

**Date:** 2026-08-19
**Status:** published_scripts_partial

## Steps

### cover
```json
{
  "status": "exists",
  "path": "/workspace/posts-emdr-memory/output/sb-19-question-before-sleep/cover.png"
}
```

### max
```json
{
  "status": "sent",
  "mode": "publish",
  "chat_id": "[REDACTED]",
  "log": "/workspace/posts-emdr-memory/output/sb-19-question-before-sleep/max-publish-log.json"
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
  "topic": "sb-19-question-before-sleep",
  "profile_chars": 4719,
  "group_chars": 4530,
  "cover_local": "/workspace/posts-emdr-memory/output/sb-19-question-before-sleep/cover.png",
  "cover_jpeg_bytes": 83690,
  "cover_public_url": "https://morozovanatalia.ru/social-covers/sb-19-question-before-sleep.jpg",
  "cover_http_status": 200,
  "cover_serves_image": true,
  "cover_upload_method": "curl_pasv"
}
```

### vk_mode
```json
"mcp_handoff"
```

### vk_mcp_handoff
```json
"/workspace/posts-emdr-memory/output/sb-19-question-before-sleep/vk-mcp-handoff.json"
```

### facebook
```json
{
  "stdout": "{\n  \"topic\": \"sb-19-question-before-sleep\",\n  \"profile_chars\": 4719,\n  \"group_chars\": 4530,\n  \"cover_local\": \"/workspace/posts-emdr-memory/output/sb-19-question-before-sleep/cover.png\",\n  \"deleted_remote_files\": [\n    \"sb-19-question-before-sleep.jpg\",\n    \"sb-19-question-before-sleep-v2.jpg\"\n  ]\n}\n{\n  \"topic\": \"sb-19-question-before-sleep\",\n  \"platform\": \"facebook\",\n  \"chars\": 6035,\n  \"cover_url\": \"https://morozovanatalia.ru/social-covers/sb-19-question-before-sleep.jpg\",\n  \"dry_run\": false,\n  \"zernio_post_id\": \"6a85ea113c1e6d9b7c9214dc\",\n  \"status\": \"published\",\n  \"platform_post_id\": \"632301483303094_122182671764837712\",\n  \"platform_post_url\": \"https://www.facebook.com/632301483303094_122182671764837712\",\n  \"page\": \"Психолог EMDR терапевт Наталья Морозова\"\n}",
  "stderr": ""
}
```

### ok_mode
```json
"mcp_handoff"
```

### ok_mcp_handoff
```json
"/workspace/posts-emdr-memory/output/sb-19-question-before-sleep/ok-mcp-handoff.json"
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
"/workspace/posts-emdr-memory/output/sb-19-question-before-sleep/browser-local-handoff.md"
```

**Deferred (no Undetectable):** telegram, b17, vk_mcp, ok_mcp
