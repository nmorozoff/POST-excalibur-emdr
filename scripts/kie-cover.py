#!/usr/bin/env python3
"""Generate social cover via Kie.ai gpt-image-2-image-to-image (Carusel API).

Defaults: aspect_ratio 5:4, resolution 1K (≈1280×1024), reference rotation by topic.

Usage:
  python3 scripts/kie-cover.py \\
    --topic sb-06-example \\
    --prompt-file posts-emdr-memory/output/sb-06-example/cover-prompt.txt \\
    --output posts-emdr-memory/output/sb-06-example/cover.png

Key: posts-emdr-memory/kie.env.local or Carusel/.env (KIE_API_KEY).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from cover_upload import load_upload_env, public_cover_url, upload_cover
from kie_client import KieImageClient
from posts_emdr_env import load_env, reference_image_path, reference_slot_for_topic

MODEL = "gpt-image-2-image-to-image"


def reference_public_https(reference: Path, slot: int | None) -> str:
    """HTTPS URL портрета для Kie input_urls (refs/ на сайте, не Kie upload API).

    Если CDN слот пуст — пробуем предыдущие слоты (sb-06 portrait-06 → portrait-05).
    """

    def _reachable(url: str) -> bool:
        try:
            req = urllib.request.Request(url, method="GET")
            req.add_header("Range", "bytes=0-31")
            with urllib.request.urlopen(req, timeout=20) as resp:
                ct = (resp.headers.get("Content-Type") or "").lower()
                return "image" in ct
        except Exception:
            return False

    def _try_slot(s: int | None, ref_file: Path) -> str | None:
        name = ref_file.name if s is None else f"portrait-{s:02d}.jpg"
        remote_name = f"refs/{name}"
        url = public_cover_url(remote_name)
        if _reachable(url):
            return url
        if ref_file.is_file():
            env = load_upload_env()
            upload_cover(ref_file, remote_name, env)
            if _reachable(url):
                return url
        return None

    slots_to_try: list[int | None] = []
    if slot is not None:
        slots_to_try = list(range(slot, 0, -1))
    else:
        slots_to_try = [None]

    ref_dir = reference.parent
    last_url = ""
    for s in slots_to_try:
        ref_file = reference if s is None else ref_dir / f"portrait-{s:02d}.jpg"
        if not ref_file.is_file():
            continue
        url = _try_slot(s, ref_file)
        if url:
            if slot is not None and s != slot:
                print(
                    json.dumps(
                        {
                            "reference_fallback": {
                                "requested_slot": slot,
                                "used_slot": s,
                                "url": url,
                            }
                        },
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
            return url
        last_url = public_cover_url(f"refs/portrait-{s:02d}.jpg" if s else f"refs/{ref_file.name}")

    raise SystemExit(f"Reference uploaded but not reachable: {last_url}")


def main() -> None:
    env = load_env("kie.env.local")
    default_ratio = env.get("KIE_COVER_ASPECT_RATIO", "5:4")
    default_resolution = env.get("KIE_COVER_RESOLUTION", "1K")

    parser = argparse.ArgumentParser(description="Kie.ai cover generator (Posts EMDR)")
    parser.add_argument("--prompt-file", type=Path, required=True)
    parser.add_argument("--topic", default=None, help="topic_id for reference rotation")
    parser.add_argument("--reference", type=Path, default=None, help="Override portrait file")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--aspect-ratio", default=default_ratio)
    parser.add_argument("--resolution", default=default_resolution, choices=["1K", "2K", "4K"])
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

    # FORBIDDEN: previous post cover as i2i reference (breaks rotation)
    ref_name = reference.name.lower()
    if "cover.png" in str(reference) or ref_name.startswith("cover"):
        raise SystemExit(
            "Reference must be portrait-NN.jpg from assets/reference/, "
            "not a previous post cover.png"
        )

    rotation_meta = {
        "topic": topic,
        "slot": slot,
        "reference_path": str(reference),
        "backend": "kie",
        "aspect_ratio": args.aspect_ratio,
        "resolution": args.resolution,
    }
    print(json.dumps({"reference_rotation": rotation_meta}, ensure_ascii=False), file=sys.stderr)

    ref_url = reference_public_https(reference, slot)
    print(f"Reference URL: {ref_url}", file=sys.stderr)

    client = KieImageClient()
    task_id = client.create_task(
        prompt=prompt,
        input_urls=[ref_url],
        aspect_ratio=args.aspect_ratio,
        resolution=args.resolution,
    )
    print(f"taskId: {task_id}", file=sys.stderr)

    data = client.wait_for_task(task_id)
    urls = client.extract_result_urls(data)
    if not urls:
        raise SystemExit(f"No resultUrls in Kie response: {json.dumps(data, ensure_ascii=False)[:500]}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    client.download(urls[0], args.output)
    args.output.with_suffix(".url").write_text(urls[0].strip() + "\n", encoding="utf-8")

    if args.task_log:
        args.task_log.parent.mkdir(parents=True, exist_ok=True)
        args.task_log.write_text(
            json.dumps(
                {
                    "taskId": task_id,
                    "resultUrls": urls,
                    "reference_rotation": rotation_meta,
                    "reference_upload_url": ref_url,
                    "model": MODEL,
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
                "imageURL": urls[0],
                "model": MODEL,
                "reference_rotation": rotation_meta,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
