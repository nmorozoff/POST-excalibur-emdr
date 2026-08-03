"""Shared Kie.ai API utilities (urllib, no requests). Posts EMDR + Carusel key fallback."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_BASE = "https://api.kie.ai/api/v1"
DEFAULT_UPLOAD_BASE = "https://kieai.redpandaai.co"
CARUSEL_ENV = Path.home() / ".cursor/plugins/local/carusel/.env"


def _parse_env_line_file(path: Path) -> dict[str, str]:
    data: dict[str, str] = {}
    if not path.is_file():
        return data
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        data[key.strip()] = value.strip().strip('"').strip("'")
    return data


def load_api_key(explicit_key: str | None = None) -> str:
    if explicit_key:
        return explicit_key.strip()

    key = os.environ.get("KIE_API_KEY", "").strip()
    if key:
        return key

    import sys

    script_dir = Path(__file__).resolve().parent
    if str(script_dir) not in sys.path:
        sys.path.insert(0, str(script_dir))

    try:
        from posts_emdr_env import load_env

        data = load_env("kie.env.local")
        key = data.get("KIE_API_KEY", "").strip()
        if key:
            return key
    except SystemExit:
        pass

    if CARUSEL_ENV.is_file():
        key = _parse_env_line_file(CARUSEL_ENV).get("KIE_API_KEY", "").strip()
        if key:
            return key

    raise ValueError(
        "KIE_API_KEY not set. Add to posts-emdr-memory/kie.env.local, "
        "Cursor Cloud Secrets, or Carusel/.env (https://kie.ai/api-key)"
    )


def _request_json(
    method: str,
    url: str,
    *,
    api_key: str,
    payload: dict | None = None,
    data: bytes | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 120,
) -> dict:
    hdrs = {"Authorization": f"Bearer {api_key}"}
    if headers:
        hdrs.update(headers)
    body = data
    if payload is not None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        hdrs.setdefault("Content-Type", "application/json")
    req = Request(url, data=body, headers=hdrs, method=method)
    try:
        with urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:2000]
        raise RuntimeError(f"HTTP {exc.code} {url}: {detail}") from exc


class KieTaskClient:
    """Base client for Kie.ai createTask + recordInfo polling."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        poll_interval: float = 5.0,
        poll_timeout: float = 1200.0,
    ) -> None:
        self.api_key = load_api_key(api_key)
        self.base_url = (base_url or os.getenv("KIE_API_BASE") or DEFAULT_BASE).rstrip("/")
        self.poll_interval = float(os.getenv("KIE_POLL_INTERVAL_SEC", poll_interval))
        self.poll_timeout = float(os.getenv("KIE_POLL_TIMEOUT_SEC", poll_timeout))

    def create_task_raw(self, payload: dict[str, Any]) -> str:
        body = _request_json(
            "POST",
            f"{self.base_url}/jobs/createTask",
            api_key=self.api_key,
            payload=payload,
            timeout=60,
        )
        if body.get("code") != 200:
            raise RuntimeError(f"createTask failed: {body.get('msg', body)}")
        task_id = body.get("data", {}).get("taskId")
        if not task_id:
            raise RuntimeError(f"No taskId in response: {body}")
        return task_id

    def get_task(self, task_id: str) -> dict[str, Any]:
        qs = urlencode({"taskId": task_id})
        body = _request_json(
            "GET",
            f"{self.base_url}/jobs/recordInfo?{qs}",
            api_key=self.api_key,
            timeout=60,
        )
        if body.get("code") != 200:
            raise RuntimeError(f"recordInfo failed: {body.get('msg', body)}")
        return body.get("data", {})

    def wait_for_task(self, task_id: str) -> dict[str, Any]:
        deadline = time.time() + self.poll_timeout
        attempt = 0
        while time.time() < deadline:
            data = self.get_task(task_id)
            state = data.get("state")
            if state == "success":
                return data
            if state == "fail":
                raise RuntimeError(
                    f"Task failed: {data.get('failCode')} — {data.get('failMsg')}"
                )
            attempt += 1
            if attempt == 1 or attempt % 6 == 0:
                elapsed = int(time.time() - (deadline - self.poll_timeout))
                print(f"  poll #{attempt} state={state!r} elapsed={elapsed}s ...")
            time.sleep(self.poll_interval)
        raise TimeoutError(f"Task {task_id} timed out after {self.poll_timeout}s")

    @staticmethod
    def extract_result_urls(task_data: dict[str, Any]) -> list[str]:
        raw = task_data.get("resultJson")
        if not raw:
            return []
        if isinstance(raw, str):
            parsed = json.loads(raw)
        else:
            parsed = raw
        urls = parsed.get("resultUrls") or []
        if not isinstance(urls, list):
            return []
        return [u for u in urls if isinstance(u, str) and u]

    def download(self, url: str, dest: Path) -> Path:
        dest.parent.mkdir(parents=True, exist_ok=True)
        req = Request(url, headers={"User-Agent": "posts-emdr-kie/1.0"})
        with urlopen(req, timeout=300) as resp:
            dest.write_bytes(resp.read())
        return dest

    def upload_file_stream(
        self,
        local_path: Path,
        *,
        upload_path: str = "posts-emdr",
        upload_base: str | None = None,
    ) -> str:
        local_path = Path(local_path)
        if not local_path.is_file():
            raise FileNotFoundError(local_path)
        try:
            return self._upload_stream_multipart(local_path, upload_path=upload_path, upload_base=upload_base)
        except RuntimeError as exc:
            if local_path.stat().st_size <= 10 * 1024 * 1024:
                print(f"WARN: stream upload failed ({exc}); trying base64", file=__import__("sys").stderr)
                return self._upload_base64(local_path, upload_path=upload_path, upload_base=upload_base)
            raise

    def _upload_base64(
        self,
        local_path: Path,
        *,
        upload_path: str,
        upload_base: str | None,
    ) -> str:
        base = (upload_base or os.getenv("KIE_FILE_UPLOAD_BASE") or DEFAULT_UPLOAD_BASE).rstrip("/")
        name = local_path.name
        mime, _ = mimetypes.guess_type(name)
        mime = mime or "application/octet-stream"
        b64 = base64.b64encode(local_path.read_bytes()).decode("ascii")
        body_json = _request_json(
            "POST",
            f"{base}/api/file-base64-upload",
            api_key=self.api_key,
            payload={
                "base64Data": f"data:{mime};base64,{b64}",
                "uploadPath": upload_path,
                "fileName": name,
            },
            timeout=300,
        )
        if not body_json.get("success") and body_json.get("code") != 200:
            raise RuntimeError(f"Kie base64 upload failed: {body_json.get('msg', body_json)}")
        data = body_json.get("data") or {}
        url = data.get("fileUrl") or data.get("downloadUrl")
        if not url or not str(url).startswith("http"):
            raise RuntimeError(f"No fileUrl in base64 upload response: {body_json}")
        return str(url)

    def _upload_stream_multipart(
        self,
        local_path: Path,
        *,
        upload_path: str,
        upload_base: str | None,
    ) -> str:
        base = (upload_base or os.getenv("KIE_FILE_UPLOAD_BASE") or DEFAULT_UPLOAD_BASE).rstrip(
            "/"
        )
        name = local_path.name
        mime, _ = mimetypes.guess_type(name)
        mime = mime or "application/octet-stream"
        boundary = f"----kie{uuid.uuid4().hex}"
        file_bytes = local_path.read_bytes()

        parts: list[bytes] = []
        for field, value in (("uploadPath", upload_path), ("fileName", name)):
            parts.append(
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="{field}"\r\n\r\n'
                f"{value}\r\n".encode()
            )
        parts.append(
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{name}"\r\n'
            f"Content-Type: {mime}\r\n\r\n".encode()
            + file_bytes
            + b"\r\n"
        )
        parts.append(f"--{boundary}--\r\n".encode())
        body = b"".join(parts)

        body_json = _request_json(
            "POST",
            f"{base}/api/file-stream-upload",
            api_key=self.api_key,
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            timeout=300,
        )
        if not body_json.get("success") and body_json.get("code") != 200:
            raise RuntimeError(f"Kie upload failed: {body_json.get('msg', body_json)}")
        data = body_json.get("data") or {}
        url = data.get("fileUrl") or data.get("downloadUrl")
        if not url or not str(url).startswith("http"):
            raise RuntimeError(f"No fileUrl in upload response: {body_json}")
        return str(url)
