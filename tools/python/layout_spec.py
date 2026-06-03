"""3840×6480 长卷布局规格 — 供 generate_figures / 导出脚本读取。

详见 docs/competition/LAYOUT_SPEC.md
"""
from __future__ import annotations

from dataclasses import dataclass

# ── 画布 ──
CANVAS_W = 3840
CANVAS_H = 6480
CANVAS_RATIO = CANVAS_H / CANVAS_W  # 1.6875

MARGIN_X = 120
GUTTER = 40
GRID_COLS = 24
CONTENT_W = CANVAS_W - 2 * MARGIN_X  # 3600
PAD_Y = 190
CONTENT_H = 6100  # sections sum; PAD_Y*2 + CONTENT_H = CANVAS_H

# 24 列宽（列间槽 40px，共 23 条槽）
_COL_W = (CONTENT_W - (GRID_COLS - 1) * GUTTER) / GRID_COLS


def col_x(col: int) -> float:
    """列左缘 X（0-based，相对画布）。"""
    if col < 0 or col >= GRID_COLS:
        raise ValueError(f"col must be 0..{GRID_COLS - 1}")
    return MARGIN_X + col * (_COL_W + GUTTER)


def span_w(cols: int) -> float:
    """连续 cols 列的总宽度（含列间槽）。"""
    if cols < 1 or cols > GRID_COLS:
        raise ValueError("cols out of range")
    return cols * _COL_W + (cols - 1) * GUTTER


# ── 颜色（与 LAYOUT_SPEC 一致）──
COLORS = {
    "bg": "#03030A",
    "border": "#1E2B48",
    "text": "#F5F9FF",
    "text_muted": "#8FA3C4",
    "low_density": "#2A88FF",
    "mid_density": "#9EEFFF",
    "high_density": "#FFCC66",
    "peak_density": "#FF3D3D",
    "accent_orange": "#FF6B2C",
    "accent_cyan": "#4EC4FF",
}

# ── 字号（px @1x，导出 2x 时 ×2）──
FONT = {
    "h1": 80,
    "h2": 40,
    "section": 30,
    "body": 24,
    "caption": 18,
    "subtitle": 34,
}

# ── 分区 ──
@dataclass(frozen=True)
class SectionBox:
    id: str
    title: str
    y: int
    h: int

    @property
    def y_canvas(self) -> int:
        return PAD_Y + self.y

    @property
    def y2(self) -> int:
        return self.y + self.h


SECTIONS: tuple[SectionBox, ...] = (
    SectionBox("01", "宇宙网诞生记", 0, 1400),
    SectionBox("02", "100 步演化全景", 1400, 1000),
    SectionBox("03", "统计分析", 2400, 1100),
    SectionBox("04", "统计空间验证", 3500, 1000),
    SectionBox("05", "关键科学发现", 4500, 900),
    SectionBox("06", "整体流程图", 5400, 700),
)

# Section 01 关键矩形（内容坐标系 Y）
S01 = {
    "title": (MARGIN_X, 80),
    "info_cards": (MARGIN_X, 300, 420, 520),
    "hero": (550, 120, 3170, 1000),
    "colorbar": (3600, 250, 40, 500),
}

# Section 02 五帧 X（画布坐标）
S02_FRAMES = [
    ("t1", 120),
    ("t25", 710),
    ("t50", 1300),
    ("t75", 1890),
    ("t100", 2480),
]
S02_FRAME_SIZE = (540, 320)
S02_FRAME_GAP = 50

# 导出 DPI：3840px 宽 @ 10.24" → ~375 dpi；matplotlib 常用 figsize 英寸
EXPORT_DPI = 200
FIG_W_IN = CANVAS_W / EXPORT_DPI
FIG_H_IN = CANVAS_H / EXPORT_DPI
