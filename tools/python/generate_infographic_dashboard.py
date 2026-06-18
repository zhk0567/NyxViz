"""Representative infographic: video.html home (top) + 系统分析流程 matrix (bottom)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))

from viz_style import (
    THEME,
    fit_panel_contain,
    hex_to_rgb,
    load_ui_font,
    save_pil_png,
)

FIG = ROOT / "docs" / "figures"
STATS = ROOT / "public" / "stats" / "timeline.json"
VIDEO_INTRO_MANUAL = FIG / "_rep_video_intro_manual.png"
VIDEO_INTRO = FIG / "_rep_video_intro.png"
OUT = FIG / "nyxviz_infographic_dashboard.png"
OUT_SUB = ROOT / "docs" / "submission" / "submission_infographic_dashboard.jpg"

CANVAS_W = 3840
MAX_TOP_H = 2400
MARGIN = 48
GAP = 20
FLOW_COL_GAP = 72  # 四列任务之间的横向间距（给行内箭头留足空间）
GOAL_GAP = 52  # 第 4 列与「设计目标」面板之间的间距
BG = "#060b16"
PANEL = "#0c1322"
BEIGE = "#c4a574"
FLOW_LINE = "#e8c878"
FLOW_ARROW = "#f5d98a"
BORDER = "#243048"

# 四列赛题（与参考图四列对齐）
COL_ACCENTS = [THEME["purple"], THEME["blue"], THEME["cyan"], THEME["coral"]]

ANALYSIS_TASKS = [
    ("任务一", "体渲染看见", "TF · 光照 · 密度演化"),
    ("任务二", "演化规律归纳", "团块化 · 结构形成"),
    ("任务三", "log 直方图", "128 bin 分布漂移"),
    ("任务四", "刷选验证导出", "统计—空间闭环"),
]

DATA_PIPELINE = [
    ("Nyx .dat", "128³ · 0000–0099 原始场"),
    ("precompute", "timeline.json · 四题共用"),
    ("stats JSON", "100 步 KPI 真源"),
    ("Web Worker", "刷选 · 投影 · 四题共用"),
]


# 可视方案配图：优先网页截屏 _flow_*.png，回退静态 task 图
def _pick_fig(*candidates: str, exclude: frozenset[str] = frozenset()) -> str:
    for name in candidates:
        if name in exclude:
            continue
        if (FIG / name).exists():
            return name
    for name in reversed(candidates):
        if name not in exclude:
            return name
    return candidates[-1]


def _flow_figures() -> tuple[list[tuple[str, str, str]], list[tuple[str, str, str]]]:
    # 任务三：算法=柱状 t=0/t=99；渲染=五步曲线叠加。禁止两格共用 task3_hist_overlay。
    t3_render = _pick_fig("task3_hist_overlay.png", "task3_story_panel.png", "task3_void_evolution.png")
    t3_algo = _pick_fig(
        "task3_log_hist_bars.png",
        "task3_bin_sensitivity.png",
        "task3_peak_drift.png",
        exclude=frozenset({t3_render}),
    )

    algo = [
        ("Hero 体渲染", _pick_fig("task1_vol_strip.png"), "五帧 t=0→99 体渲染条带"),
        (
            "空间统计证据",
            _pick_fig("task2_spatial_summary.png", "task2_spatial_metrics.png"),
            "Moran · ξ · 分形维 · bootstrap",
        ),
        (
            "log 直方图 128 bins",
            t3_algo,
            "t=0 / t=99 柱状分布对比",
        ),
        (
            "空间→统计反查",
            _pick_fig(
                "task4_spatial_to_stats.png",
                "task4_threshold_comparison.png",
            ),
            "亮脊投影 · 密度带 ρ 反查闭环",
        ),
    ]
    render = [
        (
            "TF 与光照",
            _pick_fig("task1_render_params.png", "task1_lighting_diagram.png"),
            "传递函数 · 配色 · Phong 光照",
        ),
        (
            "科学发现",
            _pick_fig("task4_discovery_summary.png", "task3_void_evolution.png"),
            "统计—空间互证 · 演化结论",
        ),
        (
            "五步分布叠加",
            t3_render,
            "代表步密度演化 · 分位漂移",
        ),
        (
            "联动刷选验证",
            _pick_fig("task4_brush_rows.png", "task4_brush_triptych.png"),
            "直方图框选 · 体渲染 · 投影反查",
        ),
    ]
    return algo, render


def _load(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(path)
    return Image.open(path).convert("RGBA")


def _trim_content_margins(img: Image.Image, *, pad: int = 6, bg: str = BG) -> Image.Image:
    """Crop outer letterbox so wide dual-panel figures use more of the cell."""
    rgb = np.array(img.convert("RGB"))
    bg_arr = np.array(hex_to_rgb(bg), dtype=np.int16)
    mask = np.abs(rgb.astype(np.int16) - bg_arr).max(axis=2) > 18
    if not mask.any():
        return img
    ys = np.where(mask.any(axis=1))[0]
    xs = np.where(mask.any(axis=0))[0]
    y0, y1 = max(0, int(ys[0]) - pad), min(rgb.shape[0], int(ys[-1]) + pad + 1)
    x0, x1 = max(0, int(xs[0]) - pad), min(rgb.shape[1], int(xs[-1]) + pad + 1)
    return img.crop((x0, y0, x1, y1))


def _paste_contain(
    canvas: Image.Image,
    img: Image.Image,
    box: tuple[int, int, int, int],
    *,
    bg: str = BG,
    valign: str = "center",
    inset_frac: float = 0.0,
) -> None:
    """Letterbox image inside box — width/height constrained, never cover-crop sides."""
    bx, by, bw, bh = box
    inset = int(min(bw, bh) * inset_frac)
    fit_w = max(1, bw - 2 * inset)
    fit_h = max(1, bh - 2 * inset)
    fitted = fit_panel_contain(img, fit_w, fit_h, bg=bg, allow_upscale=True, valign=valign)
    px = bx + inset + (fit_w - fitted.width) // 2
    py = by + inset + (fit_h - fitted.height) // 2
    canvas.paste(fitted, (px, py))


def _draw_arrow_v(
    draw: ImageDraw.ImageDraw,
    x: int,
    y1: int,
    y2: int,
    *,
    color: str = BEIGE,
    dashed: bool = False,
    width: int = 6,
) -> None:
    c = hex_to_rgb(color)
    if dashed:
        dist = abs(y2 - y1)
        step, gap = 14, 10
        pos = 0.0
        while pos < dist:
            end = min(pos + step, dist)
            ya, yb = (y1 + pos, y1 + end) if y2 > y1 else (y1 - pos, y1 - end)
            draw.line([(x, ya), (x, yb)], fill=c, width=width)
            pos += step + gap
    else:
        draw.line([(x, y1), (x, y2)], fill=c, width=width)
    tip = y2
    sz = 22
    draw.polygon(
        [(x, tip), (x - sz // 2, tip - (sz if y2 > y1 else -sz)), (x + sz // 2, tip - (sz if y2 > y1 else -sz))],
        fill=c,
    )


def _draw_arrow_h(
    draw: ImageDraw.ImageDraw,
    x1: int,
    y: int,
    x2: int,
    *,
    color: str = BEIGE,
    width: int = 6,
) -> None:
    c = hex_to_rgb(color)
    draw.line([(x1, y), (x2, y)], fill=c, width=width)
    direction = 1 if x2 > x1 else -1
    tip = x2
    sz = 22
    draw.polygon(
        [(tip, y), (tip - direction * sz, y - sz // 2), (tip - direction * sz, y + sz // 2)],
        fill=c,
    )


def _draw_column_flow(
    draw: ImageDraw.ImageDraw,
    x: int,
    y1: int,
    y2: int,
    *,
    color: str = BEIGE,
) -> None:
    """列内纵向流程：粗线 + 箭头。"""
    c = hex_to_rgb(color)
    direction = 1 if y2 > y1 else -1
    sz = 32
    shaft_end = y2 - direction * sz
    draw.line([(x, y1), (x, shaft_end)], fill=c, width=14)
    draw.polygon(
        [(x, y2), (x - sz // 2, y2 - direction * sz), (x + sz // 2, y2 - direction * sz)],
        fill=c,
    )


def _draw_row_flow(
    draw: ImageDraw.ImageDraw,
    x1: int,
    x2: int,
    y: int,
    *,
    color: str = BEIGE,
) -> None:
    """行内横向流程：粗线 + 箭头。"""
    c = hex_to_rgb(color)
    direction = 1 if x2 > x1 else -1
    span = abs(x2 - x1)
    sz = max(18, min(28, span // 3))
    shaft_end = x2 - direction * sz
    if direction * (shaft_end - x1) >= 6:
        draw.line([(x1, y), (shaft_end, y)], fill=c, width=12)
    draw.polygon(
        [(x2, y), (x2 - direction * sz, y - sz // 2), (x2 - direction * sz, y + sz // 2)],
        fill=c,
    )


def _kpis(timeline: dict) -> dict:
    s0, s99 = timeline["timesteps"][0], timeline["timesteps"][99]
    span0, span99 = s0["p99"] - s0["p01"], s99["p99"] - s99["p01"]
    return {
        "sigma_pct": (s99["std"] - s0["std"]) / s0["std"] * 100,
        "span_pct": (span99 - span0) / span0 * 100,
        "void0": s0.get("voidFractionBelowT0P10", 0) * 100,
        "void99": s99.get("voidFractionBelowT0P10", 0) * 100,
    }


def _resolve_video_intro() -> Image.Image:
    candidates: list[Path] = []
    if VIDEO_INTRO.exists():
        candidates.append(VIDEO_INTRO)
    if VIDEO_INTRO_MANUAL.exists():
        candidates.append(VIDEO_INTRO_MANUAL)
    if not candidates:
        raise FileNotFoundError("Missing video intro. Run: npm run figures:infographic")
    best = max(candidates, key=lambda p: Image.open(p).size[0] * Image.open(p).size[1])
    print(f"Using video home: {best.name} ({Image.open(best).size[0]}×{Image.open(best).size[1]})")
    return _load(best).convert("RGB")


HERO_TITLE_GRAD_L = "#4ec4ff"
HERO_TITLE_GRAD_R = "#9b8cf8"
HERO_GAP = 12


def _trim_vertical_empty(img: Image.Image, *, pad: int = 8) -> Image.Image:
    """Crop letterbox / empty margins so the intro panel fills the top band."""
    rgb = np.array(img.convert("RGB"))
    bg = np.array(hex_to_rgb(BG), dtype=np.int16)
    diff = np.abs(rgb.astype(np.int16) - bg).max(axis=2)
    mask = diff > 18
    if not mask.any():
        return img
    ys = np.where(mask.any(axis=1))[0]
    xs = np.where(mask.any(axis=0))[0]
    y0, y1 = max(0, int(ys[0]) - pad), min(rgb.shape[0], int(ys[-1]) + pad + 1)
    x0, x1 = max(0, int(xs[0]) - pad), min(rgb.shape[1], int(xs[-1]) + pad + 1)
    return img.crop((x0, y0, x1, y1))


def _draw_gradient_text(
    canvas: Image.Image,
    text: str,
    center_x: int,
    y: int,
    font,
    color_left: str,
    color_right: str,
) -> None:
    """Horizontal gradient fill clipped to glyph mask."""
    probe = ImageDraw.Draw(canvas)
    tw = int(probe.textlength(text, font=font))
    x = center_x - tw // 2
    pad = 4
    mask = Image.new("L", (tw + pad * 2, int(font.size * 1.6)), 0)
    md = ImageDraw.Draw(mask)
    bbox = md.textbbox((0, 0), text, font=font)
    th = bbox[3] - bbox[1]
    ty = pad - bbox[1]
    md.text((pad, ty), text, fill=255, font=font)
    gw, gh = mask.size
    c0 = np.array(hex_to_rgb(color_left), dtype=np.float64)
    c1 = np.array(hex_to_rgb(color_right), dtype=np.float64)
    ramp = np.linspace(0.0, 1.0, gw, dtype=np.float64)
    grad_row = (c0 * (1.0 - ramp[:, None]) + c1 * ramp[:, None]).astype(np.uint8)
    grad_arr = np.tile(grad_row[None, :, :], (gh, 1, 1))
    layer = Image.fromarray(grad_arr, mode="RGB")
    layer.putalpha(mask)
    canvas.paste(layer, (x - pad, y), layer)


def _draw_infographic_hero(width: int) -> Image.Image:
    """PIL hero: gradient title + subtitle."""
    title_font = load_ui_font(80, bold=True)
    sub_font = load_ui_font(30)
    title_h = 96
    sub_h = 44
    pad_top, pad_mid, pad_bottom = 40, 16, 28
    hero_h = pad_top + title_h + pad_mid + sub_h + pad_bottom
    hero = Image.new("RGBA", (width, hero_h), (*hex_to_rgb(BG), 255))
    draw = ImageDraw.Draw(hero)

    _draw_gradient_text(hero, "宇宙网诞生记", width // 2, pad_top, title_font, HERO_TITLE_GRAD_L, HERO_TITLE_GRAD_R)

    subtitle = "从近乎均匀的涨落到支配宇宙的大尺度结构"
    sw = int(draw.textlength(subtitle, font=sub_font))
    draw.text(((width - sw) // 2, pad_top + title_h + pad_mid), subtitle, fill=hex_to_rgb(THEME["muted"]), font=sub_font)

    return hero.convert("RGB")


def _detect_intro_body_top(img: Image.Image, *, fallback: int = 218) -> int:
    """Find Y below vd-header: skip NYXVIZ/title band, keep 3-column panel body."""
    rgb = np.array(img.convert("RGB"))
    bg = np.array(hex_to_rgb(BG), dtype=np.int16)
    row_content = (np.abs(rgb.astype(np.int16) - bg).max(axis=2) > 22).sum(axis=1)
    h = len(row_content)
    in_header = False
    gap_start = None
    for y in range(min(80, h), min(400, h)):
        c = int(row_content[y])
        if not in_header and c > 400:
            in_header = True
            continue
        if in_header and c < 30:
            if gap_start is None:
                gap_start = y
            elif y - gap_start >= 35:
                for y2 in range(y, min(y + 30, h)):
                    if row_content[y2] > 200:
                        return max(0, y2 - 2)
                return y
        elif in_header and c >= 30:
            gap_start = None
    return fallback


def _compose_top(intro: Image.Image) -> Image.Image:
    """录屏首页整页：header + 三栏 + 四卡发现区（Playwright 一次截屏）。"""
    intro = _trim_vertical_empty(intro.convert("RGB"))
    w = CANVAS_W
    scaled_h = max(1, int(intro.height * w / intro.width))
    if scaled_h > MAX_TOP_H:
        top = intro.resize((w, MAX_TOP_H), Image.Resampling.LANCZOS)
        print(f"Top section: {top.width}×{top.height} (clamped from {scaled_h}px)")
    else:
        top = intro.resize((w, scaled_h), Image.Resampling.LANCZOS)
        print(f"Top section: {top.width}×{top.height} (full video intro home)")
    return top


def _text_cell(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    line1: str,
    line2: str,
    line3: str | None,
    accent: str,
) -> None:
    draw.rounded_rectangle([x, y, x + w, y + h], radius=10, fill=hex_to_rgb("#121e38"), outline=hex_to_rgb(accent), width=2)
    f1 = load_ui_font(22, bold=True)
    f2 = load_ui_font(20, bold=True)
    f3 = load_ui_font(17)
    draw.text((x + 14, y + 12), line1, fill=hex_to_rgb(BEIGE), font=f1)
    draw.text((x + 14, y + 38), line2, fill=(245, 249, 255), font=f2)
    if line3:
        draw.text((x + 14, y + 64), line3, fill=hex_to_rgb(THEME["muted"]), font=f3)


def _draw_vertical_row_label(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    label: str,
    *,
    text_color: str = BEIGE,
    outline: str = BEIGE,
) -> None:
    """Left-column row label: one bordered box per flow row, two stacked chars."""
    draw.rounded_rectangle(
        [x, y, x + w, y + h],
        radius=10,
        fill=hex_to_rgb("#0a1020"),
        outline=hex_to_rgb(outline),
        width=2,
    )
    lf = load_ui_font(28, bold=True)
    tc = hex_to_rgb(text_color)
    chars = [c for c in (list(label[:2]) if len(label) >= 2 else [label]) if c]
    if not chars:
        return

    bboxes = [draw.textbbox((0, 0), ch, font=lf) for ch in chars]
    char_gap = 6
    total_h = sum(bb[3] - bb[1] for bb in bboxes) + char_gap * (len(chars) - 1)
    stack_y = y + (h - total_h) // 2

    for ch, bb in zip(chars, bboxes):
        tw = bb[2] - bb[0]
        th = bb[3] - bb[1]
        tx = x + (w - tw) // 2 - bb[0]
        ty = stack_y - bb[1]
        draw.text((tx, ty), ch, fill=tc, font=lf)
        stack_y += th + char_gap


def _viz_cell(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    fig_name: str,
    sub: str,
    accent: str,
) -> None:
    draw.rounded_rectangle([x, y, x + w, y + h], radius=12, fill=hex_to_rgb(PANEL), outline=hex_to_rgb(accent), width=2)
    tf = load_ui_font(24, bold=True)
    sf = load_ui_font(18)
    # 标题区高度：24px 标题 + 18px 副标题 + 上下留白，避免配图覆盖副标题
    cap = 80
    img_gap = 12
    img_pad_x = 8
    img_pad_bottom = 12
    draw.text((x + 12, y + 12), title, fill=hex_to_rgb(accent), font=tf)
    draw.text((x + 12, y + 44), sub, fill=hex_to_rgb(THEME["muted"]), font=sf)
    p = FIG / fig_name
    if p.exists():
        img = _load(p)
        img_box = (x + img_pad_x, y + cap + img_gap, w - 2 * img_pad_x, h - cap - img_gap - img_pad_bottom)
        aspect = img.width / max(1, img.height)
        # Wide dual-panel figures (e.g. task3 t=0/t=99 bars): trim margins, inset so both panels stay visible.
        if aspect >= 1.75:
            img = _trim_content_margins(img)
            _paste_contain(canvas, img, img_box, inset_frac=0.05, valign="center")
        else:
            _paste_contain(canvas, img, img_box)


def _compose_flow(kpi: dict) -> Image.Image:
    """系统分析流程：分析任务 → 数据处理 → 可视方案(算法/渲染) → 设计目标。"""
    ALGO_VIZ, RENDER_VIZ = _flow_figures()
    inner_w = CANVAS_W - 2 * MARGIN
    goal_w = 380
    row_label_w = 108
    grid_w = inner_w - goal_w - GOAL_GAP - row_label_w - GAP
    col_w = (grid_w - 3 * FLOW_COL_GAP) // 4
    col_x = [MARGIN + row_label_w + GAP + i * (col_w + FLOW_COL_GAP) for i in range(4)]

    title_h = 52
    legend_h = 36
    task_h = 92
    data_h = 78
    viz_h = 540
    footer_h = 56
    legend_gap = 71  # 图例 → 分析任务行（随 row_gap 同比放大，原 44）
    row_gap = 84  # 主流程行间距：任务/数据/算法/渲染（原 52）
    footer_gap = 65  # 渲染行 → 底栏 KPI（随 row_gap 同比放大，原 40）
    arrow_gap = 10  # 横向箭头端点距列框边缘的内边距
    v_flow_inset = 20  # 纵向箭头端点距上下行框边缘（加大以匹配行距，原 14）

    block_h = (
        title_h + legend_h + legend_gap + task_h + row_gap + data_h + row_gap
        + viz_h + row_gap + viz_h + footer_gap + footer_h
    )
    section = Image.new("RGB", (CANVAS_W, MARGIN + block_h + MARGIN), hex_to_rgb(BG))
    draw = ImageDraw.Draw(section)

    y = MARGIN
    draw.text((MARGIN, y), "系统分析流程", fill=hex_to_rgb(BEIGE), font=load_ui_font(42, bold=True))
    y += title_h
    legend = "分析任务  →  数据处理  →  可视方案（算法 / 渲染）  →  设计目标"
    draw.text((MARGIN, y), legend, fill=hex_to_rgb(THEME["muted"]), font=load_ui_font(24))
    y += legend_h + legend_gap

    lx = MARGIN

    # ── 行1：分析任务 ──
    row1_y = y
    for i, (lab, title, sub) in enumerate(ANALYSIS_TASKS):
        _text_cell(draw, col_x[i], row1_y, col_w, task_h, lab, title, sub, COL_ACCENTS[i])
    for i in range(3):
        ax1 = col_x[i] + col_w + arrow_gap
        ax2 = col_x[i + 1] - arrow_gap
        _draw_row_flow(draw, ax1, ax2, row1_y + task_h // 2, color=FLOW_ARROW)
    y += task_h + row_gap

    # ── 行2：数据处理 ──
    row2_y = y
    _draw_vertical_row_label(draw, lx, row2_y, row_label_w, data_h, "数据", text_color=BEIGE)
    for i, (t, s) in enumerate(DATA_PIPELINE):
        _text_cell(draw, col_x[i], row2_y, col_w, data_h, t, s, None, COL_ACCENTS[i])
    for i in range(3):
        ax1 = col_x[i] + col_w + arrow_gap
        ax2 = col_x[i + 1] - arrow_gap
        _draw_row_flow(draw, ax1, ax2, row2_y + data_h // 2, color=FLOW_ARROW)
    y += data_h + row_gap

    # ── 行1→2、行2→可视：列内纵向箭头 ──
    row3_y = y
    for i in range(4):
        cx = col_x[i] + col_w // 2
        _draw_column_flow(draw, cx, row1_y + task_h + v_flow_inset, row2_y - v_flow_inset, color=FLOW_LINE)
        _draw_column_flow(draw, cx, row2_y + data_h + v_flow_inset, row3_y - v_flow_inset, color=FLOW_LINE)

    # ── 行3：算法（配图）──
    _draw_vertical_row_label(draw, lx, row3_y, row_label_w, viz_h, "算法", text_color=BEIGE)
    for i, (title, fig, sub) in enumerate(ALGO_VIZ):
        _viz_cell(section, draw, col_x[i], row3_y, col_w, viz_h, title, fig, sub, COL_ACCENTS[i])
    for i in range(3):
        ax1 = col_x[i] + col_w + arrow_gap
        ax2 = col_x[i + 1] - arrow_gap
        _draw_row_flow(draw, ax1, ax2, row3_y + viz_h // 2, color=FLOW_ARROW)
    y += viz_h + row_gap

    row4_y = y
    _draw_vertical_row_label(draw, lx, row4_y, row_label_w, viz_h, "渲染", text_color=THEME["cyan"])

    for i in range(4):
        cx = col_x[i] + col_w // 2
        _draw_column_flow(draw, cx, row3_y + viz_h + v_flow_inset, row4_y - v_flow_inset, color=FLOW_LINE)

    # ── 行4：渲染（配图）──
    for i, (title, fig, sub) in enumerate(RENDER_VIZ):
        _viz_cell(section, draw, col_x[i], row4_y, col_w, viz_h, title, fig, sub, COL_ACCENTS[i])
    for i in range(3):
        ax1 = col_x[i] + col_w + arrow_gap
        ax2 = col_x[i + 1] - arrow_gap
        _draw_row_flow(draw, ax1, ax2, row4_y + viz_h // 2, color=FLOW_ARROW)

    y += viz_h + footer_gap

    # ── 右侧：设计目标（跨可视方案两行）──
    gx = MARGIN + inner_w - goal_w
    gy = row3_y
    gh = viz_h + row_gap + viz_h
    draw.rounded_rectangle([gx, gy, gx + goal_w, gy + gh], radius=14, fill=hex_to_rgb("#121e38"), outline=hex_to_rgb(THEME["gold"]), width=3)
    gf = load_ui_font(30, bold=True)
    bf = load_ui_font(22)
    sf = load_ui_font(19)
    draw.text((gx + 20, gy + 20), "设计目标", fill=hex_to_rgb(THEME["gold"]), font=gf)
    goals = [
        "video.html",
        "录屏三栏首页",
        "",
        "app.html",
        "交互长卷探索",
        "",
        "看见 → 量化 → 分布 → 验证",
    ]
    ty = gy + 68
    for line in goals:
        if not line:
            ty += 10
            continue
        color = (245, 249, 255) if "html" in line else hex_to_rgb(THEME["muted"])
        f = bf if "html" in line else sf
        draw.text((gx + 24, ty), line, fill=color, font=f)
        ty += 34 if "html" in line else 28

    # 指向设计目标的横向箭头（从第4列渲染格）
    if RENDER_VIZ[3][1]:
        _draw_row_flow(
            draw,
            col_x[3] + col_w + arrow_gap,
            gx - arrow_gap,
            row4_y + viz_h // 2,
            color=THEME["gold"],
        )

    # app 长卷缩略图：紧接文案下方，占列高 ~70%（与 _viz_cell 配图区一致）
    app_thumb = FIG / "task6_story_poster.png"
    if app_thumb.exists():
        thumb_pad_x = 16
        thumb_pad_bottom = 16
        thumb_gap = 12
        thumb_top = ty + thumb_gap
        thumb_w = goal_w - 2 * thumb_pad_x
        thumb_h = gy + gh - thumb_pad_bottom - thumb_top
        if thumb_h >= 120:
            _paste_contain(
                section,
                _load(app_thumb),
                (gx + thumb_pad_x, thumb_top, thumb_w, thumb_h),
            )

    # ── 底栏 KPI ──
    draw.rounded_rectangle(
        [MARGIN, y, MARGIN + inner_w, y + footer_h],
        radius=8,
        fill=hex_to_rgb("#0a1020"),
        outline=hex_to_rgb(BORDER),
        width=1,
    )
    foot = (
        f"Nyx 128³ · 100 步  |  void {kpi['void0']:.1f}%→{kpi['void99']:.1f}%  |  "
        f"σ +{kpi['sigma_pct']:.1f}%  ·  p99−p01 +{kpi['span_pct']:.1f}%  |  "
        f"timeline.json 为统计真源 · 刷选区间与空间结构双向验证"
    )
    draw.text((MARGIN + 16, y + 16), foot, fill=hex_to_rgb(THEME["muted"]), font=load_ui_font(20))

    return section


def compose_infographic(timeline: dict) -> Image.Image:
    top = _compose_top(_resolve_video_intro())
    bottom = _compose_flow(_kpis(timeline))
    div = 8
    canvas = Image.new("RGB", (CANVAS_W, top.height + div + bottom.height), hex_to_rgb(BG))
    canvas.paste(top, (0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.line([(MARGIN, top.height + 4), (CANVAS_W - MARGIN, top.height + 4)], fill=hex_to_rgb(BEIGE), width=4)
    canvas.paste(bottom, (0, top.height + div))
    return canvas


def main() -> int:
    if not STATS.exists():
        print("Missing timeline.json", file=sys.stderr)
        return 1
    timeline = json.loads(STATS.read_text(encoding="utf-8"))
    FIG.mkdir(parents=True, exist_ok=True)
    # 确保柱状 log 直方图存在（信息图任务三算法格需 t=0/t=99 柱状对比）
    try:
        from generate_figures import compose_findings_strip, task3_log_hist_bars

        task3_log_hist_bars(timeline)
        compose_findings_strip(timeline)
    except Exception as exc:
        print(f"Warn: figure prebuild skipped: {exc}", file=sys.stderr)
    poster = compose_infographic(timeline)
    save_pil_png(poster, OUT)
    OUT_SUB.parent.mkdir(parents=True, exist_ok=True)
    poster.convert("RGB").save(OUT_SUB, format="JPEG", quality=93, optimize=True)
    public = ROOT / "public" / "figures" / OUT.name
    public.parent.mkdir(parents=True, exist_ok=True)
    save_pil_png(poster, public)
    print(f"Infographic: {OUT} ({poster.width}×{poster.height}px)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
