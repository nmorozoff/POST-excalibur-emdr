#!/usr/bin/env python3
"""Grsai Chat API client (OpenAI-compatible /v1/chat/completions)."""

from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any

DEFAULT_BASE = "https://grsaiapi.com"
DEFAULT_MODEL = "gemini-3.1-pro"
# Grsai chat может отвечать >400 с — один запрос, без retry (см. GRSAI_CHAT_TIMEOUT_SEC).
DEFAULT_TIMEOUT_SEC = 900


@dataclass
class ChatResult:
    content: str
    model: str
    usage: dict[str, int]
    raw: dict[str, Any]


def chat_completion(
    *,
    api_key: str,
    messages: list[dict[str, str]],
    base_url: str = DEFAULT_BASE,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7,
    max_tokens: int = 8192,
    timeout_sec: int = DEFAULT_TIMEOUT_SEC,
) -> ChatResult:
    """Call Grsai chat/completions and return assistant text.

    Single blocking request — no retries. Use a long timeout to avoid duplicate
    generations when the server is still working.
    """
    url = f"{base_url.rstrip('/')}/v1/chat/completions"
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    ctx = ssl.create_default_context()
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec, context=ctx) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        err = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"Grsai Chat HTTP {exc.code}: {err}") from exc
    except urllib.error.URLError as exc:
        reason = getattr(exc, "reason", exc)
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            raise SystemExit(
                f"Grsai Chat timeout after {timeout_sec}s — не повторяйте запрос вслепую: "
                "проверьте уже записанные файлы в output/, затем перезапустите без --force "
                f"(пропустит готовые) или --platform для одной площадки. "
                f"Таймаут: GRSAI_CHAT_TIMEOUT_SEC={timeout_sec}."
            ) from exc
        raise SystemExit(f"Grsai Chat network error: {exc}") from exc
    except TimeoutError as exc:
        raise SystemExit(
            f"Grsai Chat timeout after {timeout_sec}s — см. GRSAI_CHAT_TIMEOUT_SEC."
        ) from exc

    if data.get("error"):
        raise SystemExit(f"Grsai Chat error: {json.dumps(data['error'], ensure_ascii=False)}")

    choices = data.get("choices") or []
    if not choices:
        raise SystemExit(f"Grsai Chat: empty choices: {json.dumps(data, ensure_ascii=False)[:800]}")

    message = choices[0].get("message") or {}
    content = (message.get("content") or "").strip()
    if not content:
        raise SystemExit(f"Grsai Chat: empty content: {json.dumps(data, ensure_ascii=False)[:800]}")

    usage_raw = data.get("usage") or {}
    usage = {
        "prompt_tokens": int(usage_raw.get("prompt_tokens") or 0),
        "completion_tokens": int(usage_raw.get("completion_tokens") or 0),
        "total_tokens": int(usage_raw.get("total_tokens") or 0),
    }
    return ChatResult(
        content=content,
        model=str(data.get("model") or model),
        usage=usage,
        raw=data,
    )
