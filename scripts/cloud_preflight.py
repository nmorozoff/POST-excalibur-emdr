#!/usr/bin/env python3
"""Preflight checks for local + Cloud Agent publish."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from posts_emdr_env import (
    MEMORY,
    PROJECT_ROOT,
    is_cloud_runtime,
    load_env,
    reference_image_path,
    undetectable_reachable,
)

AUTO_PLATFORMS = ("max", "telegram", "vk", "facebook")
BROWSER_PLATFORMS = ("b17", "tenchat")


def _check_file(name: str, required_keys: list[str]) -> dict:
    path = MEMORY / name
    try:
        data = load_env(name, required=required_keys)
        return {"ok": True, "path": str(path), "keys": list(data.keys())}
    except SystemExit as exc:
        return {"ok": False, "path": str(path), "error": str(exc)}


def run_preflight(*, strict: bool = True) -> dict:
    checks: dict[str, dict] = {}

    checks["max"] = _check_file("max.env.local", ["MAX_BOT_TOKEN", "MAX_CHAT_ID"])
    checks["telegram"] = _check_file(
        "telegram.env.local",
        ["TELEGRAM_BOT_TOKEN"],
    )
    tg = load_env("telegram.env.local") if checks["telegram"]["ok"] else {}
    has_channels = bool(
        tg.get("TELEGRAM_CHANNEL_CHAT_IDS") or tg.get("TELEGRAM_CHANNEL_CHAT_ID")
    )
    checks["telegram"]["channels_configured"] = has_channels

    checks["vk"] = _check_file("vk.env.local", ["VK_ACCESS_TOKEN", "VK_GROUP_ID"])
    checks["zernio"] = _check_file(
        "zernio.env.local",
        ["ZERNIO_API_KEY", "ZERNIO_FACEBOOK_ACCOUNT_ID"],
    )
    checks["runware"] = _check_file("runware.env.local", ["RUNWARE_API_KEY"])
    checks["ftp"] = _check_file(
        "ftp.env.local",
        ["FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD"],
    )
    if not checks["ftp"]["ok"]:
        legacy = Path("/Users/natala/Documents/Проекты СURSOR/sessya-morozova/.ftp-deploy.env")
        if legacy.is_file():
            checks["ftp"] = {"ok": True, "path": str(legacy), "source": "legacy_fallback"}

    ref = reference_image_path()
    checks["reference_image"] = {
        "ok": ref.is_file(),
        "path": str(ref),
    }

    try:
        undetectable_url = load_env("b17.env.local").get("UNDETECTABLE_BASE_URL", "")
    except SystemExit:
        import os

        undetectable_url = os.environ.get("UNDETECTABLE_BASE_URL", "")
    checks["undetectable"] = {
        "ok": undetectable_reachable(undetectable_url or None),
        "base_url": undetectable_url or "http://127.0.0.1:25325",
        "note": "b17/TenChat need local Undetectable; skipped in cloud if unreachable",
    }

    auto_ok = all(
        checks[p]["ok"]
        for p in ("max", "telegram", "vk", "zernio", "runware", "ftp")
    ) and checks["telegram"].get("channels_configured") and checks["reference_image"]["ok"]

    report = {
        "runtime": "cloud" if is_cloud_runtime() else "local",
        "checks": checks,
        "ready_for_auto_publish": auto_ok,
        "auto_platforms": list(AUTO_PLATFORMS),
        "browser_platforms_deferred": not checks["undetectable"]["ok"],
    }

    if strict and not auto_ok:
        missing = [k for k, v in checks.items() if isinstance(v, dict) and v.get("ok") is False]
        report["blockers"] = missing

    return report


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    report = run_preflight(strict=False)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        status = "READY" if report["ready_for_auto_publish"] else "NOT READY"
        print(f"Posts EMDR preflight: {status} ({report['runtime']})")
        for name, check in report["checks"].items():
            ok = check.get("ok")
            mark = "✓" if ok else "✗"
            print(f"  {mark} {name}: {check}")
    sys.exit(0 if report["ready_for_auto_publish"] else 2)


if __name__ == "__main__":
    main()
