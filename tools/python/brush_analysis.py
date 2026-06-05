"""Brush threshold comparison, P88 sensitivity, FP/FN, and scan timing."""
from __future__ import annotations

import json
import time
from pathlib import Path

import numpy as np

from spatial_to_stats import filament_density_band, load_volume_dat

try:
    from validation_suite import brush_sample_recall
except ImportError:
    brush_sample_recall = None  # type: ignore[assignment,misc]

ROOT = Path(__file__).resolve().parents[2]
GRID = 128
VOXEL_COUNT = GRID**3


def max_projection(vol: np.ndarray, axis: str) -> np.ndarray:
    if axis == "xy":
        return np.max(vol, axis=2)
    if axis == "xz":
        return np.max(vol, axis=1)
    if axis == "yz":
        return np.max(vol, axis=0)
    raise ValueError(axis)


def brush_scan_ms(
    flat: np.ndarray,
    lo: float,
    hi: float,
    *,
    max_points: int = 8000,
    count_all: bool = False,
) -> dict:
    """Mirror brushScan.worker.ts loop; return timing ms."""
    stride = 2 if max_points < 20000 else 1
    vol = flat.reshape((GRID, GRID, GRID), order="C")
    t0 = time.perf_counter()
    n_hit = 0
    points = 0
    outer = False
    for x in range(0, GRID, stride):
        if outer:
            break
        x_off = x * GRID * GRID
        for y in range(0, GRID, stride):
            if outer:
                break
            y_off = x_off + y * GRID
            for z in range(0, GRID, stride):
                d = flat[y_off + z]
                if lo <= d <= hi:
                    n_hit += 1
                    points += 1
                    if not count_all and points >= max_points:
                        outer = True
                        break
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return {
        "elapsedMs": round(elapsed_ms, 2),
        "stride": stride,
        "maxPoints": max_points,
        "hitsSampled": n_hit,
        "countAll": count_all,
    }


def filament_proxy_3d(vol: np.ndarray, proj_pct: float = 88.0) -> tuple[np.ndarray, float, float]:
    """3D mask: XY bright-ridge columns with ρ ≥ band_lo."""
    lo, hi, mask2d = filament_density_band(vol, proj_percentile=proj_pct)
    proxy = np.zeros(vol.shape, dtype=bool)
    for x in range(GRID):
        for y in range(GRID):
            if mask2d[x, y]:
                proxy[x, y, :] = vol[x, y, :] >= lo
    return proxy, lo, hi


def isolated_brush_stats(brush_vol: np.ndarray) -> tuple[int, int]:
    """Brush voxels with ≤1 brush neighbor (6-connectivity) — likely noise/isolated."""
    isolated = 0
    total = 0
    offsets = ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1))
    for x in range(GRID):
        for y in range(GRID):
            for z in range(GRID):
                if not brush_vol[x, y, z]:
                    continue
                total += 1
                nb = 0
                for dx, dy, dz in offsets:
                    nx, ny, nz = x + dx, y + dy, z + dz
                    if 0 <= nx < GRID and 0 <= ny < GRID and 0 <= nz < GRID and brush_vol[nx, ny, nz]:
                        nb += 1
                if nb <= 1:
                    isolated += 1
    return isolated, total


def threshold_comparison(vol: np.ndarray, s99: dict) -> list[dict]:
    flat = vol.ravel()
    total_mass = float(flat.sum()) or 1.0
    p95 = float(np.percentile(flat, 95))
    p90 = float(s99["p90"])
    p99 = float(s99["p99"])
    filament_mask = (flat >= p90) & (flat <= p99)
    specs = [
        ("p95 (Top 5%)", p95, None, "更宽右尾，易混入 IGM 过渡区"),
        ("90–99% 纤维带", p90, p99, "交互预设纤维刷选 ρ∈[p90,p99]"),
        ("p99 (Top 1%)", p99, None, "默认 Top 1% 刷选（交互预设）"),
        ("p99.9 (Top 0.1%)", float(s99["p999"]), None, "更极端节点核，体积份额更小"),
    ]
    rows = []
    for label, thr_lo, thr_hi, note in specs:
        if thr_hi is None:
            mask = flat >= thr_lo
            rho_label = thr_lo
        else:
            mask = (flat >= thr_lo) & (flat <= thr_hi)
            rho_label = thr_lo
        rows.append(
            {
                "label": label,
                "rhoMin": thr_lo,
                "rhoMax": thr_hi,
                "volumePct": float(mask.mean()) * 100,
                "massPct": float(flat[mask].sum()) / total_mass * 100,
                "note": note,
            }
        )
    return rows


def custom_brush_error_study(flat: np.ndarray, s99: dict, *, max_points: int = 8000) -> list[dict]:
    """Quantify KPI underestimate for non-preset drag ranges (mirrors UI maxPoints=8000)."""
    specs = [
        ("Top 1% 区间（对照）", float(s99["p99"]), float(s99["max"])),
        ("纤维 90–99% 区间（对照）", float(s99["p90"]), float(s99["p99"])),
        ("自定义：p50–p99", float(s99["p50"]), float(s99["p99"])),
        ("自定义：p75–max", float(s99["p75"]), float(s99["max"])),
        ("自定义：p01–p90", float(s99["p01"]), float(s99["p90"])),
        ("自定义：p25–p75", float(s99["p25"]), float(s99["p75"])),
    ]
    rows = []
    for label, lo, hi in specs:
        true_n = int(((flat >= lo) & (flat <= hi)).sum())
        early = brush_scan_ms(flat, lo, hi, max_points=max_points)
        reported = int(early["hitsSampled"])
        if brush_sample_recall is not None:
            rec = brush_sample_recall(flat, lo, hi, max_points=max_points)
            unique_found = int(rec["uniqueTrueFound"])
            recall_pct = float(rec["recallVsTrue"]) * 100
        else:
            unique_found = reported
            recall_pct = (unique_found / true_n * 100) if true_n else 0.0
        rows.append(
            {
                "label": label,
                "rhoRange": [lo, hi],
                "trueVoxels": true_n,
                "reportedCount": reported,
                "reportedOverTruePct": (reported / true_n * 100) if true_n else 0.0,
                "uniqueTrueFound": unique_found,
                "recallVsTruePct": recall_pct,
                "maxPoints": max_points,
                "stride": early["stride"],
            }
        )
    return rows


def p88_sensitivity(vol: np.ndarray) -> list[dict]:
    rows = []
    for pct in (85, 88, 90, 92, 95):
        lo, hi, mask = filament_density_band(vol, proj_percentile=pct)
        rows.append(
            {
                "projPercentile": pct,
                "ridgePixels": int(mask.sum()),
                "ridgePixelPct": float(mask.mean()) * 100,
                "densityBand": [lo, hi],
            }
        )
    return rows


def fp_fn_metrics(vol: np.ndarray, s99: dict, proj_pct: float = 88.0) -> dict:
    flat = vol.ravel()
    brush = flat >= float(s99["p99"])
    proxy, lo, hi = filament_proxy_3d(vol, proj_pct)
    proxy_flat = proxy.ravel()

    tp = int((brush & proxy_flat).sum())
    fp = int((brush & ~proxy_flat).sum())
    fn = int((~brush & proxy_flat).sum())
    brush_n = int(brush.sum())
    proxy_n = int(proxy_flat.sum())

    brush_vol = brush.reshape(vol.shape)
    isolated, _ = isolated_brush_stats(brush_vol)

    return {
        "projPercentile": proj_pct,
        "filamentBand": [lo, hi],
        "brushVoxels": brush_n,
        "filamentProxyVoxels": proxy_n,
        "truePositive": tp,
        "falsePositive": fp,
        "falseNegative": fn,
        "precision": tp / (tp + fp) if (tp + fp) else 0.0,
        "recall": tp / (tp + fn) if (tp + fn) else 0.0,
        "fpRateInBrush": fp / brush_n if brush_n else 0.0,
        "fnRateInProxy": fn / proxy_n if proxy_n else 0.0,
        "isolatedHighDensityInBrush": isolated,
        "isolatedRateInBrush": isolated / brush_n if brush_n else 0.0,
    }


def analyze_timestep(vol_path: Path, s99: dict) -> dict:
    vol = load_volume_dat(vol_path)
    flat = vol.ravel()
    bench = {
        "top1_earlyExit": brush_scan_ms(
            flat, float(s99["p99"]), float(s99["max"]), max_points=8000
        ),
        "top1_fullCount": brush_scan_ms(
            flat, float(s99["p99"]), float(s99["max"]), max_points=VOXEL_COUNT, count_all=True
        ),
        "filament_earlyExit": brush_scan_ms(
            flat, float(s99["p90"]), float(s99["p99"]), max_points=8000
        ),
    }
    if brush_sample_recall is not None:
        bench["sampleRecall"] = brush_sample_recall(
            flat, float(s99["p99"]), float(s99["max"]), max_points=8000
        )
        bench["customBrushErrors"] = custom_brush_error_study(flat, s99, max_points=8000)
    return {
        "thresholds": threshold_comparison(vol, s99),
        "p88Sweep": p88_sensitivity(vol),
        "fpFnDefault": fp_fn_metrics(vol, s99, 88.0),
        "benchmark": bench,
    }


def export_brush_validation(timeline: dict, out: Path) -> dict:
    s99 = timeline["timesteps"][99]
    vol_path = ROOT / "Nyx" / "0099.dat"
    payload = {
        "timestep": 99,
        "note": (
            "Top 1% uses empirical p99 (no halo Δ200 on this 128³ gas subvolume). "
            "Filament proxy = P88 XY ridge columns with ρ≥band_lo."
        ),
        **analyze_timestep(vol_path, s99),
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return payload
