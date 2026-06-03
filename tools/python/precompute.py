"""Precompute per-timestep density statistics and log-spaced histograms."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
NYX = ROOT / "Nyx"
OUT = ROOT / "public" / "stats"
GRID = 128
BIN_COUNT = 128
TIMESTEPS = 100


def load_volume(path: Path) -> np.ndarray:
    flat = np.fromfile(path, dtype="<f4")
    return flat.reshape((GRID, GRID, GRID), order="C")


def skewness(a: np.ndarray) -> float:
    m = a.mean()
    s = a.std()
    if s < 1e-12:
        return 0.0
    return float(((a - m) ** 3).mean() / (s**3))


def main() -> int:
    if not NYX.exists():
        print(f"Missing data directory: {NYX}", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    all_mins: list[float] = []
    all_maxs: list[float] = []

    for t in range(TIMESTEPS):
        path = NYX / f"{t:04d}.dat"
        if not path.exists():
            print(f"Missing {path}", file=sys.stderr)
            return 1
        vol = load_volume(path)
        all_mins.append(float(vol.min()))
        all_maxs.append(float(vol.max()))

    global_min = float(min(all_mins))
    global_max = float(max(all_maxs))
    log_edges = np.logspace(
        np.log10(global_min), np.log10(global_max), BIN_COUNT + 1
    ).tolist()

    timesteps_stats = []
    histograms: list[list[float]] = []

    for t in range(TIMESTEPS):
        path = NYX / f"{t:04d}.dat"
        vol = load_volume(path)
        flat = vol.ravel()
        p01, p50, p90, p99, p999 = np.percentile(flat, [1, 50, 90, 99, 99.9])
        counts, _ = np.histogram(flat, bins=log_edges)
        hist = (counts / counts.sum()).tolist()
        histograms.append(hist)
        tail_above = float((flat >= p99).mean())
        tail_below = float((flat <= p01).mean())
        total_mass = float(flat.sum())
        mass_above = float(flat[flat >= p99].sum()) if total_mass > 0 else 0.0
        mass_below = float(flat[flat <= p01].sum()) if total_mass > 0 else 0.0
        timesteps_stats.append(
            {
                "timestep": t,
                "min": float(flat.min()),
                "max": float(flat.max()),
                "mean": float(flat.mean()),
                "std": float(flat.std()),
                "skewness": skewness(flat),
                "p01": float(p01),
                "p50": float(p50),
                "p90": float(p90),
                "p99": float(p99),
                "p999": float(p999),
                "tailMassAboveP99": tail_above,
                "tailMassBelowP01": tail_below,
                "massFractionAboveP99": mass_above / total_mass,
                "massFractionBelowP01": mass_below / total_mass,
            }
        )
        print(f"Processed timestep {t:04d}")

    payload = {
        "globalMin": global_min,
        "globalMax": global_max,
        "binCount": BIN_COUNT,
        "logBinEdges": log_edges,
        "timesteps": timesteps_stats,
        "histograms": histograms,
    }
    timeline_path = OUT / "timeline.json"
    timeline_path.write_text(json.dumps(payload), encoding="utf-8")
    print(f"Wrote {timeline_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
