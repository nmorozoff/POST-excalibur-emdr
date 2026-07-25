#!/usr/bin/env python3
"""One-time local bootstrap: ftp.env.local from legacy + vk.env.local template."""

from __future__ import annotations

import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MEMORY = PROJECT_ROOT / "posts-emdr-memory"
LEGACY_FTP = Path("/Users/natala/Documents/Проекты СURSOR/sessya-morozova/.ftp-deploy.env")


def main() -> None:
    ftp_dst = MEMORY / "ftp.env.local"
    if not ftp_dst.exists() and LEGACY_FTP.is_file():
        shutil.copy(LEGACY_FTP, ftp_dst)
        print(f"Created {ftp_dst} from legacy FTP env")
    elif ftp_dst.exists():
        print(f"Exists: {ftp_dst}")
    else:
        print(f"Skip FTP: no legacy at {LEGACY_FTP}")

    vk_dst = MEMORY / "vk.env.local"
    vk_example = MEMORY / "vk.env.example"
    if vk_dst.exists():
        text = vk_dst.read_text(encoding="utf-8")
        if "VK_ACCESS_TOKEN=" in text and not text.strip().endswith("VK_ACCESS_TOKEN="):
            print(f"VK token present in {vk_dst}")
        else:
            print(f"Add VK_ACCESS_TOKEN to {vk_dst} (see vk.env.example)")
    elif vk_example.exists():
        shutil.copy(vk_example, vk_dst)
        print(f"Created {vk_dst} — fill VK_ACCESS_TOKEN")


if __name__ == "__main__":
    main()
