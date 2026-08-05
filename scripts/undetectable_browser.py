#!/usr/bin/env python3
"""Thin client for Undetectable Browser Local API (shared by publish scripts)."""

from __future__ import annotations

import base64
import json
import os
import subprocess
import tempfile
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_API_BASE = "http://127.0.0.1:25325"


def _api_headers(extra: dict[str, str] | None = None) -> dict[str, str]:
    headers = {"Accept": "application/json"}
    token = os.environ.get("UNDETECTABLE_API_BEARER", "").strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra:
        headers.update(extra)
    return headers

# Заполняет заголовок и текст на странице без ручных CSS-селекторов.
SMART_COMPOSE_FILL_JS = r"""
((title, body) => {
  const visible = (el) => {
    if (!el) return false;
    const st = window.getComputedStyle(el);
    if (st.display === 'none' || st.visibility === 'hidden' || st.opacity === '0') return false;
    const r = el.getBoundingClientRect();
    return r.width > 0 && r.height > 0;
  };

  const pick = (selectors) => {
    for (const s of selectors) {
      const el = document.querySelector(s);
      if (visible(el) && !el.disabled && !el.readOnly) return el;
    }
    return null;
  };

  const titleSelectors = [
    "input[name='title']", "input#title", "input[name='subject']",
    "input[name='name']", "input[placeholder*='аголов' i]",
    "input[placeholder*='заголов' i]", "input[type='text']"
  ];
  const bodySelectors = [
    "textarea[name='text']", "textarea#text", "textarea[name='body']",
    "textarea[name='message']", "textarea[name='content']", "textarea",
    "[contenteditable='true'][role='textbox']", "[contenteditable='true']",
    "[role='textbox']", ".ql-editor", ".ProseMirror", ".tox-edit-area iframe"
  ];

  const setValue = (el, value) => {
    if (!el) return false;
    if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT') {
      el.focus();
      el.value = value;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      el.dispatchEvent(new Event('change', { bubbles: true }));
      return true;
    }
    if (el.isContentEditable) {
      el.focus();
      el.innerText = value;
      el.dispatchEvent(new Event('input', { bubbles: true }));
      return true;
    }
    if (el.tagName === 'IFRAME') {
      try {
        const doc = el.contentDocument || el.contentWindow?.document;
        const editable = doc?.querySelector('[contenteditable="true"], body');
        if (editable) {
          editable.focus();
          editable.innerText = value;
          editable.dispatchEvent(new Event('input', { bubbles: true }));
          return true;
        }
      } catch (_) {}
    }
    return false;
  };

  let titleEl = pick(titleSelectors);
  if (!titleEl) {
    const inputs = [...document.querySelectorAll('input[type="text"], input:not([type])')]
      .filter((el) => visible(el) && !el.disabled && !el.readOnly);
    titleEl = inputs[0] || null;
  }

  let bodyEl = pick(bodySelectors);
  if (!bodyEl) {
    const areas = [...document.querySelectorAll('textarea, [contenteditable="true"]')]
      .filter((el) => visible(el));
    bodyEl = areas[0] || null;
  }

  const result = { ok: false, filled: [], discovered: {} };
  if (titleEl) {
    result.discovered.title = titleEl.tagName.toLowerCase()
      + (titleEl.id ? '#' + titleEl.id : '')
      + (titleEl.name ? `[name="${titleEl.name}"]` : '');
    if (setValue(titleEl, title)) result.filled.push('title');
  }
  if (bodyEl) {
    result.discovered.body = bodyEl.tagName.toLowerCase()
      + (bodyEl.id ? '#' + bodyEl.id : '')
      + (bodyEl.name ? `[name="${bodyEl.name}"]` : '');
    if (setValue(bodyEl, body)) result.filled.push('body');
  }
  result.ok = result.filled.includes('title') && result.filled.includes('body');
  if (!result.ok && result.filled.length === 1 && bodyEl && !titleEl) {
    // TenChat: один contenteditable — весь текст (заголовок + тело)
    const combined = title ? (title + '\n\n' + body) : body;
    if (setValue(bodyEl, combined)) {
      result.filled = ['body_combined'];
      result.ok = true;
    }
  }
  return result;
})
"""


def load_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.exists():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def apply_undetectable_env(env: dict[str, str]) -> None:
    """Push auth token from env file into os.environ for remote VPS API."""
    token = env.get("UNDETECTABLE_API_BEARER", "").strip()
    if token:
        os.environ["UNDETECTABLE_API_BEARER"] = token


def api_request(
    base_url: str,
    method: str,
    path: str,
    payload: dict[str, Any] | None = None,
    *,
    timeout: int = 90,
) -> dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    data = None
    headers = _api_headers({"Content-Type": "application/json"} if payload is not None else None)
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8", errors="replace"))


def ensure_ready(base_url: str) -> None:
    try:
        result = api_request(base_url, "GET", "/status")
    except urllib.error.URLError as exc:
        raise SystemExit(
            "Undetectable Browser API недоступен. Локально: запустите Undetectable. "
            f"VPS/cloud: проверьте UNDETECTABLE_BASE_URL ({base_url}). Ошибка: {exc}"
        ) from exc
    if result.get("code") != 0:
        raise SystemExit(f"Undetectable API not ready: {result}")


def open_url(base_url: str, profile_id: str, url: str) -> None:
    result = api_request(base_url, "POST", f"/browser/openurl/{profile_id}", {"url": url})
    if result.get("code") != 0:
        raise SystemExit(f"openurl failed: {result}")


def get_page_html(base_url: str, profile_id: str) -> str:
    result = api_request(base_url, "GET", f"/browser/getpage/{profile_id}")
    if result.get("code") != 0:
        raise SystemExit(f"getpage failed: {result}")
    page = result.get("data", {}).get("page")
    if not page:
        raise SystemExit("getpage returned empty HTML")
    return page


def fill_field(base_url: str, profile_id: str, selector: str, text: str) -> None:
    result = api_request(
        base_url,
        "POST",
        f"/browser/fill/{profile_id}",
        {"selector": selector, "text": text},
    )
    if result.get("code") != 0:
        raise SystemExit(f"fill failed for {selector}: {result}")


def evaluate_js(base_url: str, profile_id: str, script: str) -> Any:
    result = api_request(
        base_url,
        "POST",
        f"/browser/evaluate/{profile_id}",
        {"script": script},
    )
    if result.get("code") != 0:
        raise SystemExit(f"evaluate failed: {result}")
    return result.get("data")


def paste_into_contenteditable(base_url: str, profile_id: str, selector: str, text: str) -> None:
    escaped = json.dumps(text, ensure_ascii=False)
    script = f"""
(() => {{
  const el = document.querySelector({json.dumps(selector)});
  if (!el) return {{ ok: false, error: 'element not found' }};
  el.focus();
  el.innerText = {escaped};
  el.dispatchEvent(new Event('input', {{ bubbles: true }}));
  return {{ ok: true, chars: {escaped}.length }};
}})()
"""
    data = evaluate_js(base_url, profile_id, script)
    if not data or not data.get("ok"):
        raise SystemExit(f"paste failed: {data}")


def smart_fill_compose(
    base_url: str,
    profile_id: str,
    title: str,
    body: str,
) -> dict[str, Any]:
    title_json = json.dumps(title, ensure_ascii=False)
    body_json = json.dumps(body, ensure_ascii=False)
    script = f"({SMART_COMPOSE_FILL_JS})({title_json}, {body_json})"
    data = evaluate_js(base_url, profile_id, script)
    if not data or not data.get("ok"):
        raise SystemExit(
            "Не удалось автоматически заполнить форму. "
            "Убедитесь, что вы залогинены и открыта страница «новая запись». "
            f"Детали: {data}"
        )
    return data


def selector_is_auto(selector: str | None) -> bool:
    if not selector:
        return True
    return selector.strip().lower() in {"", "auto", "*", "discover"}


def run_js(base_url: str, profile_id: str, script: str, *, timeout: int = 30) -> None:
    """Execute JS in the active tab; API may not return script result."""
    result = api_request(
        base_url,
        "POST",
        f"/browser/evaluate/{profile_id}",
        {"script": script},
        timeout=timeout,
    )
    if result.get("code") != 0:
        raise SystemExit(f"evaluate failed: {result}")


def set_field_value_js(base_url: str, profile_id: str, selector: str, value: str) -> None:
    """Unicode-safe fill (Undetectable /browser/fill ломает кириллицу)."""
    sel = json.dumps(selector, ensure_ascii=False)
    val = json.dumps(value, ensure_ascii=False)
    run_js(
        base_url,
        profile_id,
        f"""(() => {{
  const el = document.querySelector({sel});
  if (!el) throw new Error('Element not found: ' + {sel});
  el.focus();
  if ('value' in el) el.value = {val};
  else el.innerText = {val};
  el.dispatchEvent(new Event('input', {{ bubbles: true }}));
  el.dispatchEvent(new Event('change', {{ bubbles: true }}));
}})();""",
    )


def wait_for_tinymce_and_set(base_url: str, profile_id: str, html_body: str, *, attempts: int = 24) -> None:
    html_json = json.dumps(html_body, ensure_ascii=False)
    for _ in range(attempts):
        run_js(
            base_url,
            profile_id,
            f"""(() => {{
  if (window.tinymce && tinymce.get('tinymce_textarea')) {{
    const ed = tinymce.get('tinymce_textarea');
    ed.setContent({html_json});
    ed.save();
    if (typeof tinymce.triggerSave === 'function') tinymce.triggerSave();
    return true;
  }}
  return false;
}})();""",
            timeout=15,
        )
        time.sleep(0.5)
    run_js(
        base_url,
        profile_id,
        f"""(() => {{
  if (!(window.tinymce && tinymce.get('tinymce_textarea'))) {{
    throw new Error('TinyMCE not ready on b17 edit page');
  }}
  const ed = tinymce.get('tinymce_textarea');
  ed.setContent({html_json});
  ed.save();
  if (typeof tinymce.triggerSave === 'function') tinymce.triggerSave();
}})();""",
    )


def tenchat_click_button_by_text(base_url: str, profile_id: str, text: str, *, exact: bool = False) -> None:
    label = json.dumps(text, ensure_ascii=False)
    exact_js = "true" if exact else "false"
    run_js(
        base_url,
        profile_id,
        f"""(() => {{
  const needle = {label};
  const btn = [...document.querySelectorAll('button')].find((b) => {{
    const t = (b.textContent || '').replace(/\\s+/g, ' ').trim();
    return {exact_js} ? t === needle : t.includes(needle);
  }});
  if (!btn) throw new Error('Button not found: ' + needle);
  btn.click();
}})();""",
    )


def set_tenchat_title_js(base_url: str, profile_id: str, title: str) -> None:
    title_json = json.dumps(title, ensure_ascii=False)
    run_js(
        base_url,
        profile_id,
        f"""(() => {{
  const root = document.querySelector('#tc-editor');
  if (!root) throw new Error('TenChat editor not found');
  const titleEl = [...root.querySelectorAll('[contenteditable="true"]')]
    .find((el) => !el.closest('.ql-container') && !el.closest('.ql-code-block-container'));
  if (!titleEl) throw new Error('TenChat title field not found');
  titleEl.focus();
  titleEl.textContent = {title_json};
  titleEl.dispatchEvent(new InputEvent('input', {{ bubbles: true, data: {title_json} }}));
  titleEl.dispatchEvent(new Event('change', {{ bubbles: true }}));
}})();""",
    )


def strip_urls_from_text(text: str) -> str:
    import re

    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"\s+на сайте:\s*", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def tenchat_markdown_to_html(md: str) -> str:
    import re

    def inline(s: str) -> str:
        s = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2" rel="noopener noreferrer">\1</a>', s)
        s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
        return s

    blocks = [b.strip() for b in md.strip().split("\n\n") if b.strip()]
    parts: list[str] = []
    for block in blocks:
        lines = [ln.strip() for ln in block.split("\n") if ln.strip()]
        if (
            len(lines) >= 2
            and all(re.match(r"^[-—•]\s+", ln) for ln in lines)
        ):
            items = "".join(f"<li>{inline(ln)}</li>" for ln in lines)
            parts.append(f"<ul>{items}</ul>")
        else:
            parts.append(f"<p>{inline(block.replace(chr(10), '<br>'))}</p>")
    return "".join(parts)


def b17_apply_form_meta(
    base_url: str,
    profile_id: str,
    *,
    section_value: str = "1",
    edit_mode: bool = False,
) -> None:
    """Латиница, раздел, авторство. При edit_mode латиницу не трогаем."""
    if not edit_mode:
        run_js(
            base_url,
            profile_id,
            """(() => {
  const lat = document.querySelector('#latname');
  if (lat) { lat.focus(); lat.click(); }
  if (typeof name_to_latname === 'function') name_to_latname();
  else document.querySelector('[onclick*="name_to_latname"]')?.click();
})();""",
        )
        time.sleep(0.8)
    section_json = json.dumps(section_value, ensure_ascii=False)
    run_js(
        base_url,
        profile_id,
        f"""(() => {{
  const sel = document.querySelector('select[name="razdel"]');
  if (!sel) throw new Error('b17 razdel select not found');
  sel.value = {section_json};
  sel.dispatchEvent(new Event('change', {{ bubbles: true }}));
}})();""",
    )
    run_js(
        base_url,
        profile_id,
        """(() => {
  const author = document.querySelector('#not_my0');
  if (!author) throw new Error('b17 author radio not found');
  author.checked = true;
  author.click();
  author.dispatchEvent(new Event('change', { bubbles: true }));
})();""",
    )

B17_COMPOSE_URL_DEFAULT = "https://www.b17.ru/my_blog.php?mod=edit"
B17_TITLE_SELECTOR = "#form_name"
TENCHAT_COMPOSE_URL_DEFAULT = "https://tenchat.ru/editor"


def fill_b17_compose(
    *,
    base_url: str,
    profile_id: str,
    compose_url: str,
    title: str,
    body: str,
    pause_sec: float = 8.0,
    publish_not_draft: bool = True,
    cover_path: Path | None = None,
    auto_submit: bool = False,
    edit_mode: bool = False,
) -> dict[str, Any]:
    ensure_ready(base_url)
    open_url(base_url, profile_id, compose_url)
    time.sleep(pause_sec)
    set_field_value_js(base_url, profile_id, B17_TITLE_SELECTOR, title)
    time.sleep(0.5)
    b17_apply_form_meta(base_url, profile_id, section_value="1", edit_mode=edit_mode)
    html_body = text_to_html_paragraphs(body)
    if cover_path:
        html_body = b17_inline_cover_html(cover_path) + html_body
    wait_for_tinymce_and_set(base_url, profile_id, html_body)
    filled = ["title", "latname", "razdel", "author", "tinymce_body"]
    if cover_path:
        filled.append("cover:https_tinymce")
    if publish_not_draft:
        run_js(
            base_url,
            profile_id,
            "(() => { const cb = document.querySelector('#chernovik'); if (cb) { cb.checked = false; cb.dispatchEvent(new Event('change', {bubbles:true})); } })();",
        )
    submitted = False
    if auto_submit:
        click_button_by_text(base_url, profile_id, "Сохранить")
        submitted = True
    note = (
        "Опубликовано автоматически (Сохранить)"
        if submitted
        else "Проверьте вкладку b17: обложка в тексте заметки. Нажмите «Сохранить изменения»"
    )
    return {
        "status": "published" if submitted else "ready_for_publish",
        "platform": "b17",
        "compose_url": compose_url,
        "filled": filled + (["draft_unchecked"] if publish_not_draft else ["draft_kept"]),
        "fill_mode": "b17-native-js",
        "cover_inline": bool(cover_path),
        "auto_submit": submitted,
        "note": note,
    }


def fill_tenchat_compose(
    *,
    base_url: str,
    profile_id: str,
    compose_url: str,
    title: str,
    body: str,
    topics: list[str] | None = None,
    pause_sec: float = 5.0,
    use_code_block: bool = False,
    cover_path: Path | None = None,
    auto_submit: bool = False,
) -> dict[str, Any]:
    ensure_ready(base_url)
    open_url(base_url, profile_id, compose_url)
    time.sleep(pause_sec)
    filled: list[str] = []
    if use_code_block:
        run_js(
            base_url,
            profile_id,
            "document.querySelector('button.ql-code-block')?.click();",
        )
        time.sleep(0.8)
        body_json = json.dumps(body, ensure_ascii=False)
        run_js(
            base_url,
            profile_id,
            f"""(() => {{
  const pre = document.querySelector('pre.ql-code-block');
  if (!pre) throw new Error('TenChat code block not found');
  pre.textContent = {body_json};
  pre.dispatchEvent(new Event('input', {{ bubbles: true }}));
}})();""",
        )
        filled.extend(["code_mode", "code_body"])
    else:
        html_body = tenchat_markdown_to_html(body)
        set_tenchat_body_html(base_url, profile_id, html_body)
        filled.append("ql_editor_html")
    set_tenchat_title_js(base_url, profile_id, title)
    filled.append("title")
    topic_list = topics or ["Саморазвитие"]
    try:
        added = tenchat_add_topics(base_url, profile_id, topic_list)
        filled.append(f"topics:{','.join(added)}")
    except SystemExit:
        filled.append("topics:failed")
    if cover_path:
        time.sleep(0.5)
        cover_result = tenchat_attach_cover_image(base_url, profile_id, cover_path)
        filled.append(f"cover:{cover_result.get('file')}")
    submitted = False
    if auto_submit:
        click_button_by_text(base_url, profile_id, "Опубликовать")
        submitted = True
    note = (
        "Опубликовано автоматически"
        if submitted
        else "Проверьте вкладку TenChat и нажмите «Опубликовать»"
    )
    return {
        "status": "published" if submitted else "ready_for_publish",
        "platform": "tenchat",
        "compose_url": compose_url,
        "filled": filled,
        "fill_mode": "tenchat-code-block" if use_code_block else "tenchat-html-editor",
        "topics": topic_list,
        "cover_attached": bool(cover_path),
        "auto_submit": submitted,
        "note": note,
    }


def copy_to_clipboard(text: str) -> bool:
    try:
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        return False


def browser_prep_flow(
    *,
    base_url: str,
    profile_id: str,
    compose_url: str,
    title: str,
    body: str,
    title_selector: str | None,
    body_selector: str | None,
    pause_sec: float = 3.0,
    auto_submit: bool = False,
    submit_selector: str | None = None,
    prefer_smart_fill: bool = True,
) -> dict[str, Any]:
    ensure_ready(base_url)
    open_url(base_url, profile_id, compose_url)
    time.sleep(pause_sec)

    filled: list[str] = []
    discovered: dict[str, str] = {}

    use_smart = prefer_smart_fill or (
        selector_is_auto(title_selector) and selector_is_auto(body_selector)
    )

    if use_smart:
        smart = smart_fill_compose(base_url, profile_id, title, body)
        filled.extend(smart.get("filled", []))
        discovered = smart.get("discovered", {})
    else:
        if title_selector and not selector_is_auto(title_selector):
            fill_field(base_url, profile_id, title_selector, title)
            filled.append("title")
        if body_selector and not selector_is_auto(body_selector):
            try:
                fill_field(base_url, profile_id, body_selector, body)
                filled.append("body_input")
            except SystemExit:
                paste_into_contenteditable(base_url, profile_id, body_selector, body)
                filled.append("body_contenteditable")

    submitted = False
    if auto_submit and submit_selector:
        api_request(base_url, "POST", f"/browser/click/{profile_id}", {"selector": submit_selector})
        submitted = True
        time.sleep(pause_sec)

    return {
        "status": "browser_prepared",
        "compose_url": compose_url,
        "filled": filled,
        "discovered_selectors": discovered,
        "fill_mode": "smart" if use_smart else "css",
        "auto_submit": submitted,
        "note": "Проверьте превью в браузере и нажмите «Опубликовать» вручную, если auto_submit=false",
    }
