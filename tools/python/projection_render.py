"""2D max-projection rendering aligned with src/viz/colormap.ts."""
from __future__ import annotations

import numpy as np

from viz_style import COSMIC_CMAP, global_projection_domain, log_norm_unit


def render_projection_rgb(
    proj: np.ndarray,
    vmin: float,
    vmax: float,
    brush_lo: float | None = None,
    brush_hi: float | None = None,
) -> np.ndarray:
    """Return H×W×3 float RGB in [0,1]."""
    h, w = proj.shape
    norm = log_norm_unit(proj, vmin, vmax)
    rgb = COSMIC_CMAP(norm)[:, :, :3]
    if brush_lo is not None and brush_hi is not None:
        mask = (proj >= brush_lo) & (proj <= brush_hi)
        gold = np.array([0.96, 0.78, 0.26])
        rgb[mask] = rgb[mask] * 0.25 + gold * 0.75
    return rgb


def render_xy_projection(
    vol: np.ndarray,
    timeline: dict,
    brush_lo: float | None = None,
    brush_hi: float | None = None,
) -> np.ndarray:
    proj = np.max(vol, axis=2)
    vmin, vmax = global_projection_domain(timeline)
    return render_projection_rgb(proj, vmin, vmax, brush_lo, brush_hi)
