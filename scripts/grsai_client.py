#!/usr/bin/env python3
"""Grsai GPT Image API client (gpt-image-2)."""

from __future__ import annotations

import json
import ssl
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE = "https://grsaiapi.com"
POLL_INTERVAL_SEC = 4
POLL_TIMEOUT_SEC = 600


def _request(
    base_url: str,
    api_key: str,
    path: str,
    payload: dict[str, Any],
    *,
    stream: bool = False,
) -> Any:
    url = f"{base_url.rstrip('/')}{path}"
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    if stream:
        return urllib.request.urlopen(req, timeout=120, context=ctx)
    try:
        with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Grsai API HTTP {exc.code}: {err}") from exc


def _parse_stream_line(line: str) -> dict[str, Any] | None:
    line = line.strip()
    if not line:
        return None
    if line.startswith("data:"):
        line = line[5:].strip()
    if line in {"[DONE]", "DONE"}:
        return None
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


def _extract_url(payload: dict[str, Any]) -> str | None:
    if payload.get("url"):
        return str(payload["url"]).strip()
    results = payload.get("results") or []
    if results and isinstance(results[0], dict) and results[0].get("url"):
        return str(results[0]["url"]).strip()
    data = payload.get("data")
    if isinstance(data, dict):
        return _extract_url(data)
    return None


def _poll_result(base_url: str, api_key: str, task_id: str) -> dict[str, Any]:
    deadline = time.time() + POLL_TIMEOUT_SEC
    last: dict[str, Any] = {}
    while time.time() < deadline:
        resp = _request(
            base_url,
            api_key,
            "/v1/draw/result",
            {"id": task_id},
            stream=False,
        )
        if resp.get("code") == -22:
            time.sleep(POLL_INTERVAL_SEC)
            continue
        if resp.get("code") not in (0, None):
            raise SystemExit(f"Grsai result error: {json.dumps(resp, ensure_ascii=False)[:800]}")
        data = resp.get("data") or resp
        last = data if isinstance(data, dict) else {"raw": data}
        status = (last.get("status") or "").lower()
        if status == "succeeded":
            return last
        if status == "failed":
            raise SystemExit(
                f"Grsai task failed: {last.get('failure_reason') or last.get('error') or last}"
            )
        time.sleep(POLL_INTERVAL_SEC)
    raise SystemExit(f"Grsai poll timeout ({POLL_TIMEOUT_SEC}s), last={json.dumps(last)[:400]}")


def generate_image(
    *,
    api_key: str,
    prompt: str,
    base_url: str = DEFAULT_BASE,
    model: str = "gpt-image-2",
    aspect_ratio: str = "1280x1024",
    quality: str = "low",
    reference_urls: list[str] | None = None,
    use_poll: bool = True,
) -> dict[str, Any]:
    """Return dict with task_id, image_url, raw final payload."""
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "aspectRatio": aspect_ratio,
        "quality": quality,
        "shutProgress": True,
    }
    if reference_urls:
        payload["urls"] = reference_urls

    if use_poll:
        payload["webHook"] = "-1"
        created = _request(base_url, api_key, "/v1/draw/completions", payload, stream=False)
        if created.get("code") not in (0, None):
            raise SystemExit(f"Grsai create error: {json.dumps(created, ensure_ascii=False)[:800]}")
        data = created.get("data") or {}
        task_id = data.get("id") or created.get("id")
        if not task_id:
            raise SystemExit(f"Grsai: no task id in response: {json.dumps(created)[:500]}")
        final = _poll_result(base_url, api_key, str(task_id))
        url = _extract_url(final)
        if not url:
            raise SystemExit(f"Grsai: no image url in result: {json.dumps(final)[:500]}")
        return {"task_id": task_id, "image_url": url, "raw": final}

    # Stream mode
    resp = _request(base_url, api_key, "/v1/draw/completions", payload, stream=True)
    task_id = ""
    final: dict[str, Any] = {}
    try:
        for raw_line in resp:
            line = raw_line.decode("utf-8", errors="replace")
            for part in line.split("\n"):
                parsed = _parse_stream_line(part)
                if not parsed:
                    continue
                if parsed.get("id"):
                    task_id = str(parsed["id"])
                final = parsed
                status = (parsed.get("status") or "").lower()
                if status == "failed":
                    raise SystemExit(
                        f"Grsai stream failed: {parsed.get('failure_reason') or parsed.get('error')}"
                    )
                if status == "succeeded" or _extract_url(parsed):
                    url = _extract_url(parsed)
                    if url:
                        return {"task_id": task_id, "image_url": url, "raw": parsed}
    finally:
        resp.close()

    url = _extract_url(final)
    if url:
        return {"task_id": task_id, "image_url": url, "raw": final}
    raise SystemExit(f"Grsai stream ended without image: {json.dumps(final)[:500]}")


def download_image(url: str, dest: Path) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "posts-emdr-grsai/1.0"})
    ctx = ssl.create_default_context()
    with urllib.request.urlopen(req, timeout=180, context=ctx) as resp:
        data = resp.read()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
