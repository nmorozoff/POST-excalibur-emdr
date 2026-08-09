# Publish log — sb-12-stray-cat-trust

**Date:** 2026-08-09
**Status:** published_scripts_partial

## Steps

### cover
```json
{
  "status": "generated",
  "path": "/workspace/posts-emdr-memory/output/sb-12-stray-cat-trust/cover.png",
  "backend": "grsai-cover",
  "detail": {
    "status": "ok",
    "output": "/workspace/posts-emdr-memory/output/sb-12-stray-cat-trust/cover.png",
    "imageURL": "https://file1.aitohumanize.com/file/ea573a7381e94256ae44ce9ae1798b2e.png",
    "model": "gpt-image-2",
    "backend": "grsai",
    "reference_rotation": {
      "topic": "sb-12-stray-cat-trust",
      "slot": 4,
      "reference_path": "/workspace/posts-emdr-memory/assets/reference/portrait-04.jpg",
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
  "chat_id": "[REDACTED]"
  "log": "/workspace/posts-emdr-memory/output/sb-12-stray-cat-trust/max-publish-log.json"
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
  "topic": "sb-12-stray-cat-trust",
  "profile_chars": 4892,
  "group_chars": 4951,
  "cover_local": "/workspace/posts-emdr-memory/output/sb-12-stray-cat-trust/cover.png",
  "cover_jpeg_bytes": 71269,
  "cover_public_url": "https://morozovanatalia.ru/social-covers/sb-12-stray-cat-trust.jpg",
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
"/workspace/posts-emdr-memory/output/sb-12-stray-cat-trust/vk-mcp-handoff.json"
```

### facebook
```json
{
  "stdout": "{\n  \"topic\": \"sb-12-stray-cat-trust\",\n  \"profile_chars\": 4892,\n  \"group_chars\": 4951,\n  \"cover_local\": \"/workspace/posts-emdr-memory/output/sb-12-stray-cat-trust/cover.png\",\n  \"deleted_remote_files\": [\n    \"sb-12-stray-cat-trust.jpg\",\n    \"sb-12-stray-cat-trust-v2.jpg\"\n  ]\n}\n{\n  \"topic\": \"sb-12-stray-cat-trust\",\n  \"platform\": \"facebook\",\n  \"chars\": 5392,\n  \"cover_url\": \"https://morozovanatalia.ru/social-covers/sb-12-stray-cat-trust.jpg\",\n  \"dry_run\": false,\n  \"zernio_post_id\": \"6a78611749b36dffca8b0af3\",\n  \"status\": \"published\",\n  \"platform_post_id\": \"632301483303094_122181625424837712\",\n  \"platform_post_url\": \"https://www.facebook.com/632301483303094_122181625424837712\",\n  \"page\": \"Психолог EMDR терапевт Наталья Морозова\"\n}",
  "stderr": ""
}
```

### ok_mode
```json
"mcp_handoff"
```

### ok_mcp_handoff
```json
"/workspace/posts-emdr-memory/output/sb-12-stray-cat-trust/ok-mcp-handoff.json"
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
"/workspace/posts-emdr-memory/output/sb-12-stray-cat-trust/browser-local-handoff.md"
```

**Deferred (no Undetectable):** telegram, b17, vk_mcp, ok_mcp
