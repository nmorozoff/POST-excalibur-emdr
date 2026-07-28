#!/usr/bin/env python3
"""Unified browser backend: undetectable (Mac) or playwright (Linux VPS)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from posts_emdr_env import (
    browser_headless,
    browser_backend_name,
    playwright_storage_state_path,
    undetectable_config,
    undetectable_reachable,
)
from undetectable_browser import (
    B17_COMPOSE_URL_DEFAULT,
    TENCHAT_COMPOSE_URL_DEFAULT,
    fill_b17_compose,
    fill_tenchat_compose,
)


def browser_ready() -> bool:
    if browser_backend_name() == "playwright":
        return playwright_deps_ok() and playwright_storage_state_path().is_file()
    return undetectable_reachable()


def playwright_deps_ok() -> bool:
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return True


def browser_health() -> dict[str, Any]:
    backend = browser_backend_name()
    if backend == "playwright":
        state = playwright_storage_state_path()
        return {
            "ok": playwright_deps_ok() and state.is_file(),
            "backend": "playwright",
            "storage_state": str(state),
            "storage_exists": state.is_file(),
            "headless": browser_headless(),
            "playwright_installed": playwright_deps_ok(),
        }
    cfg = undetectable_config()
    return {
        "ok": undetectable_reachable(),
        "backend": "undetectable",
        "base_url": cfg["base_url"],
        "profile_id_set": bool(cfg.get("profile_id")),
        "bearer_set": bool(cfg.get("bearer")),
    }


def publish_b17(
    *,
    env: dict[str, str],
    compose_url: str,
    title: str,
    body: str,
    cover_path: Path | None,
    auto_submit: bool,
) -> dict[str, Any]:
    if browser_backend_name() == "playwright":
        from playwright_browser import fill_b17_compose_playwright

        return fill_b17_compose_playwright(
            compose_url=compose_url,
            title=title,
            body=body,
            cover_path=cover_path,
            auto_submit=auto_submit,
            headless=browser_headless(),
        )
    profile_id = env.get("UNDETECTABLE_PROFILE_ID", "")
    if not profile_id:
        raise SystemExit("Set UNDETECTABLE_PROFILE_ID or BROWSER_BACKEND=playwright")
    return fill_b17_compose(
        base_url=env.get("UNDETECTABLE_BASE_URL", "http://127.0.0.1:25325"),
        profile_id=profile_id,
        compose_url=compose_url,
        title=title,
        body=body,
        cover_path=cover_path,
        auto_submit=auto_submit,
    )


def publish_tenchat(
    *,
    env: dict[str, str],
    compose_url: str,
    title: str,
    body: str,
    topics: list[str],
    use_code_block: bool,
    cover_path: Path | None,
    auto_submit: bool,
) -> dict[str, Any]:
    if browser_backend_name() == "playwright":
        from playwright_browser import fill_tenchat_compose_playwright

        return fill_tenchat_compose_playwright(
            compose_url=compose_url,
            title=title,
            body=body,
            topics=topics,
            use_code_block=use_code_block,
            cover_path=cover_path,
            auto_submit=auto_submit,
            headless=browser_headless(),
        )
    profile_id = env.get("UNDETECTABLE_PROFILE_ID", "")
    if not profile_id:
        raise SystemExit("Set UNDETECTABLE_PROFILE_ID or BROWSER_BACKEND=playwright")
    return fill_tenchat_compose(
        base_url=env.get("UNDETECTABLE_BASE_URL", "http://127.0.0.1:25325"),
        profile_id=profile_id,
        compose_url=compose_url,
        title=title,
        body=body,
        topics=topics,
        use_code_block=use_code_block,
        cover_path=cover_path,
        auto_submit=auto_submit,
    )


def default_b17_compose_url(env: dict[str, str]) -> str:
    return env.get("B17_COMPOSE_URL", B17_COMPOSE_URL_DEFAULT)


def default_tenchat_compose_url(env: dict[str, str]) -> str:
    return env.get("TENCHAT_COMPOSE_URL", TENCHAT_COMPOSE_URL_DEFAULT)
