"""Resize a Playwright full-page capture to doc poster width (3840px)."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "figures"
TARGET_W = 3840


def main() -> int:
    src = Path(sys.argv[1]) if len(sys.argv) > 1 else OUT / "_app_poster_capture_raw.png"
    dst = OUT / "_app_poster_capture_resized.png"
    if not src.is_file():
        print(f"Missing: {src}", file=sys.stderr)
        return 1

    img = Image.open(src).convert("RGB")
    if img.width != TARGET_W:
        scale = TARGET_W / img.width
        img = img.resize((TARGET_W, max(1, int(img.height * scale))), Image.Resampling.LANCZOS)

    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, format="PNG", optimize=True)
    print(f"Resized {src.name} → {dst.name} ({img.width}×{img.height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
