#!/usr/bin/env python3
"""Playwright backend for b17 + TenChat (Linux VPS, no Undetectable/Windows)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from posts_emdr_env import playwright_storage_state_path
from undetectable_browser import (
    B17_TITLE_SELECTOR,
    b17_apply_form_meta,
    b17_inline_cover_html,
    click_button_by_text,
    prepare_cover_jpeg_for_browser,
    set_field_value_js,
    set_tenchat_body_html,
    set_tenchat_title_js,
    tenchat_add_topics,
    tenchat_markdown_to_html,
    text_to_html_paragraphs,
    wait_for_tinymce_and_set,
)


class _PlaywrightJs:
    def __init__(self, page: Any) -> None:
        self.page = page

    def run_js(self, _base_url: str, _profile_id: str, script: str, *, timeout: int = 30) -> None:
        self.page.set_default_timeout(timeout * 1000)
        self.page.evaluate(script)


def _patch_undetectable_js(page: Any) -> Any:
    import undetectable_browser as ub

    adapter = _PlaywrightJs(page)
    original = ub.run_js
    ub.run_js = adapter.run_js  # type: ignore[method-assign]
    return original


def _restore_undetectable_js(original: Any) -> None:
    import undetectable_browser as ub

    ub.run_js = original  # type: ignore[method-assign]


def _tenchat_attach_cover_playwright(page: Any, cover_path: Path) -> dict[str, Any]:
    if not cover_path.exists():
        raise SystemExit(f"Cover not found: {cover_path}")
    jpeg = prepare_cover_jpeg_for_browser(cover_path)
    page.evaluate(
        """(() => {
  const btn = [...document.querySelectorAll('button')].find(b => b.querySelector('.i-fa6-solid\\:paperclip'));
  if (!btn) throw new Error('TenChat paperclip button not found');
  btn.click();
})();"""
    )
    page.wait_for_selector('input[type="file"]', timeout=8000)
    page.locator('input[type="file"]').first.set_input_files(str(jpeg))
    page.wait_for_timeout(1500)
    page.evaluate(
        """(() => {
  const imgs = [...document.querySelectorAll('#tc-editor img, .ql-editor img, [class*="attachment"] img')];
  if (!imgs.length) throw new Error('TenChat cover image not visible after attach');
})();"""
    )
    return {"ok": True, "file": jpeg.name, "source": str(cover_path), "method": "paperclip_playwright"}


def fill_b17_compose_playwright(
    *,
    storage_state: Path | None = None,
    compose_url: str,
    title: str,
    body: str,
    pause_sec: float = 8.0,
    publish_not_draft: bool = True,
    cover_path: Path | None = None,
    auto_submit: bool = False,
    headless: bool = True,
) -> dict[str, Any]:
    state_path = storage_state or playwright_storage_state_path()
    if not state_path.is_file():
        raise SystemExit(
            f"Playwright storage state not found: {state_path}. "
            "Run: python3 scripts/browser_bootstrap_sessions.py"
        )

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=str(state_path))
        page = context.new_page()
        original = _patch_undetectable_js(page)
        try:
            page.goto(compose_url, wait_until="domcontentloaded", timeout=120_000)
            time.sleep(pause_sec)
            set_field_value_js("", "", B17_TITLE_SELECTOR, title)
            time.sleep(0.5)
            b17_apply_form_meta("", "", section_value="1")
            html_body = text_to_html_paragraphs(body)
            if cover_path:
                html_body = b17_inline_cover_html(cover_path) + html_body
            wait_for_tinymce_and_set("", "", html_body)
            filled = ["title", "latname", "razdel", "author", "tinymce_body"]
            if cover_path:
                filled.append("cover:inline_tinymce")
            if publish_not_draft:
                page.evaluate(
                    """(() => {
  const cb = document.querySelector('#chernovik');
  if (cb) { cb.checked = false; cb.dispatchEvent(new Event('change', {bubbles:true})); }
})();"""
                )
            submitted = False
            if auto_submit:
                click_button_by_text("", "", "Сохранить")
                submitted = True
                time.sleep(3)
            post_url = page.url
            context.storage_state(path=str(state_path))
            return {
                "status": "published" if submitted else "ready_for_publish",
                "platform": "b17",
                "compose_url": compose_url,
                "post_url": post_url,
                "filled": filled + (["draft_unchecked"] if publish_not_draft else ["draft_kept"]),
                "fill_mode": "playwright-b17",
                "cover_inline": bool(cover_path),
                "auto_submit": submitted,
                "backend": "playwright",
                "note": "Опубликовано автоматически (Сохранить)" if submitted else "Проверьте b17",
            }
        finally:
            _restore_undetectable_js(original)
            context.close()
            browser.close()


def fill_tenchat_compose_playwright(
    *,
    storage_state: Path | None = None,
    compose_url: str,
    title: str,
    body: str,
    topics: list[str] | None = None,
    pause_sec: float = 5.0,
    use_code_block: bool = False,
    cover_path: Path | None = None,
    auto_submit: bool = False,
    headless: bool = True,
) -> dict[str, Any]:
    state_path = storage_state or playwright_storage_state_path()
    if not state_path.is_file():
        raise SystemExit(f"Playwright storage state not found: {state_path}")

    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=headless)
        context = browser.new_context(storage_state=str(state_path))
        page = context.new_page()
        original = _patch_undetectable_js(page)
        try:
            page.goto(compose_url, wait_until="domcontentloaded", timeout=120_000)
            time.sleep(pause_sec)
            filled: list[str] = []
            if use_code_block:
                page.evaluate("document.querySelector('button.ql-code-block')?.click();")
                time.sleep(0.8)
                body_json = json.dumps(body, ensure_ascii=False)
                page.evaluate(
                    f"""(() => {{
  const pre = document.querySelector('pre.ql-code-block');
  if (!pre) throw new Error('TenChat code block not found');
  pre.textContent = {body_json};
  pre.dispatchEvent(new Event('input', {{ bubbles: true }}));
}})();"""
                )
                filled.extend(["code_mode", "code_body"])
            else:
                set_tenchat_body_html("", "", tenchat_markdown_to_html(body))
                filled.append("ql_editor_html")
            set_tenchat_title_js("", "", title)
            filled.append("title")
            topic_list = topics or ["Саморазвитие"]
            try:
                added = tenchat_add_topics("", "", topic_list)
                filled.append(f"topics:{','.join(added)}")
            except Exception:
                filled.append("topics:skipped")
            if cover_path:
                time.sleep(0.5)
                cover_result = _tenchat_attach_cover_playwright(page, cover_path)
                filled.append(f"cover:{cover_result.get('file')}")
            submitted = False
            if auto_submit:
                click_button_by_text("", "", "Опубликовать")
                submitted = True
                time.sleep(4)
            post_url = page.url
            context.storage_state(path=str(state_path))
            return {
                "status": "published" if submitted else "ready_for_publish",
                "platform": "tenchat",
                "compose_url": compose_url,
                "post_url": post_url,
                "filled": filled,
                "fill_mode": "playwright-tenchat",
                "topics": topic_list,
                "cover_attached": bool(cover_path),
                "auto_submit": submitted,
                "backend": "playwright",
                "note": "Опубликовано автоматически" if submitted else "Проверьте TenChat",
            }
        finally:
            _restore_undetectable_js(original)
            context.close()
            browser.close()


def playwright_deps_ok() -> bool:
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return True
