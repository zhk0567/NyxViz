"""Encode morph frame PNGs to GIF (no ffmpeg required)."""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
FRAMES = ROOT / "docs" / "figures" / "_morph_frames"
OUT_GIF = ROOT / "docs" / "figures" / "morph_t0_99.gif"
FPS = int(sys.argv[1]) if len(sys.argv) > 1 else 12


def main() -> int:
    paths = sorted(FRAMES.glob("frame_*.png"))
    if not paths:
        print(f"No frames in {FRAMES}", file=sys.stderr)
        return 1
    duration_ms = max(1, round(1000 / FPS))
    frames = [Image.open(p).convert("RGB") for p in paths]
    frames[0].save(
        OUT_GIF,
        save_all=True,
        append_images=frames[1:],
        duration=duration_ms,
        loop=0,
        optimize=False,
    )
    print(f"Wrote {OUT_GIF} ({len(frames)} frames @ {FPS} fps)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
