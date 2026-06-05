"""Spatial / higher-order statistics for Nyx 128³ gas density."""
from __future__ import annotations

import numpy as np

GRID = 128


def excess_kurtosis(flat: np.ndarray) -> float:
    m = float(flat.mean())
    s = float(flat.std())
    if s < 1e-12:
        return 0.0
    return float(((flat - m) ** 4).mean() / (s**4) - 3.0)


def max_projection_xy(vol: np.ndarray) -> np.ndarray:
    return np.max(vol, axis=2)


def morans_i_6_neighbor(vol: np.ndarray) -> float:
    """Global Moran's I with 6-neighbor weights on interior voxels."""
    x = vol[1:-1, 1:-1, 1:-1].astype(np.float64)
    x = x - x.mean()
    denom = float((x * x).sum())
    if denom < 1e-18:
        return 0.0
    neighbor = (
        vol[0:-2, 1:-1, 1:-1]
        + vol[2:, 1:-1, 1:-1]
        + vol[1:-1, 0:-2, 1:-1]
        + vol[1:-1, 2:, 1:-1]
        + vol[1:-1, 1:-1, 0:-2]
        + vol[1:-1, 1:-1, 2:]
    ).astype(np.float64)
    neighbor = neighbor - neighbor.mean()
    n = x.size
    s0 = 6.0 * n
    return float((n / s0) * (x * neighbor).sum() / denom)


def radial_two_point_profile(field: np.ndarray, max_r: int = 48) -> tuple[np.ndarray, np.ndarray]:
    """Binned two-point correlation ξ(r) on 2D field (Wiener–Khinchin)."""
    delta = field.astype(np.float64)
    delta -= delta.mean()
    power = np.abs(np.fft.fft2(delta)) ** 2
    acf = np.fft.ifft2(power).real
    acf = np.fft.fftshift(acf)
    cy, cx = acf.shape[0] // 2, acf.shape[1] // 2
    center = acf[cy, cx]
    if abs(center) < 1e-18:
        radii = np.arange(1, max_r + 1, dtype=np.float64)
        return radii, np.zeros_like(radii)
    acf /= center

    ys, xs = np.indices(acf.shape)
    dist = np.sqrt((ys - cy) ** 2 + (xs - cx) ** 2)
    radii = np.arange(1, max_r + 1, dtype=np.float64)
    xi = np.zeros_like(radii)
    for i, r in enumerate(radii):
        mask = (dist >= r - 0.5) & (dist < r + 0.5)
        if mask.any():
            xi[i] = float(acf[mask].mean())
    return radii, xi


def correlation_half_length(field: np.ndarray, max_r: int = 48) -> float:
    """Smallest r (pixels) where ξ(r) drops below 0.5; NaN if never."""
    radii, xi = radial_two_point_profile(field, max_r=max_r)
    below = np.where(xi < 0.5)[0]
    if below.size == 0:
        return float(max_r)
    return float(radii[below[0]])


def xi_at_lag(field: np.ndarray, lag: int) -> float:
    _radii, xi = radial_two_point_profile(field, max_r=max(lag + 2, 48))
    idx = max(0, min(lag - 1, len(xi) - 1))
    return float(xi[idx])


def xi_band_mean(field: np.ndarray, r_lo: int, r_hi: int) -> float:
    radii, xi = radial_two_point_profile(field)
    mask = (radii >= r_lo) & (radii <= r_hi)
    if not mask.any():
        return 0.0
    return float(xi[mask].mean())


def box_count_fractal_dim(binary: np.ndarray) -> float:
    """Box-counting dimension on 2D binary mask."""
    sizes = [2, 4, 8, 16, 32, 64]
    counts: list[float] = []
    h, w = binary.shape
    for s in sizes:
        if s > min(h, w):
            continue
        hh, ww = h - h % s, w - w % s
        blocks = binary[:hh, :ww].reshape(hh // s, s, ww // s, s)
        occupied = np.any(blocks, axis=(1, 3))
        counts.append(float(occupied.sum()))
    if len(counts) < 2:
        return 0.0
    log_s = np.log(np.array(sizes[: len(counts)], dtype=np.float64))
    log_c = np.log(np.maximum(counts, 1.0))
    slope = np.polyfit(log_s, log_c, 1)[0]
    return float(-slope)


def coarse_grain_entropy(field_2d: np.ndarray, scale: int, bins: int = 32) -> float:
    """Shannon entropy of block-averaged field (multiscale entropy proxy)."""
    h, w = field_2d.shape
    h2, w2 = h - h % scale, w - w % scale
    if h2 < scale or w2 < scale:
        return 0.0
    blocks = (
        field_2d[:h2, :w2]
        .reshape(h2 // scale, scale, w2 // scale, scale)
        .mean(axis=(1, 3))
    )
    hist, _ = np.histogram(blocks.ravel(), bins=bins, density=True)
    hist = hist[hist > 1e-15]
    return float(-np.sum(hist * np.log(hist)))


def spatial_metrics_for_volume(vol: np.ndarray, p90: float) -> dict[str, float]:
    proj = max_projection_xy(vol)
    mask = proj >= p90
    return {
        "excessKurtosis": excess_kurtosis(vol.ravel()),
        "moransI": morans_i_6_neighbor(vol),
        "xiHalfLength": correlation_half_length(proj),
        "xiR1": xi_at_lag(proj, 1),
        "xiR10": xi_at_lag(proj, 10),
        "xiBand8_16": xi_band_mean(proj, 8, 16),
        "fractalDimP90": box_count_fractal_dim(mask),
        "multiscaleEntropy8": coarse_grain_entropy(proj, 8),
    }
