# Publish log — sb-13-no-repot-in-storm

**Date:** 2026-08-10
**Status:** published_scripts_partial

## Steps

### cover
```json
{
  "status": "generated",
  "path": "/workspace/posts-emdr-memory/output/sb-13-no-repot-in-storm/cover.png",
  "backend": "grsai-cover",
  "detail": {
    "status": "ok",
    "output": "/workspace/posts-emdr-memory/output/sb-13-no-repot-in-storm/cover.png",
    "imageURL": "https://file1.aitohumanize.com/file/b94fa37382374c6f97e89fe4292c3200.png",
    "model": "gpt-image-2",
    "backend": "grsai",
    "reference_rotation": {
      "topic": "sb-13-no-repot-in-storm",
      "slot": 5,
      "reference_path": "/workspace/posts-emdr-memory/assets/reference/portrait-05.jpg",
      "backend": "grsai",
      "aspect_ratio": "1280x1024",
      "quality": "low",
      "model": "gpt-image-2"
    }
  }
}
```

### max
```json
{
  "status": "sent",
  "mode": "publish",
  "chat_id": "[REDACTED]",
  "log": "/workspace/posts-emdr-memory/output/sb-13-no-repot-in-storm/max-publish-log.json"
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
  "topic": "sb-13-no-repot-in-storm",
  "profile_chars": 4646,
  "group_chars": 4618,
  "cover_local": "/workspace/posts-emdr-memory/output/sb-13-no-repot-in-storm/cover.png",
  "cover_jpeg_bytes": 73050,
  "cover_public_url": "https://morozovanatalia.ru/social-covers/sb-13-no-repot-in-storm.jpg",
  "cover_http_status": 200,
  "cover_serves_image": true,
  "cover_upload_method": "ftplib_pasv"
}
```

### vk_mode
```json
"mcp_handoff"
```

### vk_mcp_handoff
```json
"/workspace/posts-emdr-memory/output/sb-13-no-repot-in-storm/vk-mcp-handoff.json"
```

### facebook
```json
{
  "stdout": "{\n  \"topic\": \"sb-13-no-repot-in-storm\",\n  \"profile_chars\": 4646,\n  \"group_chars\": 4618,\n  \"cover_local\": \"/workspace/posts-emdr-memory/output/sb-13-no-repot-in-storm/cover.png\",\n  \"deleted_remote_files\": [\n    \"sb-13-no-repot-in-storm.jpg\",\n    \"sb-13-no-repot-in-storm-v2.jpg\"\n  ]\n}\n{\n  \"topic\": \"sb-13-no-repot-in-storm\",\n  \"platform\": \"facebook\",\n  \"chars\": 4724,\n  \"cover_url\": \"https://morozovanatalia.ru/wp-content/uploads/2026/08/sb-13-no-repot-in-storm.jpg\",\n  \"dry_run\": false,\n  \"zernio_post_id\": \"6a79a74fae3bc2d9e495804b\",\n  \"status\": \"published\",\n  \"platform_post_id\": \"632301483303094_122181733574837712\",\n  \"platform_post_url\": \"https://www.facebook.com/632301483303094_122181733574837712\",\n  \"page\": \"Психолог EMDR терапевт Наталья Морозова\"\n}",
  "stderr": ""
}
```

### ok_mode
```json
"mcp_handoff"
```

### ok_mcp_handoff
```json
"/workspace/posts-emdr-memory/output/sb-13-no-repot-in-storm/ok-mcp-handoff.json"
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
"/workspace/posts-emdr-memory/output/sb-13-no-repot-in-storm/browser-local-handoff.md"
```

**Deferred (no Undetectable):** telegram, b17, vk_mcp, ok_mcp
