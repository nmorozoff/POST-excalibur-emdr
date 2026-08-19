"""Shared helpers for probing the VPS posts-emdr webhook from Cloud."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Any


def classify_probe_error(exc: BaseException) -> dict[str, Any]:
    msg = str(exc)
    lowered = msg.lower()
    if "connection reset" in lowered or "errno 104" in lowered:
        return {
            "error": msg[:500],
            "vps_down": True,
            "kind": "connection_reset",
            "hint": (
                "TCP к 8787 есть, но HTTP обрывается — webhook на VPS не отвечает. "
                "SSH на VPS: systemctl status posts-emdr-webhook; "
                "systemctl restart posts-emdr-webhook; curl -fsS localhost:8787/health. "
                "См. posts-emdr-memory/profile/browser-autonomous-vps.md (§ Webhook недоступен)"
            ),
        }
    if "timed out" in lowered or "timeout" in lowered:
        return {
            "error": msg[:500],
            "vps_down": False,
            "kind": "timeout",
            "hint": "Повторить через 10–15 мин или проверить нагрузку VPS.",
        }
    if "connection refused" in lowered or "errno 111" in lowered:
        return {
            "error": msg[:500],
            "vps_down": True,
            "kind": "connection_refused",
            "hint": "Порт 8787 не слушает — запустить posts-emdr-webhook (systemd).",
        }
    return {"error": msg[:500], "vps_down": False, "kind": "unknown"}


def probe_health(host: str, port: int, *, timeout: float = 10.0) -> tuple[bool, dict[str, Any]]:
    url = f"http://{host}:{port}/health"
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
            data = json.loads(text) if text else {}
            ok = resp.status == 200 and bool(data.get("ok"))
            return ok, {"status": resp.status, **data}
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(text) if text else {}
        except json.JSONDecodeError:
            data = {"raw": text[:200]}
        return False, {"status": e.code, **data}
    except Exception as e:
        return False, classify_probe_error(e)


def post_json(
    url: str,
    secret: str,
    payload: dict[str, Any],
    *,
    timeout: float = 90.0,
) -> tuple[int, dict[str, Any]]:
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {secret}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            text = resp.read().decode("utf-8")
            data = json.loads(text) if text else {}
            return resp.status, data
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(text) if text else {}
        except json.JSONDecodeError:
            data = {"raw": text[:200]}
        return e.code, data
    except Exception as e:
        return 0, classify_probe_error(e)
