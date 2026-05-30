"""Shared matplotlib styling for NyxViz submission figures."""
from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap
from matplotlib.figure import Figure

FIG_DPI = 200
VIZ_BG = "#0a0e1a"
PANEL_BG = "#0f1424"
GRID_ALPHA = 0.22

THEME = {
    "purple": "#7c6cf0",
    "cyan": "#3dd6c6",
    "blue": "#5b9bd5",
    "gold": "#f5c842",
    "coral": "#e87a5a",
    "muted": "#9aa3b8",
}

COSMIC_STOPS = [
    (0.0, (0.02, 0.03, 0.10)),
    (0.15, (0.04, 0.08, 0.28)),
    (0.35, (0.12, 0.20, 0.48)),
    (0.55, (0.24, 0.55, 0.72)),
    (0.72, (0.55, 0.42, 0.78)),
    (0.85, (0.85, 0.65, 0.42)),
    (1.0, (0.98, 0.92, 0.78)),
]

COSMIC_CMAP = LinearSegmentedColormap.from_list("cosmic", COSMIC_STOPS, N=256)


def apply_dark_theme() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": VIZ_BG,
            "axes.facecolor": PANEL_BG,
            "axes.edgecolor": "#2a3348",
            "axes.labelcolor": THEME["muted"],
            "axes.titlecolor": "#e6edf3",
            "xtick.color": THEME["muted"],
            "ytick.color": THEME["muted"],
            "text.color": "#e6edf3",
            "grid.color": "#3a4558",
            "grid.alpha": GRID_ALPHA,
            "legend.facecolor": PANEL_BG,
            "legend.edgecolor": "#2a3348",
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "savefig.facecolor": VIZ_BG,
            "savefig.edgecolor": VIZ_BG,
        }
    )


def style_axes(ax) -> None:
    ax.set_facecolor(PANEL_BG)
    ax.grid(True, alpha=GRID_ALPHA)


def save_figure(
    fig: Figure,
    path: Path | str,
    *,
    has_suptitle: bool = False,
    pad: float = 0.14,
) -> None:
    """Save with bbox_inches=tight so titles and suptitles are not clipped."""
    if has_suptitle:
        fig.tight_layout(rect=[0, 0, 1, 0.90])
    else:
        fig.tight_layout()
    fig.savefig(
        path,
        dpi=FIG_DPI,
        bbox_inches="tight",
        pad_inches=pad,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
    )
    plt.close(fig)


def global_projection_domain(timeline: dict) -> tuple[float, float]:
    mins = [s["p01"] for s in timeline["timesteps"]]
    maxs = [s["p99"] for s in timeline["timesteps"]]
    return float(min(mins)), float(max(maxs))


def log_norm_unit(values: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    lo = np.log10(max(vmin, 1e-6))
    hi = np.log10(max(vmax, 1e-6))
    span = hi - lo if hi > lo else 1.0
    v = np.clip(values, vmin, vmax)
    return np.clip((np.log10(np.maximum(v, 1e-6)) - lo) / span, 0.0, 1.0)
