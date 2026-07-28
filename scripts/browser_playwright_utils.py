#!/usr/bin/env python3
"""Shared Playwright launch: storage state, headless, optional proxy."""

from __future__ import annotations

import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import urlparse

from posts_emdr_env import browser_headless, load_env, playwright_storage_state_path


def _browser_env() -> dict[str, str]:
    try:
        return load_env("browser.env.local")
    except SystemExit:
        return {}


def _normalize_proxy_server(server: str) -> str:
    server = server.strip()
    if not server:
        return server
    if "://" not in server:
        return f"http://{server}"
    return server


def _proxy_dict(prefix: str = "") -> dict[str, str] | None:
    """Build Playwright proxy dict from BROWSER_PROXY_* or B17_PROXY_* env."""
    env = _browser_env()
    server = env.get(f"{prefix}PROXY_SERVER", "").strip()
    if not server and prefix:
        server = env.get("BROWSER_PROXY_SERVER", "").strip()
    if not server:
        return None

    proxy: dict[str, str] = {"server": _normalize_proxy_server(server)}
    user = env.get(f"{prefix}PROXY_USERNAME", "").strip() or env.get(
        "BROWSER_PROXY_USERNAME", ""
    ).strip()
    password = env.get(f"{prefix}PROXY_PASSWORD", "").strip() or env.get(
        "BROWSER_PROXY_PASSWORD", ""
    ).strip()
    if user:
        proxy["username"] = user
    if password:
        proxy["password"] = password
    return proxy


def b17_proxy_configured() -> bool:
    return _proxy_dict("B17_") is not None or _proxy_dict("") is not None


def b17_proxy_for_urllib() -> dict[str, str] | None:
    proxy = _proxy_dict("B17_") or _proxy_dict("")
    if not proxy:
        return None
    server = proxy["server"]
    parsed = urlparse(server if "://" in server else f"http://{server}")
    host = parsed.hostname or ""
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    auth = ""
    if proxy.get("username"):
        auth = f"{proxy['username']}:{proxy.get('password', '')}@"
    scheme = parsed.scheme or "http"
    url = f"{scheme}://{auth}{host}:{port}"
    return {"http": url, "https": url}


@contextmanager
def playwright_session(
    *,
    storage_state: Path | None = None,
    headless: bool | None = None,
    proxy_prefix: str = "",
) -> Iterator[tuple[Any, Any, Any]]:
    """Yield (playwright, browser, context). Caller owns pages."""
    from playwright.sync_api import sync_playwright

    state_path = storage_state or playwright_storage_state_path()
    if not state_path.is_file():
        raise SystemExit(
            f"Playwright storage state not found: {state_path}. "
            "Run export-playwright-storage-from-undetectable.py once, then scp to VPS."
        )

    proxy = _proxy_dict(proxy_prefix)
    launch_headless = browser_headless() if headless is None else headless

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=launch_headless, proxy=proxy)
        context = browser.new_context(storage_state=str(state_path))
        try:
            yield pw, browser, context
        finally:
            context.storage_state(path=str(state_path))
            context.close()
            browser.close()
