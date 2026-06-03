"""Export 3840×6480 grayscale wireframe from LAYOUT_SPEC (no real data)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

from viz_style import apply_dark_theme
from layout_spec import (
    CANVAS_H,
    CANVAS_W,
    COLORS,
    CONTENT_H,
    MARGIN_X,
    PAD_Y,
    S01,
    S02_FRAMES,
    S02_FRAME_SIZE,
    SECTIONS,
)

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs" / "figures" / "wireframe_3840x6480.png"


def _rect(ax, x, y, w, h, label: str, *, content_y: bool = True) -> None:
    yc = y + PAD_Y if content_y else y
    r = mpatches.Rectangle(
        (x, yc),
        w,
        h,
        linewidth=1.2,
        edgecolor="#6a7a9a",
        facecolor="#1a2030",
        alpha=0.85,
    )
    ax.add_patch(r)
    ax.text(
        x + w / 2,
        yc + h / 2,
        label,
        ha="center",
        va="center",
        fontsize=9,
        color="#c8d4e8",
        wrap=True,
    )


def main() -> int:
    apply_dark_theme()
    fig, ax = plt.subplots(figsize=(CANVAS_W / 100, CANVAS_H / 100), dpi=100)
    ax.set_xlim(0, CANVAS_W)
    ax.set_ylim(CANVAS_H, 0)
    ax.set_facecolor(COLORS["bg"])
    fig.patch.set_facecolor(COLORS["bg"])
    ax.axis("off")

    for sec in SECTIONS:
        y0 = PAD_Y + sec.y
        band = mpatches.Rectangle(
            (MARGIN_X, y0),
            CANVAS_W - 2 * MARGIN_X,
            sec.h,
            linewidth=2,
            edgecolor="#3d5080",
            facecolor="none",
            linestyle="--",
        )
        ax.add_patch(band)
        ax.text(
            MARGIN_X + 8,
            y0 + 28,
            f"{sec.id} · {sec.title}  (H={sec.h})",
            fontsize=14,
            color="#8fa3c4",
            va="top",
        )

    tx, ty = S01["title"]
    _rect(ax, tx, ty, 2000, 120, "主标题 80px + 副标题 34px", content_y=False)

    cx, cy, cw, ch = S01["info_cards"]
    _rect(ax, cx, cy, cw, ch, "信息卡 420×520\n3×140", content_y=False)
    for i in range(3):
        _rect(ax, cx, cy + 20 + i * 150, cw, 140, f"卡{i + 1}", content_y=False)

    hx, hy, hw, hh = S01["hero"]
    _rect(ax, hx, hy, hw, hh, "主宇宙图 3170×1000", content_y=False)

    bx, by, bw, bh = S01["colorbar"]
    _rect(ax, bx, by, bw, bh, "色标 40×500", content_y=False)

    fw, fh = S02_FRAME_SIZE
    for name, fx in S02_FRAMES:
        fy = PAD_Y + SECTIONS[1].y + 140
        _rect(ax, fx, fy - PAD_Y, fw, fh, f"{name}\n{fw}×{fh}", content_y=True)

    _rect(ax, 120, 2600 - PAD_Y, 1600, 600, "直方图 1600×600", content_y=True)
    for i in range(3):
        _rect(ax, 1850 + i * (520 + 40), 2700 - PAD_Y, 520, 300, f"趋势{i + 1}", content_y=True)
    for i in range(4):
        col, row = i % 2, i // 2
        _rect(
            ax,
            1850 + col * (370 + 40),
            3050 - PAD_Y + row * 200,
            370,
            180,
            f"KPI{i + 1}",
            content_y=True,
        )

    for row, tag in enumerate(["Top 1%", "Bottom 1%"]):
        y_row = PAD_Y + SECTIONS[3].y + 120 + row * 440
        x = MARGIN_X
        w_total = CANVAS_W - 2 * MARGIN_X
        parts = [0.15, 0.05, 0.35, 0.45]
        labels = ["直方 15%", "→ 5%", "映射 35%", "放大 45%"]
        for ratio, lab in zip(parts, labels):
            ww = w_total * ratio
            r = mpatches.Rectangle(
                (x, y_row),
                ww,
                420,
                linewidth=1,
                edgecolor="#6a7a9a",
                facecolor="#1a2030",
                alpha=0.85,
            )
            ax.add_patch(r)
            ax.text(x + ww / 2, y_row + 210, f"{tag}\n{lab}", ha="center", va="center", fontsize=8, color="#c8d4e8")
            x += ww

    y5 = PAD_Y + SECTIONS[4].y + 80
    for i in range(4):
        _rect(ax, MARGIN_X + i * (860 + 40), y5 - PAD_Y, 860, 650, f"发现{i + 1}", content_y=True)

    y6 = PAD_Y + SECTIONS[5].y + 120
    nodes = [
        "Nyx",
        "体渲染",
        "统计",
        "刷选",
        "映射",
        "验证",
        "发现",
    ]
    x = 120
    for n in nodes:
        _rect(ax, x, y6 - PAD_Y, 420, 220, n, content_y=True)
        x += 420 + 80

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=100, bbox_inches="tight", pad_inches=0, facecolor=COLORS["bg"])
    plt.close(fig)
    print(f"Wireframe: {OUT} ({CANVAS_W}×{CANVAS_H} target)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
