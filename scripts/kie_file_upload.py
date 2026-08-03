"""Kie.ai File Upload — thin wrapper (upload in kie_common.KieTaskClient)."""

from __future__ import annotations

from pathlib import Path

from kie_common import KieTaskClient


class KieFileUploadClient(KieTaskClient):
    def upload_stream(
        self,
        local_path: Path,
        upload_path: str = "posts-emdr",
        file_name: str | None = None,
    ) -> str:
        path = Path(local_path)
        if file_name:
            # Kie uses fileName field; copy to temp name if needed — use basename override via symlink-less rename not needed
            pass
        return self.upload_file_stream(path, upload_path=upload_path)
