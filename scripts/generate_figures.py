"""Generate static figures for tasks 1–4 into docs/figures/."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
NYX = ROOT / "Nyx"
STATS = ROOT / "public" / "stats" / "timeline.json"
OUT = ROOT / "docs" / "figures"
GRID = 128
REP_STEPS = [0, 25, 50, 75, 99]


def load_volume(path: Path) -> np.ndarray:
    flat = np.fromfile(path, dtype="<f4")
    return flat.reshape((GRID, GRID, GRID), order="C")


def slice_figure(vol: np.ndarray, timestep: int, out: Path) -> None:
    mid = GRID // 2
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    slices = [
        (vol[mid, :, :], "x = mid"),
        (vol[:, mid, :], "y = mid"),
        (vol[:, :, mid], "z = mid"),
    ]
    vmin, vmax = np.percentile(vol, [2, 99.5])
    for ax, (sl, title) in zip(axes, slices):
        im = ax.imshow(sl.T, origin="lower", cmap="magma", vmin=vmin, vmax=vmax)
        ax.set_title(title)
        ax.axis("off")
    fig.colorbar(im, ax=axes, fraction=0.02, label="density")
    fig.suptitle(f"Nyx gas density — timestep {timestep}")
    fig.tight_layout()
    fig.savefig(out, dpi=150, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    if not STATS.exists():
        print("Run precompute first", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    timeline = json.loads(STATS.read_text(encoding="utf-8"))
    edges = timeline["logBinEdges"]
    centers = [np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)]

    for t in REP_STEPS:
        vol_path = NYX / f"{t:04d}.dat"
        vol_png = OUT / f"task1_vol_t{t:04d}.png"
        slice_png = OUT / f"task1_slice_t{t:04d}.png"
        if not vol_png.exists():
            vol = load_volume(vol_path)
            slice_figure(vol, t, slice_png)
            print(f"Slice fallback (no vtk capture): {slice_png}")
        else:
            print(f"Using vtk volume render: {vol_png}")

    # Task 3 overlay
    fig, ax = plt.subplots(figsize=(8, 5))
    colors = plt.cm.viridis(np.linspace(0, 1, len(REP_STEPS)))
    for t, c in zip(REP_STEPS, colors):
        hist = timeline["histograms"][t]
        ax.plot(centers, hist, label=f"t={t}", color=c, lw=1.8)
    ax.set_xscale("log")
    ax.set_xlabel("Density")
    ax.set_ylabel("Fraction")
    ax.set_title("Log-spaced density histogram evolution")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "task3_hist_overlay.png", dpi=150)
    plt.close(fig)

    # Task 3 metrics
    steps = timeline["timesteps"]
    ts = [s["timestep"] for s in steps]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(ts, [s["mean"] for s in steps], label="mean", color="#5b8def")
    ax.plot(ts, [s["p99"] for s in steps], label="p99", color="#f0c040")
    ax.plot(ts, [s["std"] for s in steps], label="std", color="#6ad49b")
    ax.set_xlabel("Timestep")
    ax.set_ylabel("Value")
    ax.set_title("Density statistics over 100 timesteps")
    ax.legend()
    fig.tight_layout()
    fig.savefig(OUT / "task3_metrics_timeline.png", dpi=150)
    plt.close(fig)

    # Task 4: top 1% spatial projection (t=99)
    vol = load_volume(NYX / "0099.dat")
    flat = vol.ravel()
    p99 = np.percentile(flat, 99)
    mask = vol >= p99
    xy = mask.max(axis=2).astype(float)
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(xy.T, origin="lower", cmap="hot")
    ax.set_title("Top 1% density voxels — max projection (t=99)")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "task4_brush_top1.png", dpi=150)
    plt.close(fig)

    print(f"Figures written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
