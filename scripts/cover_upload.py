#!/usr/bin/env python3
"""Upload social cover to morozovanatalia.ru — cloud-safe (FTP active + WordPress fallback)."""

from __future__ import annotations

import base64
import ftplib
import json
import os
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

SITE_COVER_BASE = "https://morozovanatalia.ru/social-covers"


def prepare_jpeg(cover: Path, *, width: int = 1024, quality: int = 65) -> Path:
    out = Path(tempfile.gettempdir()) / f"{cover.stem}-vk.jpg"
    try:
        subprocess.run(
            [
                "sips",
                "-s",
                "format",
                "jpeg",
                "-s",
                "formatOptions",
                str(quality),
                "--resampleWidth",
                str(width),
                str(cover),
                "--out",
                str(out),
            ],
            check=True,
            capture_output=True,
        )
        return out
    except (FileNotFoundError, subprocess.CalledProcessError):
        try:
            from PIL import Image
        except ImportError as exc:
            raise SystemExit("Нужен Pillow: pip install Pillow") from exc
        img = Image.open(cover).convert("RGB")
        height = max(1, int(img.height * width / img.width))
        img = img.resize((width, height), Image.Resampling.LANCZOS)
        img.save(out, "JPEG", quality=quality, optimize=True)
        return out


def public_cover_url(remote_name: str) -> str:
    return f"{SITE_COVER_BASE}/{remote_name}"


def _ftp_target(env: dict[str, str], remote_name: str) -> tuple[str, str]:
    server = env["FTP_SERVER"].lstrip("ftp://").split("/")[0]
    remote_dir = env.get("FTP_SERVER_DIR", "/public_html/").rstrip("/")
    remote_rel = f"social-covers/{remote_name}"
    url = f"ftp://{server}{remote_dir}/{remote_rel}"
    return url, remote_rel


def _curl_upload(local: Path, env: dict[str, str], remote_name: str, *, passive: bool) -> None:
    url, _ = _ftp_target(env, remote_name)
    cmd = [
        "curl",
        "-sS",
        "--fail",
        "--connect-timeout",
        "30",
        "--max-time",
        "120",
        "-u",
        f"{env['FTP_USERNAME']}:{env['FTP_PASSWORD']}",
        "-T",
        str(local),
        "--ftp-create-dirs",
    ]
    if passive:
        cmd.append("--ftp-pasv")
    else:
        cmd.extend(["--disable-epsv", "--ftp-port", "-"])
    cmd.append(url)
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        err = (proc.stderr or proc.stdout or "curl failed").strip()
        raise RuntimeError(err)


def _ftplib_upload(local: Path, env: dict[str, str], remote_name: str, *, passive: bool) -> None:
    server = env["FTP_SERVER"].lstrip("ftp://").split("/")[0]
    remote_dir = env.get("FTP_SERVER_DIR", "/public_html/").strip("/")
    last_err: Exception | None = None

    for cwd_chain in (
        [remote_dir, "social-covers"] if remote_dir else ["social-covers"],
        ["public_html", "social-covers"],
        ["social-covers"],
        [],
    ):
        ftp: ftplib.FTP | None = None
        try:
            ftp = ftplib.FTP(timeout=90)
            ftp.connect(server, 21)
            ftp.login(env["FTP_USERNAME"], env["FTP_PASSWORD"])
            ftp.set_pasv(passive)
            for part in cwd_chain:
                try:
                    ftp.cwd(part)
                except ftplib.error_perm:
                    try:
                        ftp.mkd(part)
                    except ftplib.error_perm:
                        pass
                    ftp.cwd(part)
            with local.open("rb") as handle:
                ftp.storbinary(f"STOR {remote_name}", handle)
            ftp.quit()
            return
        except Exception as exc:
            last_err = exc
            if ftp:
                try:
                    ftp.quit()
                except Exception:
                    pass
    raise RuntimeError(str(last_err or "ftplib upload failed"))


def _wordpress_creds(env: dict[str, str]) -> tuple[str, str, str] | None:
    site = (env.get("WORDPRESS_URL") or env.get("WORDPRESS_SITE_URL") or "").strip().rstrip("/")
    user = (env.get("WORDPRESS_USER") or "").strip()
    app_pw = (env.get("WORDPRESS_APP_PASSWORD") or "").strip()
    if site and user and app_pw:
        return site, user, app_pw
    return None


def _wordpress_upload(local: Path, remote_name: str, env: dict[str, str]) -> str:
    creds = _wordpress_creds(env)
    if not creds:
        raise RuntimeError("WORDPRESS_URL, WORDPRESS_USER, WORDPRESS_APP_PASSWORD not set")
    site, user, app_pw = creds
    auth = base64.b64encode(f"{user}:{app_pw}".encode()).decode()
    req = urllib.request.Request(
        f"{site}/wp-json/wp/v2/media",
        data=local.read_bytes(),
        method="POST",
        headers={
            "Authorization": f"Basic {auth}",
            "Content-Disposition": f'attachment; filename="{remote_name}"',
            "Content-Type": "image/jpeg",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            body = json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"WordPress HTTP {exc.code}: {detail}") from exc
    url = body.get("source_url") or (body.get("guid") or {}).get("rendered")
    if not url:
        raise RuntimeError(f"WordPress response without URL: {body!r}")
    return str(url)


def upload_cover(local: Path, remote_name: str, env: dict[str, str]) -> dict[str, Any]:
    """Try upload strategies until URL serves image/jpeg.

    Prefer FTP → social-covers/{name} (stable for VK MCP). WordPress media is fallback
    only if the returned URL passes image Content-Type probe (wp-content often returns HTML).
    """
    errors: list[str] = []
    strategies: list[tuple[str, Any]] = [
        ("curl_active", lambda: _curl_upload(local, env, remote_name, passive=False)),
        ("curl_pasv", lambda: _curl_upload(local, env, remote_name, passive=True)),
        ("ftplib_active", lambda: _ftplib_upload(local, env, remote_name, passive=False)),
        ("ftplib_pasv", lambda: _ftplib_upload(local, env, remote_name, passive=True)),
    ]
    if _wordpress_creds(env):
        strategies.append(("wordpress_media", lambda: _wordpress_upload(local, remote_name, env)))

    for name, fn in strategies:
        try:
            result = fn()
            if isinstance(result, str):
                candidate_url = result
            else:
                candidate_url = public_cover_url(remote_name)
            probe = verify_cover_url(candidate_url)
            if probe["ok"]:
                return {
                    "url": candidate_url,
                    "method": name,
                    "path": f"social-covers/{remote_name}",
                    "verify": probe,
                }
            errors.append(
                f"{name}: URL reachable but not image/jpeg "
                f"(status={probe['http_status']}, url={candidate_url[:80]})"
            )
        except Exception as exc:
            errors.append(f"{name}: {exc}")

    raise SystemExit("Cover upload failed:\n" + "\n".join(errors))


def _curl_delete(env: dict[str, str], remote_name: str, *, passive: bool) -> None:
    _, remote_rel = _ftp_target(env, remote_name)
    server = env["FTP_SERVER"].lstrip("ftp://").split("/")[0]
    remote_dir = env.get("FTP_SERVER_DIR", "/public_html/").rstrip("/")
    url = f"ftp://{server}{remote_dir}/{remote_rel}"
    cmd = [
        "curl",
        "-sS",
        "-u",
        f"{env['FTP_USERNAME']}:{env['FTP_PASSWORD']}",
        url,
        "-Q",
        f"DELE {remote_rel}",
    ]
    if passive:
        cmd.insert(1, "--ftp-pasv")
    else:
        cmd[1:1] = ["--disable-epsv", "--ftp-port", "-"]
    subprocess.run(cmd, capture_output=True, text=True, check=False)


def delete_remote_cover(remote_name: str, env: dict[str, str]) -> None:
    for passive in (False, True):
        try:
            _curl_delete(env, remote_name, passive=passive)
            return
        except Exception:
            pass
    try:
        _ftplib_delete(remote_name, env, passive=False)
    except Exception:
        _ftplib_delete(remote_name, env, passive=True)


def _ftplib_delete(remote_name: str, env: dict[str, str], *, passive: bool) -> None:
    server = env["FTP_SERVER"].lstrip("ftp://").split("/")[0]
    remote_dir = env.get("FTP_SERVER_DIR", "/public_html/").strip("/")
    ftp = ftplib.FTP(timeout=60)
    ftp.connect(server, 21)
    ftp.login(env["FTP_USERNAME"], env["FTP_PASSWORD"])
    ftp.set_pasv(passive)
    if remote_dir:
        ftp.cwd(remote_dir)
    ftp.cwd("social-covers")
    ftp.delete(remote_name)
    ftp.quit()


def verify_url(url: str) -> int:
    proc = subprocess.run(
        ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", "-L", url],
        capture_output=True,
        text=True,
        check=False,
    )
    return int((proc.stdout or "0").strip() or "0")


def url_serves_image(url: str, *, timeout: int = 30) -> bool:
    """True if URL responds with image/* (not HTML login/404 page with HTTP 200)."""
    try:
        req = urllib.request.Request(url, method="GET")
        req.add_header("Range", "bytes=0-63")
        req.add_header(
            "User-Agent",
            "Mozilla/5.0 (compatible; PostsEMDR-cover-verify/1.0)",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", None) or resp.getcode()
            ct = (resp.headers.get("Content-Type") or "").lower()
            if status not in (200, 206):
                return False
            return "image" in ct or "octet-stream" in ct
    except Exception:
        return False


def verify_cover_url(url: str) -> dict[str, Any]:
    """HTTP status + whether Content-Type is image (for VK MCP / Zernio gates)."""
    status = verify_url(url)
    serves_image = url_serves_image(url) if status in (200, 301, 302) else False
    return {"http_status": status, "serves_image": serves_image, "ok": serves_image}


def probe_ftp(env: dict[str, str]) -> dict[str, Any]:
    """Lightweight FTP probe for cloud preflight."""
    server = env["FTP_SERVER"].lstrip("ftp://").split("/")[0]
    result: dict[str, Any] = {"server": server, "modes": {}}
    for mode, passive in (("active", False), ("passive", True)):
        try:
            ftp = ftplib.FTP(timeout=20)
            ftp.connect(server, 21)
            ftp.login(env["FTP_USERNAME"], env["FTP_PASSWORD"])
            ftp.set_pasv(passive)
            ftp.voidcmd("NOOP")
            result["modes"][mode] = "ok"
            ftp.quit()
        except Exception as exc:
            result["modes"][mode] = str(exc)
    result["ok"] = result["modes"].get("active") == "ok" or result["modes"].get("passive") == "ok"
    result["upload_recommended"] = (
        "curl_active"
        if result["modes"].get("active") == "ok"
        else ("curl_pasv" if result["modes"].get("passive") == "ok" else "wordpress_or_fix")
    )
    if _wordpress_creds(env):
        result["wordpress_fallback"] = True
    return result


def load_upload_env() -> dict[str, str]:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from posts_emdr_env import MEMORY, load_env as _load

    data: dict[str, str] = {}
    for name in ("ftp.env.local", "wordpress.env.local"):
        try:
            data.update(_load(name))
        except SystemExit:
            pass
    for key in (
        "FTP_SERVER",
        "FTP_USERNAME",
        "FTP_PASSWORD",
        "FTP_SERVER_DIR",
        "WORDPRESS_URL",
        "WORDPRESS_SITE_URL",
        "WORDPRESS_USER",
        "WORDPRESS_APP_PASSWORD",
    ):
        val = os.environ.get(key, "").strip()
        if val:
            data[key] = val
    if not data.get("FTP_SERVER"):
        legacy = Path("/Users/natala/Documents/Проекты СURSOR/sessya-morozova/.ftp-deploy.env")
        if legacy.is_file():
            for line in legacy.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                data[k.strip()] = v.strip().strip('"').strip("'")
    missing = [k for k in ("FTP_SERVER", "FTP_USERNAME", "FTP_PASSWORD") if not data.get(k)]
    if missing and not _wordpress_creds(data):
        raise SystemExit(f"Missing FTP secrets and no WordPress fallback: {missing}")
    return data
