#!/usr/bin/env python3
"""Generate social cover via Grsai gpt-image-2 (primary for MSP short-blog).

Usage:
  python3 scripts/grsai-cover.py \\
    --topic sb-09-one-question-calms \\
    --prompt-file posts-emdr-memory/output/sb-09/cover-prompt.txt \\
    --output posts-emdr-memory/output/sb-09/cover.png

Key: posts-emdr-memory/grsai.env.local (GRSAI_API_KEY).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cover_upload import ensure_reference_public_url
from grsai_client import download_image, generate_image
from posts_emdr_env import load_env, reference_image_path, reference_slot_for_topic

MODEL_DEFAULT = "gpt-image-2"


def main() -> None:
    env = load_env("grsai.env.local", required=["GRSAI_API_KEY"])
    api_key = env["GRSAI_API_KEY"]
    base_url = env.get("GRSAI_API_BASE", "https://grsaiapi.com")
    aspect_ratio = env.get("GRSAI_COVER_ASPECT_RATIO", "1280x1024")
    quality = env.get("GRSAI_COVER_QUALITY", "low")
    model = env.get("GRSAI_COVER_MODEL", MODEL_DEFAULT)

    parser = argparse.ArgumentParser(description="Grsai cover generator (Posts EMDR)")
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--topic", default=None)
    parser.add_argument("--reference", type=Path, default=None)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--aspect-ratio", default=aspect_ratio)
    parser.add_argument("--quality", default=quality, choices=["auto", "low", "medium", "high"])
    parser.add_argument("--task-log", type=Path, default=None)
    args = parser.parse_args()

    prompt = args.prompt_file.read_text(encoding="utf-8").strip()
    topic = args.topic
    if topic is None:
        stem = args.output.parent.name
        if stem.startswith("sb-") or re.match(r"^\d", stem):
            topic = stem

    reference = args.reference
    slot = None
    if reference is None and topic:
        reference = reference_image_path(topic)
        slot = reference_slot_for_topic(topic)
    elif reference is None:
        reference = reference_image_path(None)

    if not reference or not reference.is_file():
        raise SystemExit(f"Reference image missing: {reference}")

    ref_name = reference.name.lower()
    if "cover.png" in str(reference) or ref_name.startswith("cover"):
        raise SystemExit(
            "Reference must be portrait-NN.jpg from assets/reference/, not cover.png"
        )

    rotation_meta = {
        "topic": topic,
        "slot": slot,
        "reference_path": str(reference),
        "backend": "grsai",
        "aspect_ratio": args.aspect_ratio,
        "quality": args.quality,
        "model": model,
    }
    print(json.dumps({"reference_rotation": rotation_meta}, ensure_ascii=False), file=sys.stderr)

    ref_url = ensure_reference_public_url(reference, slot=slot)
    print(f"Reference URL: {ref_url}", file=sys.stderr)
    rotation_meta["reference_upload_url"] = ref_url

    result = generate_image(
        api_key=api_key,
        base_url=base_url,
        prompt=prompt,
        model=model,
        aspect_ratio=args.aspect_ratio,
        quality=args.quality,
        reference_urls=[ref_url],
        use_poll=True,
    )
    image_url = result["image_url"]
    task_id = result.get("task_id", "")
    print(f"taskId: {task_id}", file=sys.stderr)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    download_image(image_url, args.output)
    args.output.with_suffix(".url").write_text(image_url.strip() + "\n", encoding="utf-8")

    if args.task_log:
        args.task_log.parent.mkdir(parents=True, exist_ok=True)
        args.task_log.write_text(
            json.dumps(
                {
                    "taskId": task_id,
                    "imageURL": image_url,
                    "reference_rotation": rotation_meta,
                    "reference_upload_url": ref_url,
                    "model": model,
                    "backend": "grsai",
                    "raw": result.get("raw"),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )

    print(
        json.dumps(
            {
                "status": "ok",
                "output": str(args.output),
                "imageURL": image_url,
                "model": model,
                "backend": "grsai",
                "reference_rotation": rotation_meta,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
