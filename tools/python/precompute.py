"""Precompute per-timestep density statistics and log-spaced histograms."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

from spatial_stats import spatial_metrics_for_volume

ROOT = Path(__file__).resolve().parents[2]
NYX = ROOT / "Nyx"
OUT = ROOT / "public" / "stats"
GRID = 128
VOXEL_COUNT = GRID**3
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

    vol0 = load_volume(NYX / "0000.dat")
    flat0 = vol0.ravel()
    void_rho_ref = float(np.percentile(flat0, 10))
    void_p01_ref = float(np.percentile(flat0, 1))

    timesteps_stats = []
    histograms: list[list[float]] = []

    for t in range(TIMESTEPS):
        path = NYX / f"{t:04d}.dat"
        vol = load_volume(path)
        flat = vol.ravel()
        p01, p10, p25, p50, p75, p90, p99, p999 = np.percentile(
            flat, [1, 10, 25, 50, 75, 90, 99, 99.9]
        )
        counts, _ = np.histogram(flat, bins=log_edges)
        hist = (counts / counts.sum()).tolist()
        histograms.append(hist)
        tail_above = float((flat >= p99).mean())
        tail_below = float((flat <= p01).mean())
        tail_filament = float(((flat >= p90) & (flat <= p99)).mean())
        total_mass = float(flat.sum())
        mass_above = float(flat[flat >= p99].sum()) if total_mass > 0 else 0.0
        mass_below = float(flat[flat <= p01].sum()) if total_mass > 0 else 0.0
        spatial = spatial_metrics_for_volume(vol, float(p90))
        timesteps_stats.append(
            {
                "timestep": t,
                "min": float(flat.min()),
                "max": float(flat.max()),
                "mean": float(flat.mean()),
                "std": float(flat.std()),
                "skewness": skewness(flat),
                "p01": float(p01),
                "p10": float(p10),
                "p25": float(p25),
                "p50": float(p50),
                "p75": float(p75),
                "p90": float(p90),
                "p99": float(p99),
                "p999": float(p999),
                "tailMassAboveP99": tail_above,
                "tailMassBelowP01": tail_below,
                "tailMassFilament90_99": tail_filament,
                "tailMassBelowP10": float((flat <= p10).mean()),
                "tailMassBelowP25": float((flat <= p25).mean()),
                "voidFractionBelowT0P10": float((flat <= void_rho_ref).mean()),
                "voidFractionBelowT0P01": float((flat <= void_p01_ref).mean()),
                "massFractionAboveP99": mass_above / total_mass,
                "massFractionBelowP01": mass_below / total_mass,
                **spatial,
            }
        )
        print(f"Processed timestep {t:04d}")

    payload = {
        "globalMin": global_min,
        "globalMax": global_max,
        "binCount": BIN_COUNT,
        "logBinEdges": log_edges,
        "histogramMeta": {
            "normalization": "per_timestep_probability_mass",
            "N_per_step": VOXEL_COUNT,
            "formula": "hist[b] = count_b / sum(counts) for the same timestep",
            "comparability": (
                "Each timestep sums to 1.0; cross-step comparison is valid for shape, "
                "not for absolute counts."
            ),
            "bin_edges": "global log-spaced edges from min/max over all 100 steps",
            "voidReference": {
                "rho_p10_t0": void_rho_ref,
                "rho_p01_t0": void_p01_ref,
                "description": "Fixed t=0 thresholds for voidFractionBelowT0*",
            },
        },
        "dataScope": {
            "simulation": "Nyx cosmological hydrodynamics (AMReX)",
            "includedFields": ["baryon_gas_density"],
            "excludedFields": ["dark_matter_nbody"],
            "note": (
                "Competition package ships uniform 128³ gas .dat only; "
                "no per-step dark-matter particle or DM density grid."
            ),
        },
        "timesteps": timesteps_stats,
        "histograms": histograms,
    }
    timeline_path = OUT / "timeline.json"
    timeline_path.write_text(json.dumps(payload), encoding="utf-8")
    print(f"Wrote {timeline_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
