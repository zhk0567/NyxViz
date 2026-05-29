"""Derive filament density band from XY max projection (spatial → statistical)."""
from __future__ import annotations

from pathlib import Path

import numpy as np

GRID = 128


def load_volume_dat(path: Path) -> np.ndarray:
    flat = np.fromfile(path, dtype="<f4")
    return flat.reshape((GRID, GRID, GRID), order="C")


def xy_max_projection(vol: np.ndarray) -> np.ndarray:
    return np.max(vol, axis=2)


def filament_density_band(
    vol: np.ndarray,
    proj_percentile: float = 88.0,
    density_percentiles: tuple[float, float] = (8.0, 92.0),
) -> tuple[float, float, np.ndarray]:
    """
    Identify bright filament pixels on max projection, return density band [lo, hi]
    and boolean mask (128×128, x–y).
    """
    proj = xy_max_projection(vol)
    thr = float(np.percentile(proj, proj_percentile))
    mask = proj >= thr
    if not mask.any():
        lo, hi = float(proj.min()), float(proj.max())
        return lo, hi, mask
    dens = proj[mask]
    lo = float(np.percentile(dens, density_percentiles[0]))
    hi = float(np.percentile(dens, density_percentiles[1]))
    return lo, hi, mask
