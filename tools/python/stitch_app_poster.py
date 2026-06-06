"""Vertically stitch /app.html section screenshots into one poster PNG."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "figures"
TARGET_W = 3840
BG = (5, 10, 20)
GAP = 18


def stitch_parts(parts: list[Path], dst: Path, *, target_w: int = TARGET_W) -> None:
    imgs: list[Image.Image] = []
    for p in parts:
        if not p.is_file():
            raise FileNotFoundError(p)
        im = Image.open(p).convert("RGBA")
        if im.width != target_w:
            scale = target_w / im.width
            im = im.resize((target_w, max(1, int(im.height * scale))), Image.Resampling.LANCZOS)
        imgs.append(im)

    total_h = sum(im.height for im in imgs) + GAP * max(0, len(imgs) - 1)
    canvas = Image.new("RGBA", (target_w, total_h), (*BG, 255))
    y = 0
    for i, im in enumerate(imgs):
        canvas.paste(im, (0, y), im)
        y += im.height + (GAP if i < len(imgs) - 1 else 0)

    dst.parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(dst, format="PNG", optimize=True)
    print(f"Stitched {len(imgs)} parts → {dst.name} ({target_w}×{total_h})")


def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: stitch_app_poster.py <part1.png> [part2.png ...]", file=sys.stderr)
        return 1
    parts = [Path(a) for a in sys.argv[1:]]
    dst = OUT / "_app_poster_capture_resized.png"
    stitch_parts(parts, dst)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
