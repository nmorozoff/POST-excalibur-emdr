"""Kie.ai GPT Image 2 Image-to-Image API client."""

from __future__ import annotations

from typing import Any

from kie_common import KieTaskClient

MODEL = "gpt-image-2-image-to-image"


class KieImageClient(KieTaskClient):
    def create_task(
        self,
        prompt: str,
        input_urls: list[str] | None = None,
        aspect_ratio: str = "5:4",
        resolution: str = "1K",
        callback_url: str | None = None,
    ) -> str:
        payload: dict[str, Any] = {
            "model": MODEL,
            "input": {
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "resolution": resolution,
            },
        }
        if input_urls:
            payload["input"]["input_urls"] = input_urls
        if callback_url:
            payload["callBackUrl"] = callback_url
        return self.create_task_raw(payload)
