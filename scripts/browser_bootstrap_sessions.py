#!/usr/bin/env python3
"""One-time login → save Playwright storage state (b17 + TenChat) on VPS.

TenChat: cookies с Mac дают 500 на VPS — перелогин только через residential proxy.

Linux VPS (окно браузера на Mac через X11 — см. ниже):
  ssh -Y -i ~/Documents/privatekey-1099880.pem ubuntu@195.209.210.45
  cd ~/POST-excalibur-emdr && source .venv-browser/bin/activate
  python3 scripts/browser_bootstrap_sessions.py --headed --tenchat-only --use-proxy

Не используйте xvfb-run, если логините с Mac: окно не появится на экране.

Полный bootstrap (b17 + TenChat):
  xvfb-run -a python3 scripts/browser_bootstrap_sessions.py --headed --use-proxy
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_playwright_utils import b17_proxy_configured, tenchat_proxy_prefix
from posts_emdr_env import playwright_storage_state_path


def _strip_tenchat_cookies(state_path: Path) -> Path:
    data = json.loads(state_path.read_text(encoding="utf-8"))
    data["cookies"] = [c for c in data.get("cookies", []) if "tenchat" not in c.get("domain", "")]
    tmp = state_path.parent / "storage-bootstrap-tmp.json"
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    return tmp


def main() -> None:
    parser = argparse.ArgumentParser(description="Bootstrap Playwright sessions for b17 + TenChat")
    parser.add_argument("--headed", action="store_true", help="Visible browser (xvfb-run on VPS)")
    parser.add_argument("--output", help="Override storage state path")
    parser.add_argument("--tenchat-only", action="store_true", help="Only re-login TenChat (keep b17 cookies)")
    parser.add_argument(
        "--use-proxy",
        action="store_true",
        help="Residential proxy (ASocks) — обязательно для TenChat на VPS",
    )
    parser.add_argument(
        "--cdp-port",
        type=int,
        default=0,
        help="Chrome remote debugging port (9222) + SSH -L для просмотра без X11",
    )
    args = parser.parse_args()

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("pip install playwright && playwright install chromium") from exc

    out = Path(args.output) if args.output else playwright_storage_state_path()
    out.parent.mkdir(parents=True, exist_ok=True)

    if args.use_proxy and not b17_proxy_configured():
        raise SystemExit("Set B17_PROXY_* in browser.env.local (ASocks) before --use-proxy")

    proxy_prefix = tenchat_proxy_prefix() if args.use_proxy else ""
    if args.use_proxy and not proxy_prefix:
        raise SystemExit("No residential proxy configured")

    from browser_playwright_utils import _proxy_dict

    proxy = _proxy_dict(proxy_prefix) if proxy_prefix else None
    storage_for_ctx = None
    if out.is_file():
        storage_for_ctx = str(_strip_tenchat_cookies(out) if args.tenchat_only else out)

    if args.tenchat_only:
        steps = [("https://tenchat.ru/auth/sign-in", "TenChat — войдите (SMS на телефон)")]
    else:
        steps = [
            ("https://www.b17.ru/login.php", "b17.ru — войдите в аккаунт"),
            ("https://tenchat.ru/auth/sign-in", "TenChat — войдите (SMS на телефон)"),
        ]

    launch_args = ["--disable-blink-features=AutomationControlled"]
    if args.cdp_port:
        launch_args.append(f"--remote-debugging-port={args.cdp_port}")

    display = os.environ.get("DISPLAY", "")
    if args.headed and display.startswith(":") and display[1:].isdigit():
        print(
            "\n⚠ Сейчас DISPLAY="
            + display
            + " — это виртуальный экран (xvfb). Окно браузера на Mac НЕ появится.\n"
            "  Нажмите Ctrl+C, выйдите и подключитесь так:\n"
            "    ssh -Y -i ~/Documents/privatekey-1099880.pem ubuntu@195.209.210.45\n"
            "  Затем снова запустите команду БЕЗ xvfb-run.\n"
        )

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=not args.headed,
            proxy=proxy,
            args=launch_args,
        )
        context = browser.new_context(
            storage_state=storage_for_ctx,
            locale="ru-RU",
        )
        page = context.new_page()
        for url, prompt in steps:
            print(f"\n→ {prompt}\n  URL: {url}\n")
            page.goto(url, wait_until="domcontentloaded", timeout=120_000)
            if args.cdp_port:
                print(
                    f"  CDP: на Mac во 2-м терминале:\n"
                    f"    ssh -i ~/Documents/privatekey-1099880.pem "
                    f"-L {args.cdp_port}:127.0.0.1:{args.cdp_port} ubuntu@195.209.210.45\n"
                    f"  Затем в Chrome: http://127.0.0.1:{args.cdp_port}/json/list\n"
                )
            print(
                "В окне браузера (на Mac): введите телефон → SMS-код с телефона → войдите.\n"
                "Когда увидите ленту TenChat / личный кабинет — вернитесь в этот терминал.\n"
            )
            input("Когда залогинены, нажмите Enter… ")
        context.storage_state(path=str(out))
        browser.close()

    tmp = out.parent / "storage-bootstrap-tmp.json"
    if tmp.is_file():
        tmp.unlink()
    print(f"\n✓ Storage state saved: {out}")
    print("Проверка: python3 scripts/check-tenchat-access.py && python3 scripts/check-b17-ip-access.py")


if __name__ == "__main__":
    main()
