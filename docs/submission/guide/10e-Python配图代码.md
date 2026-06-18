# 10e · Python 配图代码

[← 10 答辩代码讲解](./10-答辩代码讲解.md) · [← 主索引](../NyxViz_零基础完全解读.md)

---

## precompute.py — load_volume

**路径**：[`tools/python/precompute.py`](../../../tools/python/precompute.py)

**职责**：读取单步 .dat 为 numpy 128³。

**为什么选这段**：统计真源生成入口。

```1:45:tools/python/precompute.py
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
```

**输入 / 输出**：.dat → ndarray

**答辩 30 秒**：和前端一样 fromfile float32，reshape 128³ 后算 mean/std/分位数。
## precompute.py — 直方图分箱

**路径**：[`tools/python/precompute.py`](../../../tools/python/precompute.py)

**职责**：log 域 128 bins 概率质量。

**为什么选这段**：任务三 JSON 字段来源。

```80:130:tools/python/precompute.py
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
```

**输入 / 输出**：体数据 → histogram + logBinEdges

**答辩 30 秒**：每步把体素分到 log 等距 bin，存概率质量供 D3 直接画。
## spatial_to_stats.py

**路径**：[`tools/python/spatial_to_stats.py`](../../../tools/python/spatial_to_stats.py)

**职责**：空间统计与 P88 反查。

**为什么选这段**：task2-spatial 静态图。

```1:50:tools/python/spatial_to_stats.py
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
```

**输入 / 输出**：体数据 → 空间指标 JSON/图

**答辩 30 秒**：从亮脊投影反查密度带，生成空间验证配图。
## brush_analysis.py

**路径**：[`tools/python/brush_analysis.py`](../../../tools/python/brush_analysis.py)

**职责**：离线刷选召回/精确率。

**为什么选这段**：task4-validate KPI。

```1:55:tools/python/brush_analysis.py
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
```

**输入 / 输出**：体数据 + 阈值 → brush_validation.json

**答辩 30 秒**：Top 1% 密度集与 filament 几何代理对比，得到召回 100%、精确率 27.6%。
## render_spec.py

**路径**：[`tools/python/render_spec.py`](../../../tools/python/render_spec.py)

**职责**：导出 render_spec.json 相机/光照。

**为什么选这段**：与前端 renderSpec.ts 对齐。

```1:50:tools/python/render_spec.py
"""Volume render spec mirrored from src/volume/renderSpec.ts for docs and figures."""
from __future__ import annotations

import json
import math
from pathlib import Path

DOMAIN_LENGTH = 14.245
GRID = 128
SPACING = DOMAIN_LENGTH / GRID
VIEW_MARGIN = 0.88
CAMERA_DISTANCE_FACTOR = 1.75
CAMERA_OFFSET = (0.92, 0.78, 0.68)
CAPTURE_CAMERA_ZOOM = 1.24
CAPTURE_ASPECT = 1920 / 1080

COSMIC_COLOR_STOPS = [
    (0.0, (0.02, 0.03, 0.10)),
    (0.15, (0.04, 0.08, 0.28)),
    (0.35, (0.12, 0.20, 0.48)),
    (0.55, (0.24, 0.55, 0.72)),
    (0.72, (0.55, 0.42, 0.78)),
    (0.85, (0.85, 0.65, 0.42)),
    (1.0, (0.98, 0.92, 0.78)),
]

CINEMATIC_COLOR_STOPS = [
    (0.0, (0.01, 0.02, 0.06)),
    (0.12, (0.02, 0.04, 0.12)),
    (0.25, (0.04, 0.07, 0.20)),
    (0.45, (0.15, 0.22, 0.55)),
    (0.65, (0.35, 0.48, 0.78)),
    (0.80, (0.95, 0.72, 0.35)),
    (0.88, (1.0, 0.82, 0.42)),
    (0.92, (1.0, 0.90, 0.58)),
    (0.96, (1.0, 0.96, 0.86)),
    (1.0, (1.0, 1.0, 0.96)),
]

COSMIC_OPACITY_STOPS = [
    (0.0, 0.0),
    (0.12, 0.02),
    (0.35, 0.06),
    (0.55, 0.14),
    (0.72, 0.32),
    (0.88, 0.65),
    (1.0, 0.95),
]

CINEMATIC_OPACITY_STOPS = [
```

**输入 / 输出**：常量 → public/stats/render_spec.json

**答辩 30 秒**：Python 与 TypeScript 各一份常量，保证截图与网页相机一致。
## projection_render.py

**路径**：[`tools/python/projection_render.py`](../../../tools/python/projection_render.py)

**职责**：matplotlib XY 最大密度投影。

**为什么选这段**：Word 空间配图。

```1:55:tools/python/projection_render.py
"""2D max-projection rendering aligned with src/viz/colormap.ts."""
from __future__ import annotations

import numpy as np

from viz_style import COSMIC_CMAP, global_projection_domain, log_norm_unit


def render_projection_rgb(
    proj: np.ndarray,
    vmin: float,
    vmax: float,
    brush_lo: float | None = None,
    brush_hi: float | None = None,
) -> np.ndarray:
    """Return H×W×3 float RGB in [0,1]."""
    h, w = proj.shape
    norm = log_norm_unit(proj, vmin, vmax)
    rgb = COSMIC_CMAP(norm)[:, :, :3]
    if brush_lo is not None and brush_hi is not None:
        mask = (proj >= brush_lo) & (proj <= brush_hi)
        gold = np.array([0.96, 0.78, 0.26])
        rgb[mask] = rgb[mask] * 0.25 + gold * 0.75
    return rgb


def max_projection(vol: np.ndarray, axis: str) -> np.ndarray:
    if axis == "xy":
        return np.max(vol, axis=2)
    if axis == "xz":
        return np.max(vol, axis=1)
    if axis == "yz":
        return np.max(vol, axis=0)
    raise ValueError(axis)


def render_axis_projection(
    vol: np.ndarray,
    timeline: dict,
    axis: str,
    brush_lo: float | None = None,
    brush_hi: float | None = None,
) -> np.ndarray:
    proj = max_projection(vol, axis)
    vmin, vmax = global_projection_domain(timeline)
    return render_projection_rgb(proj, vmin, vmax, brush_lo, brush_hi)


def render_xy_projection(
    vol: np.ndarray,
    timeline: dict,
    brush_lo: float | None = None,
    brush_hi: float | None = None,
) -> np.ndarray:
    return render_axis_projection(vol, timeline, "xy", brush_lo, brush_hi)
```

**输入 / 输出**：.dat → PNG 投影

**答辩 30 秒**：离线用 numpy 做 max-Z 投影，色标调 viz_style。
## viz_style.py

**路径**：[`tools/python/viz_style.py`](../../../tools/python/viz_style.py)

**职责**：matplotlib rcParams 与赛题色板。

**为什么选这段**：全部配图统一风格。

```1:60:tools/python/viz_style.py
"""Shared matplotlib styling and PIL stitch utilities for NyxViz figures."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.figure import Figure
from PIL import Image, ImageDraw, ImageFont

FIG_DPI = 300
DOC_EMBED_DPI = 300
VIZ_BG = "#0a0e1a"
PANEL_BG = "#0f1424"
GRID_ALPHA = 0.12
LINE_WIDTH = 2.5
DIVIDER_RGB = (58, 69, 88)

# Figure Composer layout tokens
PANEL_RADIUS = 12
PANEL_BORDER = 2
PANEL_PAD = 16
PANEL_GAP = 20
SECTION_GAP = 32
LABEL_BAR_H = 44
TITLE_BAR_H = 52
SHADOW_OFFSET = 4
SHADOW_ALPHA = 72

_FONT_CACHE: dict[tuple[int, bool], ImageFont.FreeTypeFont | ImageFont.ImageFont] = {}

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


def hex_to_rgb(hex_color: str) -> tuple[int, int, int]:
    h = hex_color.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)

```

**输入 / 输出**：无 → 全局样式

**答辩 30 秒**：字体、背景、cosmic 色表在这里设，generate_figures 复用。
## generate_figures.py — compose_narrative_poster

**路径**：[`tools/python/generate_figures.py`](../../../tools/python/generate_figures.py)

**职责**：四幕叙事代表图 PIL 合成。

**为什么选这段**：submission_representative 来源。

```4238:4285:tools/python/generate_figures.py
def compose_narrative_poster(timeline: dict) -> None:
    """文档/录屏对齐代表图：三幕各一张 task 配图 + findings 四卡。"""
    canvas_w = NARR_CANVAS_W
    h1, h2, h3, h4 = _narr_compute_act_heights(canvas_w)
    for _ in range(5):
        new_w = _narr_compute_canvas_width((h1, h2, h3))
        if abs(new_w - canvas_w) <= 2:
            canvas_w = new_w
            break
        canvas_w = new_w
        h1, h2, h3, h4 = _narr_compute_act_heights(canvas_w)

    header = _narr_poster_header(canvas_w)
    act_specs = [
        (NARR_DOC_SECTIONS[0], h1),
        (NARR_DOC_SECTIONS[1], h2),
        (NARR_DOC_SECTIONS[2], h3),
    ]
    acts: list[Image.Image] = []
    for (act_num, title, scene_tag, figs), act_h in act_specs:
        scale = NARR_ACT1_FIG_SCALE if act_num == 1 else 1.0
        acts.append(
            _build_doc_figure_act(
                act_num, title, scene_tag, figs, canvas_w, act_h, fig_scale=scale
            )
        )
    acts.append(_build_findings_act(timeline, canvas_w, h4))

    bg = hex_to_rgb("#050a14")
    canvas = Image.new("RGB", (canvas_w, NARR_CANVAS_H), bg)
    y = 0
    canvas.paste(header.convert("RGB"), (0, y))
    y += header.height
    for i, act in enumerate(acts):
        canvas.paste(act.convert("RGB"), (0, y))
        y += act.height
        if i < len(acts) - 1:
            y += NARR_SECTION_GAP
            div = _narr_section_divider(canvas_w)
            canvas.paste(div.convert("RGB"), (0, y))
            y += NARR_DIVIDER_H

    for name in (
        "_app_poster_capture_resized.png",
        "task6_story_poster.png",
        "app_infographic_poster.png",
    ):
        save_pil_png(canvas, OUT / name)
```

**输入 / 输出**：截图 PNG → task6_story_poster.png

**答辩 30 秒**：把 app 截图、发现卡、配图按叙事幕次竖拼，动态算画布宽。
## generate_figures.py — findings 卡

**路径**：[`tools/python/generate_figures.py`](../../../tools/python/generate_figures.py)

**职责**：第 4 幕发现卡铺满。

**为什么选这段**：代表图第 4 节。

```4130:4185:tools/python/generate_figures.py
def _build_findings_act(timeline: dict, width: int, height: int) -> Image.Image:
    """第四幕 · 铺满内容区的 2×2 发现卡。"""
    k = _story_kpis(timeline)
    canvas = Image.new("RGBA", (width, height), (*hex_to_rgb(VIZ_BG), 255))

    heading = _narr_act_heading(4, "科学发现", width)
    canvas.paste(heading, (0, 0), heading)

    footer_h = NARR_FINDINGS_FOOTER_H
    body_y = heading.height
    body_h = height - body_y - footer_h

    cards = [
        ("01", "引力驱动团块化", f"σ +{k['sigma_pct']:.1f}%", f"p99−p01 +{k['span_pct']:.1f}%"),
        ("02", "密度分布两极化", f"void {k['void_vol']:.1f}%", "右尾增厚 · 两极化"),
        ("03", "少数致密承载结构", f"vol {k['tail_vol']:.2f}%", f"mass {k['tail_mass']:.1f}%"),
        ("04", "统计—空间可验证", "召回 100%", "Top 1% · filament 一致"),
    ]
    gap = NARR_FINDINGS_CARD_GAP
    inner_w = _narr_inner_w(width)
    card_w = (inner_w - gap) // 2
    card_h = (body_h - gap) // 2
    grid_x = NARR_MARGIN
    grid_y = 0

    overlay = Image.new("RGBA", (width, body_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    positions = [
        (grid_x, grid_y),
        (grid_x + card_w + gap, grid_y),
        (grid_x, grid_y + card_h + gap),
        (grid_x + card_w + gap, grid_y + card_h + gap),
    ]
    for (num, title, primary, secondary), (cx, cy) in zip(cards, positions, strict=True):
        _render_findings_card_filled(draw, cx, cy, card_w, card_h, num, title, primary, secondary)

    canvas.paste(overlay, (0, body_y), overlay)
    draw = ImageDraw.Draw(canvas)
    foot_font = load_ui_font(22)
    foot_txt = "Nyx 128³  ·  100 时间步  ·  气体密度 ρ"
    tw = draw.textlength(foot_txt, font=foot_font)
    draw.text(
        ((width - tw) / 2, height - footer_h + 4),
        foot_txt,
        fill=hex_to_rgb(THEME["muted"]),
        font=foot_font,
    )
    return canvas


def _render_findings_card_filled(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
```

**输入 / 输出**：指标 dict → PIL 卡片

**答辩 30 秒**：从 timeline 读 σ%、void 等，画四张发现卡。
## compose_representative_poster.py

**路径**：[`tools/python/compose_representative_poster.py`](../../../tools/python/compose_representative_poster.py)

**职责**：npm run capture-app-poster 流水线。

**为什么选这段**：一键生成代表图。

```1:45:tools/python/compose_representative_poster.py
"""Compose representative poster: 4-act narrative science story → 3840×5200."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_figures import (  # noqa: E402
    STATS,
    compose_representative_poster,
    representative_poster,
)


def main() -> int:
    timeline = json.loads(STATS.read_text(encoding="utf-8"))
    compose_representative_poster(timeline)
    representative_poster(timeline)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**输入 / 输出**：Playwright 截图 → generate_figures

**答辩 30 秒**：先截 app 海报，再调 compose_narrative_poster。
