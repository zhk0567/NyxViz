"""Export task4 band preview PNGs aligned with BandPreviewCanvas (src/spatial/BandPreviewCanvas.tsx)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT / "tools" / "python") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools" / "python"))

from generate_figures import GRID, NYX, OUT, STATS, load_volume  # noqa: E402
from projection_render import max_projection  # noqa: E402
from viz_style import COSMIC_CMAP, global_projection_domain, log_norm_unit  # noqa: E402

BRUSH_GOLD = np.array([0.96, 0.78, 0.26], dtype=np.float64)
BG_RGB = (6 / 255, 12 / 255, 24 / 255)


def render_band_preview_rgb(
    proj: np.ndarray,
    vmin: float,
    vmax: float,
    brush_lo: float,
    brush_hi: float,
) -> np.ndarray:
    """Match BandPreviewCanvas: cosmic background + full gold in brush range."""
    norm = log_norm_unit(proj, vmin, vmax)
    rgb = COSMIC_CMAP(norm)[:, :, :3].astype(np.float64)
    mask = (proj >= brush_lo) & (proj <= brush_hi)
    rgb[mask] = BRUSH_GOLD
    return rgb.transpose(1, 0, 2)


def save_band_preview(
    vol: np.ndarray,
    timeline: dict,
    brush_lo: float,
    brush_hi: float,
    out_name: str,
    size: int = 512,
) -> None:
    proj = max_projection(vol, "xy")
    vmin, vmax = global_projection_domain(timeline)
    rgb = render_band_preview_rgb(proj, vmin, vmax, brush_lo, brush_hi)

    canvas = np.zeros((size, size, 3), dtype=np.float64)
    canvas[:, :] = BG_RGB
    margin = 0
    inner = size - 2 * margin
    img = Image.fromarray((np.clip(rgb, 0, 1) * 255).astype(np.uint8))
    img = img.resize((inner, inner), Image.Resampling.BILINEAR)
    arr = np.asarray(img, dtype=np.float64) / 255.0
    canvas[margin : margin + inner, margin : margin + inner] = arr

    out = OUT / out_name
    fig, ax = plt.subplots(figsize=(5, 5), facecolor="#060c18")
    ax.imshow(canvas, origin="lower", interpolation="bilinear")
    ax.axis("off")
    fig.savefig(out, dpi=100, bbox_inches="tight", pad_inches=0.02, facecolor="#060c18")
    plt.close(fig)
    print(f"Band preview: {out.name} ρ∈[{brush_lo:.2f}, {brush_hi:.2f}]")


def export_band_previews(timeline: dict, t: int = 99) -> int:
    dat = NYX / f"{t:04d}.dat"
    if not dat.exists():
        print(f"Skip band previews: missing {dat}", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    vol = load_volume(dat)
    s = timeline["timesteps"][t]

    bands = [
        ("task4_band_bottom_t99.png", float(s["min"]), float(s["p01"])),
        ("task4_band_mid_t99.png", float(s["p01"]), float(s["p90"])),
        ("task4_band_filament_t99.png", float(s["p90"]), float(s["p99"])),
        ("task4_band_top_t99.png", float(s["p99"]), float(s["max"])),
    ]
    for name, lo, hi in bands:
        save_band_preview(vol, timeline, lo, hi, name)
    return 0


def main() -> int:
    if not STATS.exists():
        print("Run precompute first", file=sys.stderr)
        return 1
    timeline = json.loads(STATS.read_text(encoding="utf-8"))
    return export_band_previews(timeline, 99)


if __name__ == "__main__":
    raise SystemExit(main())
