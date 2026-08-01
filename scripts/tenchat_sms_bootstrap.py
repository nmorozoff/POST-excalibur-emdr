#!/usr/bin/env python3
"""TenChat SMS login on VPS — телефон из файла, код из файла или stdin.

Файлы (gitignored):
  posts-emdr-memory/tenchat-bootstrap.env.local  → TENCHAT_PHONE=9123456789
  posts-emdr-memory/tenchat-sms-code.local       → одна строка: 123456

Капча Yandex: один раз кликнуть в окне VNC (scripts/tenchat-vnc-login.sh).

  python3 scripts/tenchat_sms_bootstrap.py --use-proxy
  python3 scripts/tenchat_sms_bootstrap.py --use-proxy --phone 9123456789 --code 123456
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from browser_playwright_utils import b17_proxy_configured, tenchat_proxy_prefix, _proxy_dict
from posts_emdr_env import MEMORY, playwright_storage_state_path

BOOTSTRAP_ENV = MEMORY / "tenchat-bootstrap.env.local"
CODE_FILE = MEMORY / "tenchat-sms-code.local"
SIGN_IN = "https://tenchat.ru/auth/sign-in"


def _parse_env_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.is_file():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        data[k.strip()] = v.strip().strip('"').strip("'")
    return data


def normalize_phone(raw: str) -> str:
    digits = re.sub(r"\D", "", raw)
    if digits.startswith("8") and len(digits) == 11:
        digits = "7" + digits[1:]
    if digits.startswith("7") and len(digits) == 11:
        digits = digits[1:]
    if len(digits) != 10:
        raise SystemExit(f"Нужен российский номер 10 цифр, получено: {raw!r}")
    return digits


def load_phone(cli_phone: str | None) -> str:
    if cli_phone:
        return normalize_phone(cli_phone)
    env = _parse_env_file(BOOTSTRAP_ENV)
    raw = env.get("TENCHAT_PHONE", "").strip() or os.environ.get("TENCHAT_PHONE", "").strip()
    if not raw:
        raise SystemExit(
            f"Укажите --phone или создайте {BOOTSTRAP_ENV} с TENCHAT_PHONE=9123456789"
        )
    return normalize_phone(raw)


def wait_for_code(cli_code: str | None, timeout_sec: int) -> str:
    if cli_code:
        return re.sub(r"\D", "", cli_code)
    deadline = time.time() + timeout_sec
    print(f"\n→ SMS: создайте файл {CODE_FILE} с кодом (одна строка)")
    print("  или введите код здесь и Enter.\n")
    while time.time() < deadline:
        if CODE_FILE.is_file():
            code = re.sub(r"\D", "", CODE_FILE.read_text(encoding="utf-8").strip())
            if len(code) >= 4:
                CODE_FILE.unlink(missing_ok=True)
                return code
        try:
            import select

            if select.select([sys.stdin], [], [], 2)[0]:
                line = sys.stdin.readline().strip()
                code = re.sub(r"\D", "", line)
                if len(code) >= 4:
                    return code
        except Exception:
            time.sleep(2)
    raise SystemExit("Таймаут ожидания SMS-кода")


def check_checkboxes(page) -> None:
    for cb in page.locator("input[type=checkbox]").all():
        try:
            if not cb.is_checked():
                cb.check(force=True)
        except Exception:
            pass


def fill_phone(page, phone: str) -> None:
    tel = page.locator("input[type=tel]").first
    tel.wait_for(state="visible", timeout=30_000)
    tel.fill(phone)


def click_continue(page) -> None:
    page.get_by_role("button", name="Продолжить").click()


def fill_sms_code(page, code: str) -> None:
    page.wait_for_timeout(1500)
    otp_one = page.locator(
        "input[inputmode=numeric], input[autocomplete=one-time-code], input[name*=code i]"
    )
    if otp_one.count() == 1:
        otp_one.first.fill(code)
        return
    cells = page.locator("input[maxlength='1']")
    if cells.count() >= len(code):
        for i, ch in enumerate(code):
            cells.nth(i).fill(ch)
        return
    # fallback: любое видимое текстовое поле кроме tel
    alt = page.locator("input:not([type=tel]):not([type=checkbox]):not([type=hidden])").first
    alt.wait_for(state="visible", timeout=60_000)
    alt.fill(code)


def logged_in(page) -> bool:
    url = page.url.lower()
    if "sign-in" in url or "oauth.tenchat" in url:
        return False
    if "tenchat.ru" in url and "auth" not in url:
        return True
    return "editor" in url or "feed" in url or "profile" in url


def main() -> None:
    parser = argparse.ArgumentParser(description="TenChat SMS bootstrap (VPS)")
    parser.add_argument("--phone", help="10 цифр, иначе tenchat-bootstrap.env.local")
    parser.add_argument("--code", help="SMS-код (иначе ждём файл/stdin)")
    parser.add_argument("--use-proxy", action="store_true", help="ASocks residential (обязательно на VPS)")
    parser.add_argument("--headed", action="store_true", help="Видимый браузер (DISPLAY=:99 + VNC)")
    parser.add_argument("--wait-code-sec", type=int, default=300)
    parser.add_argument("--output", help="storage state path")
    args = parser.parse_args()

    if args.use_proxy and not b17_proxy_configured():
        raise SystemExit("Нужен B17_PROXY_* в browser.env.local")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise SystemExit("pip install playwright && playwright install chromium") from exc

    phone = load_phone(args.phone)
    out = Path(args.output) if args.output else playwright_storage_state_path()
    out.parent.mkdir(parents=True, exist_ok=True)

    proxy_prefix = tenchat_proxy_prefix() if args.use_proxy else ""
    proxy = _proxy_dict(proxy_prefix) if proxy_prefix else None

    with sync_playwright() as pw:
        browser = pw.chromium.launch(
            headless=not args.headed,
            proxy=proxy,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = browser.new_context(locale="ru-RU")
        page = context.new_page()
        page.goto(SIGN_IN, wait_until="domcontentloaded", timeout=120_000)
        page.wait_for_timeout(2000)

        check_checkboxes(page)
        fill_phone(page, phone)
        print(f"\n✓ Телефон введён: +7 ({phone[:3]}) {phone[3:6]}-{phone[6:8]}-{phone[8:]}")
        print(
            "\n⚠ Если открыт VNC (localhost:6080): отметьте капчу «Я не робот» и нажмите «Продолжить» в окне.\n"
            "  Если капчи нет — просто нажмите Enter здесь, скрипт нажмёт «Продолжить» сам.\n"
        )
        input("После капчи / когда готовы отправить SMS — Enter… ")
        if "sign-in" in page.url.lower():
            click_continue(page)
        page.wait_for_timeout(3000)

        if logged_in(page):
            print("Уже вошли без SMS.")
        else:
            code = wait_for_code(args.code, args.wait_code_sec)
            print(f"✓ Код получен, вводим…")
            fill_sms_code(page, code)
            page.wait_for_timeout(2000)
            for btn_name in ("Войти", "Продолжить", "Подтвердить"):
                btn = page.get_by_role("button", name=btn_name)
                if btn.count() and btn.first.is_enabled():
                    btn.first.click()
                    break
            page.wait_for_timeout(5000)
            if not logged_in(page):
                page.goto("https://tenchat.ru/editor", wait_until="domcontentloaded", timeout=90_000)
                page.wait_for_timeout(4000)

        if not logged_in(page):
            page.screenshot(path=str(out.parent / "tenchat-login-failed.png"), full_page=True)
            raise SystemExit(
                f"Вход не удался — вы не залогинены.\n"
                f"URL: {page.url}\n"
                f"Скрин: {out.parent / 'tenchat-login-failed.png'}\n"
                "Откройте http://localhost:6080/vnc.html — капча → SMS → лента TenChat, потом Enter."
            )

        context.storage_state(path=str(out))
        browser.close()

    print(f"\n✓ Сохранено: {out}")
    print("Проверка: python3 scripts/check-tenchat-access.py")


if __name__ == "__main__":
    main()
