"""Compose 3840×6480 cosmic web poster per LAYOUT_SPEC (visual-first)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

from layout_spec import (
    CANVAS_H,
    CANVAS_W,
    CONTENT_W,
    MARGIN_X,
    PAD_Y,
    S01,
    S02_FRAMES,
    S02_FRAME_SIZE,
    SECTIONS,
)
from poster_draw import (
    RGB,
    draw_round_card,
    draw_section_title,
    draw_vertical_colorbar,
    load_fonts,
    paste_cover,
    ratio_label,
    render_sparkline,
)
from viz_style import global_projection_domain

ROOT = Path(__file__).resolve().parents[2]
STATS = ROOT / "public" / "stats" / "timeline.json"
FIG = ROOT / "docs" / "figures"
OUT_POSTER = FIG / "cosmic_poster_3840.png"
OUT_APP = FIG / "app_infographic_poster.png"


def _wrap_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font,
    max_w: int,
) -> None:
    line, ly = "", y
    for ch in text:
        trial = line + ch
        if draw.textlength(trial, font=font) > max_w and line:
            draw.text((x, ly), line, fill=RGB["text_muted"], font=font)
            ly += 32
            line = ch
        else:
            line = trial
    if line:
        draw.text((x, ly), line, fill=RGB["text_muted"], font=font)


def _cy(section_y: int, offset: int) -> int:
    """Content Y → canvas Y."""
    return PAD_Y + section_y + offset


def _resolve_vol(t: int) -> Path:
    for name in (f"task1_vol_t{t:04d}.png", f"task1_slice_t{t:04d}.png"):
        p = FIG / name
        if p.exists():
            return p
    return FIG / f"task1_vol_t{t:04d}.png"


def compose_s01(canvas: Image.Image, draw: ImageDraw.ImageDraw, fonts: dict, timeline: dict) -> None:
    y0 = PAD_Y
    s99 = timeline["timesteps"][99]
    s0 = timeline["timesteps"][0]
    span_pct = ratio_label(s0["p99"] - s0["p01"], s99["p99"] - s99["p01"])

    draw_section_title(
        draw,
        fonts,
        MARGIN_X,
        y0 + 80,
        "01",
        "宇宙网诞生记",
        "基于 Nyx 128³ 气体密度，揭示宇宙大尺度结构（宇宙网）的形成过程",
    )

    cx, cy, cw, ch = S01["info_cards"]
    cards = ["128³ 网格", "100 时间步", "气体密度 ρ"]
    for i, label in enumerate(cards):
        top = _cy(0, cy - PAD_Y) + i * 155
        draw_round_card(draw, (cx, top, cx + cw, top + 140))
        draw.text((cx + 24, top + 48), label, fill=RGB["accent_cyan"], font=fonts["body"])

    hx, hy, hw, hh = S01["hero"]
    paste_cover(canvas, _resolve_vol(99), (hx, _cy(0, hy - PAD_Y), hw, hh))
    bx, by, bw, bh = S01["colorbar"]
    vmin, vmax = global_projection_domain(timeline)
    draw_vertical_colorbar(canvas, (bx, _cy(0, by - PAD_Y), bw, bh), vmin, vmax)

    draw.text(
        (hx, _cy(0, hy - PAD_Y) + hh + 12),
        f"t=99 · σ={s99['std']:.4f} · p99−p01 {span_pct}",
        fill=RGB["text_muted"],
        font=fonts["caption"],
    )


def compose_s02(canvas: Image.Image, draw: ImageDraw.ImageDraw, fonts: dict) -> None:
    sec = SECTIONS[1]
    y0 = sec.y_canvas
    draw_section_title(
        draw,
        fonts,
        MARGIN_X,
        y0 + 24,
        "02",
        "宇宙如何长大：100 步演化全景",
        "从均匀气体到纤维、节点分明的宇宙网拓扑",
    )
    fw, fh = S02_FRAME_SIZE
    frame_y = y0 + 140
    labels = {"t1": 0, "t25": 25, "t50": 50, "t75": 75, "t100": 99}
    for name, fx in S02_FRAMES:
        t = labels[name]
        paste_cover(canvas, _resolve_vol(t), (fx, frame_y, fw, fh))
        draw.text((fx + 8, frame_y + fh - 36), f"t={t}", fill=RGB["text"], font=fonts["body"])

    phase_y = frame_y + fh + 24
    phases = ["早期宇宙（线性阶段）", "非线性增长阶段", "宇宙网形成阶段"]
    pw = CONTENT_W // 3
    for i, text in enumerate(phases):
        px = MARGIN_X + i * pw
        draw_round_card(draw, (px + 8, phase_y, px + pw - 8, phase_y + 120), fill=(12, 18, 32))
        draw.text((px + 28, phase_y + 42), text, fill=RGB["accent_cyan"], font=fonts["body"])

    bar_y = phase_y + 140
    draw.rounded_rectangle(
        (MARGIN_X, bar_y, MARGIN_X + CONTENT_W, bar_y + 16),
        radius=8,
        fill=(30, 50, 90),
    )
    for t in (0, 25, 50, 75, 99):
        px = MARGIN_X + int(t / 99 * CONTENT_W)
        draw.ellipse((px - 6, bar_y + 2, px + 6, bar_y + 14), fill=RGB["accent_orange"])


def compose_s03(canvas: Image.Image, draw: ImageDraw.ImageDraw, fonts: dict, timeline: dict) -> None:
    steps = timeline["timesteps"]
    ts = [s["timestep"] for s in steps]
    s0, s99 = steps[0], steps[99]
    std = [s["std"] for s in steps]
    span = [s["p99"] - s["p01"] for s in steps]
    tail = [s["tailMassAboveP99"] * 100 for s in steps]

    y0 = SECTIONS[2].y_canvas
    draw_section_title(
        draw,
        fonts,
        MARGIN_X,
        y0 + 24,
        "03",
        "用数字证明变化：密度分布的两极化演化",
        "100 步 log 直方图与 σ、p99−p01、高密度尾体积占比（真实 timeline）",
    )

    hist_y = y0 + 200
    hist_path = FIG / "task3_hist_overlay.png"
    if hist_path.exists():
        paste_cover(canvas, hist_path, (MARGIN_X, hist_y, 1600, 600))

    specs = [
        (std, "#4EC4FF", "σ(t)", ratio_label(s0["std"], s99["std"])),
        (span, "#9EEFFF", "p99−p01", ratio_label(span[0], span[-1])),
        (tail, "#FFCC66", "≥p99 体积%", ratio_label(tail[0], tail[-1])),
    ]
    for i, (vals, color, title, badge) in enumerate(specs):
        spark = render_sparkline(ts, vals, color=color, title=title, badge=badge, w=520, h=300)
        canvas.paste(spark, (1850 + i * (520 + 40), hist_y))

    kpi_y = hist_y + 620
    kpis = [
        ("均值 μ", f"{s99['mean']:.3f}"),
        ("标准差 σ", f"{s99['std']:.4f}"),
        ("p99", f"{s99['p99']:.3f}"),
        ("≥p99 体积", f"{s99['tailMassAboveP99'] * 100:.2f}%"),
    ]
    for i, (label, val) in enumerate(kpis):
        col, row = i % 2, i // 2
        kx = 1850 + col * (370 + 40)
        ky = kpi_y + row * (180 + 24)
        draw_round_card(draw, (kx, ky, kx + 370, ky + 180))
        draw.text((kx + 20, ky + 28), label, fill=RGB["text_muted"], font=fonts["body"])
        draw.text((kx + 20, ky + 88), val, fill=RGB["text"], font=fonts["h2"])


def compose_s04_row(
    canvas: Image.Image,
    draw: ImageDraw.ImageDraw,
    fonts: dict,
    y: int,
    *,
    title: str,
    hist: Path,
    spatial: Path,
    bullets: list[str],
    accent: tuple[int, int, int],
) -> None:
    x = MARGIN_X
    w_total = CONTENT_W
    ratios = [0.15, 0.05, 0.35, 0.45]
    labels = ["直方图刷选", "→", "空间映射", "局部放大"]
    paths = [hist, None, spatial, spatial]
    for ratio, lab, path in zip(ratios, labels, paths):
        ww = int(w_total * ratio)
        draw_round_card(draw, (x, y, x + ww, y + 420), fill=(10, 16, 28))
        if lab == "→":
            draw.text((x + ww // 2 - 12, y + 180), "⇄", fill=accent, font=fonts["h1"])
        elif path and path.exists():
            paste_cover(canvas, path, (x + 6, y + 36, ww - 12, 340))
        draw.text((x + 12, y + 8), lab, fill=RGB["text_muted"], font=fonts["caption"])
        x += ww
    draw.text((MARGIN_X + 12, y - 32), title, fill=accent, font=fonts["section"])
    by = y + 48
    for line in bullets[:3]:
        draw.text((MARGIN_X + int(w_total * 0.52), by), f"• {line}", fill=RGB["text"], font=fonts["caption"])
        by += 32


def compose_s04(canvas: Image.Image, draw: ImageDraw.ImageDraw, fonts: dict, timeline: dict) -> None:
    s99 = timeline["timesteps"][99]
    y0 = SECTIONS[3].y_canvas
    draw_section_title(
        draw,
        fonts,
        MARGIN_X,
        y0 + 20,
        "04",
        "统计与空间验证：相空间刷选与结构定位",
        "Top 1% / Bottom 1% 在直方图、体渲染与投影间双向联动",
    )
    row0 = y0 + 130
    compose_s04_row(
        canvas,
        draw,
        fonts,
        row0,
        title="Top 1% 高密度尾 → 节点/纤维",
        hist=FIG / "task4_hist_brush_top1.png",
        spatial=FIG / "task4_brush_top1.png",
        bullets=[
            f"ρ ≥ p99 ({s99['p99']:.2f})",
            f"体积 {s99['tailMassAboveP99'] * 100:.2f}%",
            f"质量 {s99.get('massFractionAboveP99', 0) * 100:.1f}%",
        ],
        accent=RGB["peak_density"],
    )
    compose_s04_row(
        canvas,
        draw,
        fonts,
        row0 + 460,
        title="Bottom 1% 低密度 → IGM 空洞",
        hist=FIG / "task4_hist_brush_bottom1.png",
        spatial=FIG / "task4_brush_bottom1.png",
        bullets=[
            f"ρ ≤ p01 ({s99['p01']:.2f})",
            f"体积 {s99['tailMassBelowP01'] * 100:.2f}%",
            f"质量 {s99.get('massFractionBelowP01', 0) * 100:.1f}%",
        ],
        accent=RGB["low_density"],
    )


def compose_s05(canvas: Image.Image, draw: ImageDraw.ImageDraw, fonts: dict, timeline: dict) -> None:
    s0, s99 = timeline["timesteps"][0], timeline["timesteps"][99]
    sigma_pct = ratio_label(s0["std"], s99["std"])
    span0, span99 = s0["p99"] - s0["p01"], s99["p99"] - s99["p01"]
    span_pct = ratio_label(span0, span99)

    discoveries = [
        ("01", "引力驱动团块化", f"σ {sigma_pct}，宇宙网拓扑在 t=50 后加速成型。"),
        ("02", "密度两极化", f"偏度 {s0['skewness']:.3f}→{s99['skewness']:.3f}，右尾增厚、void 与节点并存。"),
        (
            "03",
            "少数致密承载结构",
            f"≥p99 体积 {s99['tailMassAboveP99'] * 100:.2f}% · 质量 {s99.get('massFractionAboveP99', 0) * 100:.1f}%。",
        ),
        ("04", "统计—空间一致", "Top 1% 刷选呈丝状聚集，与 XY 投影亮脊一致。"),
    ]

    y0 = SECTIONS[4].y_canvas
    draw_section_title(draw, fonts, MARGIN_X, y0 + 20, "05", "关键科学发现（t=99）", None)

    col_w, col_h, gap = 860, 650, 40
    y_cards = y0 + 120
    thumb = FIG / "task5_mass_pie.png"
    for i, (num, title, body) in enumerate(discoveries):
        x = MARGIN_X + i * (col_w + gap)
        draw_round_card(draw, (x, y_cards, x + col_w, y_cards + col_h))
        draw.text((x + 24, y_cards + 20), num, fill=RGB["accent_orange"], font=fonts["h2"])
        draw.text((x + 80, y_cards + 28), title, fill=RGB["text"], font=fonts["section"])
        if i == 2 and thumb.exists():
            paste_cover(canvas, thumb, (x + 40, y_cards + 200, col_w - 80, 380))
        else:
            _wrap_text(draw, x + 24, y_cards + 120, body, fonts["body"], col_w - 48)


def compose_s06(canvas: Image.Image, draw: ImageDraw.ImageDraw, fonts: dict) -> None:
    y0 = SECTIONS[5].y_canvas
    draw_section_title(draw, fonts, MARGIN_X, y0 + 24, "06", "整体分析流程图", None)

    nodes = [
        "Nyx 数据",
        "体渲染",
        "时序统计",
        "相空间刷选",
        "空间映射",
        "验证分析",
        "科学发现",
    ]
    nw, nh, gap = 420, 220, 80
    y_node = y0 + 200
    x = MARGIN_X
    for i, label in enumerate(nodes):
        draw_round_card(draw, (x, y_node, x + nw, y_node + nh), fill=(14, 22, 40))
        draw.text((x + 36, y_node + 80), label, fill=RGB["accent_cyan"], font=fonts["body"])
        if i < len(nodes) - 1:
            draw.text((x + nw + 20, y_node + 90), "→", fill=RGB["accent_orange"], font=fonts["h2"])
        x += nw + gap


def compose_poster_3840(timeline: dict) -> Path:
    canvas = Image.new("RGB", (CANVAS_W, CANVAS_H), RGB["bg"])
    draw = ImageDraw.Draw(canvas)
    fonts = load_fonts()

    for sec in SECTIONS:
        draw.line(
            [(MARGIN_X, sec.y_canvas), (MARGIN_X + CONTENT_W, sec.y_canvas)],
            fill=RGB["border"],
            width=1,
        )

    compose_s01(canvas, draw, fonts, timeline)
    compose_s02(canvas, draw, fonts)
    compose_s03(canvas, draw, fonts, timeline)
    compose_s04(canvas, draw, fonts, timeline)
    compose_s05(canvas, draw, fonts, timeline)
    compose_s06(canvas, draw, fonts)

    FIG.mkdir(parents=True, exist_ok=True)
    canvas.save(OUT_POSTER, format="PNG", optimize=True)
    canvas.save(OUT_APP, format="PNG", optimize=True)
    return OUT_POSTER


def main() -> int:
    if not STATS.exists():
        print("Run precompute first", file=sys.stderr)
        return 1
    timeline = json.loads(STATS.read_text(encoding="utf-8"))
    path = compose_poster_3840(timeline)
    print(f"Poster 3840: {path}")
    print(f"App copy: {OUT_APP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
