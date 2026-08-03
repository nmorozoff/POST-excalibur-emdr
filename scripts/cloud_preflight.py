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
    browser_backend_name,
    browser_headless,
    is_cloud_runtime,
    load_env,
    reference_image_path,
    playwright_storage_state_path,
)
from browser_backend import browser_ready

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

    checks["vk_token"] = _check_file("vk.env.local", ["VK_ACCESS_TOKEN"])
    checks["vk_group"] = _check_file("vk.env.local", ["VK_GROUP_ID"])
    vk_via_mcp = not checks["vk_token"]["ok"] and checks["vk_group"]["ok"]
    checks["vk"] = {
        "ok": checks["vk_token"]["ok"] or vk_via_mcp,
        "mode": "api" if checks["vk_token"]["ok"] else ("mcp" if vk_via_mcp else "missing"),
    }
    checks["zernio"] = _check_file(
        "zernio.env.local",
        ["ZERNIO_API_KEY", "ZERNIO_FACEBOOK_ACCOUNT_ID"],
    )
    checks["kie"] = _check_file("kie.env.local", ["KIE_API_KEY"])
    checks["runware"] = _check_file("runware.env.local", ["RUNWARE_API_KEY"])
    checks["cover_api"] = {
        "ok": checks["kie"]["ok"] or checks["runware"]["ok"],
        "preferred": "kie" if checks["kie"]["ok"] else ("runware" if checks["runware"]["ok"] else "missing"),
    }
    checks["ftp"] = _check_file(
        "ftp.env.local",
        ["FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD"],
    )
    if checks["ftp"]["ok"]:
        try:
            from cover_upload import load_upload_env, probe_ftp

            env = load_upload_env()
            probe = probe_ftp(env)
            checks["ftp"]["probe"] = probe
            checks["ftp"]["upload_ready"] = probe.get("ok") or probe.get("wordpress_fallback")
        except SystemExit as exc:
            checks["ftp"]["probe"] = {"ok": False, "error": str(exc)}
            checks["ftp"]["upload_ready"] = False
    if not checks["ftp"]["ok"]:
        legacy = Path("/Users/natala/Documents/Проекты СURSOR/sessya-morozova/.ftp-deploy.env")
        if legacy.is_file():
            checks["ftp"] = {"ok": True, "path": str(legacy), "source": "legacy_fallback"}
            try:
                from cover_upload import load_upload_env, probe_ftp

                probe = probe_ftp(load_upload_env())
                checks["ftp"]["probe"] = probe
                checks["ftp"]["upload_ready"] = probe.get("ok") or probe.get("wordpress_fallback")
            except SystemExit as exc:
                checks["ftp"]["probe"] = {"ok": False, "error": str(exc)}
                checks["ftp"]["upload_ready"] = False

    from posts_emdr_env import REFERENCE_MANIFEST, reference_slot_count

    ref = reference_image_path()
    manifest_ok = REFERENCE_MANIFEST.is_file()
    slot_files = 0
    if manifest_ok:
        import json

        try:
            data = json.loads(REFERENCE_MANIFEST.read_text(encoding="utf-8"))
            for item in data.get("slots") or []:
                p = ref.parent / str(item.get("file", ""))
                if p.is_file():
                    slot_files += 1
        except (json.JSONDecodeError, OSError):
            pass
    checks["reference_image"] = {
        "ok": ref.is_file(),
        "path": str(ref),
        "manifest": str(REFERENCE_MANIFEST) if manifest_ok else None,
        "rotation_slots_ready": slot_files,
        "rotation_slots_total": reference_slot_count(),
        "rotation_ok": slot_files >= reference_slot_count() or not manifest_ok,
    }

    browser = {
        "ok": browser_ready(),
        "backend": browser_backend_name(),
        "note": "Linux VPS: BROWSER_BACKEND=playwright; Mac: undetectable",
    }
    if browser["backend"] == "playwright":
        state = playwright_storage_state_path()
        browser["storage_state"] = str(state)
        browser["storage_exists"] = state.is_file()
        browser["headless"] = browser_headless()
    else:
        try:
            undetectable_url = load_env("b17.env.local").get("UNDETECTABLE_BASE_URL", "")
        except SystemExit:
            import os

            undetectable_url = os.environ.get("UNDETECTABLE_BASE_URL", "")
        browser["base_url"] = undetectable_url or "http://127.0.0.1:25325"
    checks["browser"] = browser

    script_platforms = ("max", "telegram", "zernio", "ftp")
    cover_ok = checks["cover_api"]["ok"]
    auto_ok = all(
        checks[p]["ok"]
        for p in script_platforms
    ) and checks["telegram"].get("channels_configured") and checks["reference_image"]["ok"] and cover_ok

    report = {
        "runtime": "cloud" if is_cloud_runtime() else "local",
        "checks": checks,
        "ready_for_auto_publish": auto_ok,
        "vk_publish_mode": checks["vk"].get("mode", "missing"),
        "vk_mcp_required_after_scripts": checks["vk"].get("mode") == "mcp",
        "auto_platforms": ["max", "telegram", "facebook"],
        "vk_platform": "mcp" if checks["vk"].get("mode") == "mcp" else "script",
        "browser_platforms_deferred": not checks["browser"]["ok"],
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
