"""Shared paths and figure lists for report / answer-sheet docx export."""
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "report"
FIGURES = ROOT / "docs" / "figures"

TASK_MD = [
    "task1_volume.md",
    "task2_evolution.md",
    "task3_histogram.md",
    "task4_brush.md",
]

TASK_IMAGES: dict[str, list[str]] = {
    "task1_volume.md": [
        "task1_vol_strip.png",
        "task1_vol_t0000.png",
        "task1_vol_t0050.png",
        "task1_vol_t0099.png",
    ],
    "task2_evolution.md": [
        "task2_evolution_story.png",
        "task3_hist_overlay.png",
        "task1_vol_t0000.png",
        "task1_vol_t0099.png",
    ],
    "task3_histogram.md": [
        "task3_hist_overlay.png",
        "task3_metrics_timeline.png",
        "task3_evolution_metrics.png",
        "task3_peak_drift.png",
    ],
    "task4_brush.md": [
        "task4_spatial_to_stats.png",
        "task4_brush_triptych.png",
        "task4_hist_brush_top1.png",
        "task4_brush_top1.png",
    ],
}

MAX_IMAGES_PER_TASK = 5


def resolve_image(name: str) -> Path | None:
    candidates = [
        name,
        name.replace("task1_vol_", "task1_"),
        name.replace("task1_vol_", "task1_slice_"),
    ]
    for c in candidates:
        p = FIGURES / c
        if p.exists():
            return p
    return None


def resolve_task_images(md_name: str) -> list[Path]:
    paths: list[Path] = []
    for name in TASK_IMAGES.get(md_name, [])[:MAX_IMAGES_PER_TASK]:
        p = resolve_image(name)
        if p:
            paths.append(p)
    return paths
