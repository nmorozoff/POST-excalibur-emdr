#!/usr/bin/env python3
"""Playwright backend for b17 + TenChat (Linux VPS, no Undetectable/Windows)."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

from browser_playwright_utils import playwright_session, tenchat_proxy_prefix
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


def _b17_page_ready(page: Any) -> bool:
    html = page.content().lower()
    return "b17_guard" not in html and "временно заблокирован" not in html and (
        page.query_selector(B17_TITLE_SELECTOR) is not None or "tinymce" in html
    )


def _tenchat_attach_cover_playwright(page: Any, cover_path: Path) -> dict[str, Any]:
    if not cover_path.exists():
        raise SystemExit(f"Cover not found: {cover_path}")
    jpeg = prepare_cover_jpeg_for_browser(cover_path)
    with page.expect_file_chooser(timeout=20_000) as fc_info:
        page.evaluate(
            """(() => {
  const btn = [...document.querySelectorAll('button')].find((b) => {
    const icon = b.querySelector('[class*="paperclip"]');
    return Boolean(icon);
  });
  if (!btn) throw new Error('TenChat paperclip button not found');
  btn.click();
})();"""
        )
    file_chooser = fc_info.value
    file_chooser.set_files(str(jpeg))
    page.wait_for_timeout(4000)
    try:
        page.wait_for_function(
            """() => {
  const imgs = [...document.querySelectorAll('#tc-editor img, .ql-editor img, [class*="attachment"] img')];
  return imgs.length > 0;
}""",
            timeout=20_000,
        )
    except Exception:
        # Обложка могла прикрепиться без img в DOM — не блокируем публикацию
        pass
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
    edit_mode: bool = False,
) -> dict[str, Any]:
    state_path = storage_state or playwright_storage_state_path()
    with playwright_session(storage_state=state_path, headless=headless, proxy_prefix="B17_") as (
        _pw,
        _browser,
        context,
    ):
        page = context.new_page()
        original = _patch_undetectable_js(page)
        try:
            page.goto(compose_url, wait_until="domcontentloaded", timeout=120_000)
            time.sleep(pause_sec)
            if not _b17_page_ready(page):
                raise SystemExit(
                    "b17 compose not ready (IP block or session expired). "
                    "Set B17_PROXY_SERVER in browser.env.local or refresh storage state."
                )
            b17_cover_url: str | None = None
            filled_extra: list[str] = []
            if cover_path:
                from undetectable_browser import prepare_cover_jpeg_for_browser

                # Загрузка обложки в b17 и захват её URL для вставки в тело поста
                try:
                    jpeg_path = prepare_cover_jpeg_for_browser(cover_path)
                    page.set_input_files("#input_file", str(jpeg_path))
                    page.wait_for_timeout(3000)
                    # Принудительно диспатчим change, чтобы JS b17 начал загрузку
                    page.evaluate(
                        """(() => {
      const inp = document.querySelector('#input_file');
      if (inp) { inp.dispatchEvent(new Event('change', { bubbles: true })); }
    })();"""
                    )
                    page.wait_for_timeout(5000)
                    # Ждём появления загруженного изображения на b17 и читаем его URL
                    for _ in range(60):
                        try:
                            # 1. Превью-изображение, которое b17 показывает после загрузки
                            img = page.query_selector("img[src*='foto/uploaded/']")
                            if img:
                                src = img.get_attribute("src")
                                if src and src.startswith("https://www.b17.ru/foto/uploaded/"):
                                    b17_cover_url = src
                                    break
                            # 2. Скрытое поле с ID загруженной фотографии
                            hidden = page.query_selector('input[type="hidden"][name*="foto"]')
                            if hidden:
                                val = hidden.get_attribute("value")
                                if val and val.startswith("upl_"):
                                    b17_cover_url = f"https://www.b17.ru/foto/uploaded/{val}.jpg"
                                    break
                        except Exception:
                            pass
                        time.sleep(1)
                    if b17_cover_url:
                        filled_extra.append("cover:announcement_image_with_b17_url")
                    else:
                        raise SystemExit(
                            "b17 cover uploaded but b17-hosted URL not found in page. "
                            "Cannot build inline image without b17 URL."
                        )
                except Exception as exc:
                    filled_extra.append(f"cover:announcement_image_failed:{exc}")

            set_field_value_js("", "", B17_TITLE_SELECTOR, title)
            time.sleep(0.5)
            b17_apply_form_meta("", "", section_value="1", edit_mode=edit_mode)
            html_body = text_to_html_paragraphs(body)
            cover_src = None
            if cover_path:
                if b17_cover_url:
                    cover_src = b17_cover_url
                    html_body = b17_inline_cover_html(cover_path, public_url=b17_cover_url) + html_body
                else:
                    from undetectable_browser import b17_cover_public_url

                    cover_src = b17_cover_public_url(cover_path)
                    html_body = b17_inline_cover_html(cover_path, public_url=cover_src) + html_body
                filled_extra.append("cover:https_tinymce")
            wait_for_tinymce_and_set("", "", html_body)
            filled = ["title", "latname", "razdel", "author", "tinymce_body"] + filled_extra
            if publish_not_draft:
                page.evaluate(
                    """(() => {
  const cb = document.querySelector('#chernovik');
  if (cb) { cb.checked = false; cb.dispatchEvent(new Event('change', {bubbles:true})); }
})();"""
                )
            submitted = False
            post_url = page.url
            public_link = None
            if auto_submit:
                page.evaluate(
                    """() => {
  const ed = window.tinymce && tinymce.get('tinymce_textarea');
  if (ed) { ed.save(); if (typeof tinymce.triggerSave === 'function') tinymce.triggerSave(); }
}"""
                )
                click_button_by_text("", "", "Сохранить")
                try:
                    page.wait_for_load_state("domcontentloaded", timeout=60_000)
                except Exception:
                    pass
                time.sleep(4)
                body_text = page.inner_text("body")
                if "ошибка" in body_text.lower() and "сохран" in body_text.lower():
                    raise SystemExit(f"b17 save error: {body_text[:500]}")
                # Verify in publications list
                page.goto("https://www.b17.ru/my.php?mod=blog", wait_until="domcontentloaded", timeout=120_000)
                time.sleep(3)
                list_text = page.inner_text("body")
                if title not in list_text:
                    raise SystemExit(
                        "b17 auto-submit clicked but title not in my.php?mod=blog — "
                        "not marking as published"
                    )
                links = page.eval_on_selector_all(
                    "a[href*='/blog/']",
                    "els => els.map(e => ({href: e.href, text: (e.innerText||'').trim()}))",
                )
                for item in links:
                    if title[:24] in (item.get("text") or "") or title in (item.get("text") or ""):
                        public_link = item.get("href")
                        break
                post_url = public_link or page.url
                submitted = True
            return {
                "status": "published" if submitted else "ready_for_publish",
                "platform": "b17",
                "compose_url": compose_url,
                "post_url": post_url,
                "public_url": public_link,
                "cover_url": cover_src,
                "filled": filled + (["draft_unchecked"] if publish_not_draft else ["draft_kept"]),
                "fill_mode": "playwright-b17",
                "cover_inline": bool(cover_path),
                "auto_submit": submitted,
                "backend": "playwright",
                "note": "Опубликовано автоматически (Сохранить)" if submitted else "Проверьте b17",
            }
        finally:
            _restore_undetectable_js(original)


def fill_tenchat_compose_playwright(
    *,
    storage_state: Path | None = None,
    compose_url: str,
    title: str,
    body: str,
    topics: list[str] | None = None,
    pause_sec: float = 10.0,
    use_code_block: bool = False,
    cover_path: Path | None = None,
    auto_submit: bool = False,
    headless: bool = True,
) -> dict[str, Any]:
    state_path = storage_state or playwright_storage_state_path()
    proxy_px = tenchat_proxy_prefix()
    with playwright_session(
        storage_state=state_path, headless=headless, proxy_prefix=proxy_px
    ) as (
        _pw,
        _browser,
        context,
    ):
        page = context.new_page()
        original = _patch_undetectable_js(page)
        try:
            page.goto(compose_url, wait_until="networkidle", timeout=120_000)
            time.sleep(pause_sec)
            if "auth/sign-in" in page.url.lower():
                raise SystemExit(
                    "TenChat session expired (SMS login required). "
                    "Re-export storage state from Undetectable once, then scp to VPS."
                )
            page_html = page.content().lower()
            if "ошибка сервера" in page_html and "500" in page_html:
                raise SystemExit(
                    "TenChat editor: 500 Ошибка сервера (часто на VPS/datacenter IP). "
                    "Опубликуйте TenChat с Mac через Undetectable: "
                    "BROWSER_BACKEND=undetectable python3 scripts/publish-tenchat-post.py --topic ... --submit"
                )
            # SPA: дождаться редактора (VPS headless часто медленнее Mac)
            editor_selectors = [
                "#tc-editor .ql-editor",
                "#tc-editor [contenteditable='true']",
                ".ql-editor",
            ]
            editor_found = False
            for sel in editor_selectors:
                try:
                    page.wait_for_selector(sel, timeout=25_000, state="visible")
                    editor_found = True
                    break
                except Exception:
                    continue
            if not editor_found and not use_code_block:
                # fallback: code block mode если HTML-редактор не поднялся
                use_code_block = True
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
                page.wait_for_selector('input[placeholder*="тематик"]', timeout=8000)
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


def playwright_deps_ok() -> bool:
    try:
        import playwright  # noqa: F401
    except ImportError:
        return False
    return True
