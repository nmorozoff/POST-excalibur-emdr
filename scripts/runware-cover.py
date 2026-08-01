#!/usr/bin/env python3
"""Generate cover via Runware GPT Image 2 (openai:gpt-image@2).

Docs: https://runware.ai/docs/models/openai-gpt-image-2

Usage:
  export RUNWARE_API_KEY=...
  python scripts/runware-cover.py \\
    --prompt-file posts-emdr-memory/output/01-panic-night/cover-prompt.txt \\
    --reference "/Users/natala/Desktop/РЕФЕРЕНСЫ/0C2A3279.jpg" \\
  --output posts-emdr-memory/output/01-panic-night/cover.png

Defaults from runware.env.local: 1280×1024, quality low.

**Runware — только с явного разрешения пользователя.** Запрещены тестовые/диагностические генерации.
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import uuid
from pathlib import Path
from urllib.request import Request, urlopen


API_URL = "https://api.runware.ai/v1"
MODEL_ID = "openai:gpt-image@2"


def load_env_defaults() -> dict[str, str]:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from posts_emdr_env import load_env

    return load_env("runware.env.local")


def load_api_key() -> str:
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from posts_emdr_env import load_env

    data = load_env("runware.env.local", required=["RUNWARE_API_KEY"])
    return data["RUNWARE_API_KEY"]


def file_to_data_uri(path: Path) -> str:
    suffix = path.suffix.lower().lstrip(".")
    mime = {"jpg": "jpeg", "jpeg": "jpeg", "png": "png", "webp": "webp"}.get(suffix, "jpeg")
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/{mime};base64,{b64}"


def run_inference(
    api_key: str,
    prompt: str,
    reference: Path | None,
    width: int,
    height: int,
    quality: str,
    output_format: str,
) -> dict:
    task_uuid = str(uuid.uuid4())
    payload_item: dict = {
        "taskType": "imageInference",
        "taskUUID": task_uuid,
        "model": MODEL_ID,
        "positivePrompt": prompt,
        "width": width,
        "height": height,
        "numberResults": 1,
        "outputType": "URL",
        "outputFormat": output_format,
        "includeCost": True,
        "providerSettings": {
            "openai": {
                "quality": quality,
            }
        },
    }
    if reference:
        payload_item["inputs"] = {"referenceImages": [file_to_data_uri(reference)]}

    body = json.dumps([payload_item]).encode("utf-8")
    req = Request(
        API_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    with urlopen(req, timeout=180) as resp:
        data = json.loads(resp.read().decode("utf-8"))

    items = data.get("data") or data.get("results") or []
    if not items:
        raise SystemExit(f"Empty Runware response: {json.dumps(data, ensure_ascii=False)[:2000]}")

    for item in items:
        if item.get("taskUUID") == task_uuid or item.get("imageURL"):
            return item
    return items[0]


def download_url(url: str, dest: Path) -> None:
    req = Request(url, headers={"User-Agent": "posts-emdr-runware/1.0"})
    with urlopen(req, timeout=120) as resp:
        dest.write_bytes(resp.read())


def main() -> None:
    env_defaults = load_env_defaults()
    default_width = int(env_defaults.get("RUNWARE_COVER_WIDTH", "1280"))
    default_height = int(env_defaults.get("RUNWARE_COVER_HEIGHT", "720"))
    default_quality = env_defaults.get("RUNWARE_COVER_QUALITY", "low")

    parser = argparse.ArgumentParser(description="Runware GPT Image 2 cover generator")
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument(
        "--topic",
        default=None,
        help="topic_id for reference rotation (e.g. sb-04-what-if-phrase)",
    )
    parser.add_argument("--reference", type=Path, default=None, help="Portrait reference (i2i)")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--width", type=int, default=default_width, help="default from runware.env.local")
    parser.add_argument("--height", type=int, default=default_height, help="default from runware.env.local")
    parser.add_argument(
        "--quality",
        choices=["auto", "low", "medium", "high"],
        default=default_quality,
    )
    parser.add_argument("--format", dest="output_format", default="PNG", choices=["PNG", "JPG", "WEBP"])
    args = parser.parse_args()

    prompt = args.prompt_file.read_text(encoding="utf-8").strip()
    reference = args.reference
    if reference is None:
        import sys

        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from posts_emdr_env import reference_image_path, reference_slot_for_topic

        topic = args.topic
        if topic is None:
            stem = args.output.parent.name
            if stem.startswith("sb-") or re.match(r"^\d", stem):
                topic = stem
        reference = reference_image_path(topic)
        if topic:
            print(
                json.dumps(
                    {
                        "reference_rotation": {
                            "topic": topic,
                            "slot": reference_slot_for_topic(topic),
                            "path": str(reference),
                        }
                    },
                    ensure_ascii=False,
                ),
                file=sys.stderr,
            )
    if reference and not reference.exists():
        raise SystemExit(f"Reference not found: {reference}")

    api_key = load_api_key()
    result = run_inference(
        api_key=api_key,
        prompt=prompt,
        reference=reference,
        width=args.width,
        height=args.height,
        quality=args.quality,
        output_format=args.output_format,
    )

    image_url = result.get("imageURL")
    if not image_url:
        raise SystemExit(f"No imageURL in response: {json.dumps(result, ensure_ascii=False)}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    download_url(image_url, args.output)
    args.output.with_suffix(".url").write_text(image_url.strip() + "\n", encoding="utf-8")

    cost = result.get("cost")
    print(json.dumps({
        "status": "ok",
        "output": str(args.output),
        "imageURL": image_url,
        "cost_usd": cost,
        "width": args.width,
        "height": args.height,
        "quality": args.quality,
        "model": MODEL_ID,
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
