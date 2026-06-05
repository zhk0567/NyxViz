"""Generate static figures for tasks 1–4 into docs/figures/."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib import image as mpimg
from matplotlib.colors import LogNorm

from projection_render import render_projection_rgb, render_xy_projection
from spatial_to_stats import filament_density_band
from viz_style import (
    COSMIC_CMAP,
    LINE_WIDTH,
    THEME,
    apply_dark_theme,
    global_projection_domain,
    hex_to_rgb,
    render_horizontal_colorbar_png,
    render_text_banner,
    save_pil_png,
    stitch_panels_png,
    stitch_vertical_weighted,
    style_axes,
    save_figure,
)
from PIL import Image

apply_dark_theme()

ROOT = Path(__file__).resolve().parents[2]
NYX = ROOT / "Nyx"
STATS = ROOT / "public" / "stats" / "timeline.json"
OUT = ROOT / "docs" / "figures"
GRID = 128
REP_STEPS = [0, 25, 50, 75, 99]


def load_volume(path: Path) -> np.ndarray:
    flat = np.fromfile(path, dtype="<f4")
    return flat.reshape((GRID, GRID, GRID), order="C")


def slice_figure(vol: np.ndarray, timestep: int, out: Path, vmin: float, vmax: float) -> None:
    mid = GRID // 2
    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    slices = [
        (vol[mid, :, :], "x = mid"),
        (vol[:, mid, :], "y = mid"),
        (vol[:, :, mid], "z = mid"),
    ]
    for ax, (sl, title) in zip(axes, slices):
        im = ax.imshow(
            sl.T,
            origin="lower",
            cmap=COSMIC_CMAP,
            norm=LogNorm(vmin=max(vmin, 1e-6), vmax=max(vmax, 1e-6)),
        )
        ax.set_title(title, fontsize=10)
        ax.axis("off")
    cbar = fig.colorbar(im, ax=axes, fraction=0.02, label="log₁₀ ρ")
    cbar.ax.yaxis.label.set_color("#9aa3b8")
    cbar.ax.tick_params(colors="#9aa3b8")
    fig.suptitle(f"Nyx gas density — timestep {timestep} (slice fallback)", fontsize=12)
    save_figure(fig, out, has_suptitle=True)


def resolve_vol_image(t: int, timeline: dict) -> Path:
    evo = OUT / f"task1_evo_t{t:04d}.png"
    if evo.exists():
        return evo
    vol = OUT / f"task1_vol_t{t:04d}.png"
    if vol.exists():
        return vol
    sl = OUT / f"task1_slice_t{t:04d}.png"
    if sl.exists():
        return sl
    if not (NYX / f"{t:04d}.dat").exists():
        raise FileNotFoundError(f"No data for t={t}")
    vmin, vmax = global_projection_domain(timeline)
    slice_figure(load_volume(NYX / f"{t:04d}.dat"), t, sl, vmin, vmax)
    return sl


def task1_evo_frames(timeline: dict) -> None:
    """Adaptive-threshold XY max projection — early sparse peaks → late cosmic web."""
    vmin, vmax = global_projection_domain(timeline)
    for t in REP_STEPS:
        dat = NYX / f"{t:04d}.dat"
        if not dat.exists():
            print(f"Skip evo frame t={t}: missing {dat}", file=sys.stderr)
            continue
        vol = load_volume(dat)
        proj = np.max(vol, axis=2)
        t_norm = t / 99.0
        # Loosen visibility: t=0 only top ~8% peaks; t=99 ~45% of projection
        quantile = 0.92 - 0.47 * t_norm
        thresh = float(np.quantile(proj, quantile))
        display = np.where(proj >= thresh, proj, vmin)
        rgb = render_projection_rgb(display, vmin, vmax)

        fig = plt.figure(figsize=(5.6, 3.5), facecolor="#03060e")
        ax = fig.add_axes([0, 0, 1, 1])
        ax.imshow(rgb, origin="lower", interpolation="bilinear")
        ax.axis("off")
        out = OUT / f"task1_evo_t{t:04d}.png"
        save_figure(fig, out, pad=0.02)
        s = timeline["timesteps"][t]
        print(f"Evo frame t={t} q={quantile:.2f} σ={s['std']:.4f} -> {out.name}")


def task1_strip(timeline: dict) -> None:
    paths = [resolve_vol_image(t, timeline) for t in REP_STEPS]
    labels = [f"t={t}  σ={timeline['timesteps'][t]['std']:.3f}" for t in REP_STEPS]
    row = stitch_panels_png(
        paths,
        direction="horizontal",
        gap=14,
        uniform_height=920,
        max_width=5200,
        panel_labels=labels,
    )
    vmin, vmax = global_projection_domain(timeline)
    title = render_text_banner(["体渲染关键帧：气体密度宇宙学演化 (128³)"], row.width)
    cbar = render_horizontal_colorbar_png(vmin, vmax, row.width)
    final = Image.new("RGBA", (row.width, title.height + row.height + cbar.height + 20), (*hex_to_rgb("#0a0e1a"), 255))
    y = 0
    final.paste(title, (0, y))
    y += title.height + 8
    final.paste(row, (0, y))
    y += row.height + 8
    final.paste(cbar, (0, y))
    save_pil_png(final, OUT / "task1_vol_strip.png")
    print(f"Vol strip (PIL): {OUT / 'task1_vol_strip.png'} ({final.width}×{final.height}px)")


def task2_evolution_story(timeline: dict) -> None:
    steps = timeline["timesteps"]
    ts = [s["timestep"] for s in steps]
    span = [s["p99"] - s["p01"] for s in steps]
    tail = [s["tailMassAboveP99"] * 100 for s in steps]
    std = [s["std"] for s in steps]
    skew = [s["skewness"] for s in steps]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    specs = [
        (span, THEME["purple"], "分位跨度 p99−p01（团块化）"),
        (std, THEME["cyan"], "标准差 σ(t)"),
        (tail, THEME["gold"], "高密度尾体积占比 ≥p99 (%)"),
        (skew, THEME["coral"], "偏度 skew(t)"),
    ]
    for ax, (y, color, title) in zip(axes.flat, specs):
        ax.fill_between(ts, y, alpha=0.12, color=color)
        ax.plot(ts, y, color=color, lw=LINE_WIDTH)
        ax.set_title(title, fontsize=13)
        ax.set_xlabel("时间步", fontsize=11)
        style_axes(ax)

    fig.suptitle("任务二：100 步全域统计揭示的演化规律", fontsize=14)
    save_figure(fig, OUT / "task2_evolution_story.png", has_suptitle=True)


def task3_figures(timeline: dict) -> None:
    edges = timeline["logBinEdges"]
    centers = [np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)]
    steps = timeline["timesteps"]
    colors = [THEME["purple"], THEME["blue"], THEME["cyan"], THEME["gold"], THEME["coral"]]

    fig, ax = plt.subplots(figsize=(10, 6))
    for t, c in zip(REP_STEPS, colors):
        hist = timeline["histograms"][t]
        ax.plot(centers, hist, label=f"t={t}", color=c, lw=LINE_WIDTH)
    ax.set_xscale("log")
    ax.set_xlabel("密度 ρ (log)")
    ax.set_ylabel("归一化频数")
    ax.set_title("对数等距分箱直方图叠加（代表步）")
    ax.legend()
    style_axes(ax)
    save_figure(fig, OUT / "task3_hist_overlay.png")

    ts = [s["timestep"] for s in steps]
    fig, ax = plt.subplots(figsize=(11, 5))
    means = [s["mean"] for s in steps]
    ax.fill_between(ts, means, alpha=0.15, color=THEME["purple"])
    ax.plot(ts, means, label="均值", color=THEME["purple"], lw=LINE_WIDTH)
    ax.plot(ts, [s["p99"] for s in steps], label="p99", color=THEME["gold"], lw=LINE_WIDTH)
    ax.plot(ts, [s["std"] for s in steps], label="σ", color=THEME["cyan"], lw=LINE_WIDTH)
    ax.set_xlabel("时间步")
    ax.set_ylabel("密度统计量")
    ax.set_title("100 时间步时序指标")
    ax.legend()
    style_axes(ax)
    save_figure(fig, OUT / "task3_metrics_timeline.png")

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.5))
    axes[0].plot(ts, [s["std"] for s in steps], color=THEME["cyan"], lw=LINE_WIDTH)
    axes[0].set_title("σ(t) 持续扩大", fontsize=12)
    axes[1].plot(ts, [s["skewness"] for s in steps], color=THEME["coral"], lw=LINE_WIDTH)
    axes[1].set_title("偏度 — 右尾增厚", fontsize=12)
    axes[2].plot(ts, [s["p99"] - s["p01"] for s in steps], color=THEME["purple"], lw=LINE_WIDTH)
    axes[2].set_title("p99−p01 分位跨度", fontsize=12)
    for ax in axes:
        ax.set_xlabel("t")
        style_axes(ax)
    save_figure(fig, OUT / "task3_evolution_metrics.png")

    peak_t = []
    for t in range(100):
        h = timeline["histograms"][t]
        peak_t.append(centers[int(np.argmax(h))])
    fig, ax = plt.subplots(figsize=(10, 4.2))
    ax.plot(ts, peak_t, color=THEME["gold"], lw=LINE_WIDTH)
    ax.set_xscale("log")
    ax.set_xlabel("时间步")
    ax.set_ylabel("主峰中心密度 (log)")
    ax.set_title("直方图主峰位置随时间的漂移")
    style_axes(ax)
    save_figure(fig, OUT / "task3_peak_drift.png")


def brush_projection(
    vol: np.ndarray,
    timeline: dict,
    lo: float,
    hi: float,
    title: str,
    out: Path,
) -> None:
    vmin, vmax = global_projection_domain(timeline)
    full = np.max(vol, axis=2)
    highlight = render_xy_projection(vol, timeline, lo, hi)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    axes[0].imshow(
        full.T,
        origin="lower",
        cmap=COSMIC_CMAP,
        norm=LogNorm(vmin=max(vmin, 1e-6), vmax=max(vmax, 1e-6)),
    )
    axes[0].set_title("XY 最大密度投影（全场）", fontsize=13)
    axes[0].axis("off")
    axes[1].imshow(highlight, origin="lower")
    axes[1].set_title(f"刷选高亮：ρ ∈ [{lo:.2f}, {hi:.2f}]", fontsize=13)
    axes[1].axis("off")
    fig.suptitle(title, fontsize=14)
    save_figure(fig, out, has_suptitle=True)


def task4_histogram_brush(timeline: dict, t: int = 99) -> None:
    edges = timeline["logBinEdges"]
    centers = np.array([np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)])
    hist = np.array(timeline["histograms"][t])
    s = timeline["timesteps"][t]
    total = hist.sum() or 1
    pct = hist / total * 100

    def one_brush(lo: float, hi: float, hi_color: str, label: str, fname: str) -> None:
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(centers, pct, width=centers * 0.08, color=THEME["purple"], alpha=0.85, align="center")
        ax.set_xscale("log")
        mask = (centers >= lo) & (centers <= hi * 1.01)
        ax.bar(
            centers[mask],
            pct[mask],
            width=centers[mask] * 0.08,
            color=hi_color,
            alpha=0.95,
            align="center",
            label=label,
        )
        ax.set_xlabel("密度 ρ (log)")
        ax.set_ylabel("占比 %")
        ax.set_title(f"任务四：直方图刷选区间 (t={t})")
        ax.legend()
        style_axes(ax)
        save_figure(fig, OUT / fname, pad=0.18)

    one_brush(s["p99"], s["max"], THEME["gold"], f"Top 1%: ρ≥{s['p99']:.2f}", "task4_hist_brush_top1.png")
    one_brush(s["min"], s["p01"], THEME["cyan"], f"Bottom 1%: ρ≤{s['p01']:.2f}", "task4_hist_brush_bottom1.png")


def task4_spatial_to_stats(vol: np.ndarray, timeline: dict, t: int = 99) -> tuple[float, float]:
    """Spatial → statistical: filament pixels on projection → density band on histogram."""
    lo, hi, filament_mask = filament_density_band(vol)
    vmin, vmax = global_projection_domain(timeline)
    proj = np.max(vol, axis=2)
    rgb = render_projection_rgb(proj, vmin, vmax)
    gold = np.array([0.96, 0.78, 0.26])
    rgb[filament_mask] = rgb[filament_mask] * 0.25 + gold * 0.75

    edges = timeline["logBinEdges"]
    centers = np.array([np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)])
    hist = np.array(timeline["histograms"][t])
    total = hist.sum() or 1
    pct = hist / total * 100

    fig, axes = plt.subplots(1, 2, figsize=(12, 4.6))
    axes[0].imshow(rgb, origin="lower")
    axes[0].set_title(f"空间：filament 亮脊 (t={t}, 投影 ≥ P88)")
    axes[0].axis("off")

    axes[1].bar(centers, pct, width=centers * 0.08, color=THEME["purple"], alpha=0.85, align="center")
    bin_mask = (centers >= lo) & (centers <= hi * 1.01)
    axes[1].bar(
        centers[bin_mask],
        pct[bin_mask],
        width=centers[bin_mask] * 0.08,
        color=THEME["gold"],
        alpha=0.95,
        align="center",
        label=f"filament 带: ρ∈[{lo:.2f}, {hi:.2f}]",
    )
    axes[1].set_xscale("log")
    axes[1].set_xlabel("密度 ρ (log)")
    axes[1].set_ylabel("占比 %")
    axes[1].set_title("统计：亮脊像素对应密度带")
    axes[1].legend()
    style_axes(axes[1])
    fig.suptitle("空间→统计：识别 filament 后在直方图标出对应密度区间", fontsize=12, color="#e6edf3")
    save_figure(fig, OUT / "task4_spatial_to_stats.png", has_suptitle=True, pad=0.16)
    return lo, hi


def task4_triptych(timeline: dict) -> None:
    paths = [
        OUT / "task4_hist_brush_top1.png",
        resolve_vol_image(99, timeline),
        OUT / "task4_brush_top1.png",
    ]
    labels = ["统计刷选", "体渲染 (t=99)", "空间投影验证"]
    row = stitch_panels_png(
        paths,
        direction="horizontal",
        gap=16,
        uniform_height=780,
        max_width=4800,
        panel_labels=labels,
    )
    title = render_text_banner(["相空间联动：Top 1% 高密度尾 → 宇宙网节点"], row.width)
    final = Image.new("RGBA", (row.width, title.height + row.height + 12), (*hex_to_rgb("#0a0e1a"), 255))
    final.paste(title, (0, 0))
    final.paste(row, (0, title.height + 8))
    save_pil_png(final, OUT / "task4_brush_triptych.png")
    print(f"Triptych (PIL): {OUT / 'task4_brush_triptych.png'} ({final.width}×{final.height}px)")


def _ratio_label(v0: float, v99: float) -> str:
    if abs(v0) < 1e-12:
        return "—"
    return f"+{(v99 - v0) / v0 * 100:.1f}%"


def task4_brush_rows(timeline: dict) -> None:
    """Section 04: Top/Bottom 1% rows — hist | projection | KPI | inset."""
    s99 = timeline["timesteps"][99]
    rows = [
        (
            "Top 1% 高密度尾 → 宇宙网节点",
            [
                OUT / "task4_hist_brush_top1.png",
                OUT / "task4_brush_top1.png",
            ],
            THEME["gold"],
            [
                f"ρ ≥ p99 = {s99['p99']:.2f}",
                f"体积占比 {s99['tailMassAboveP99'] * 100:.2f}%",
                f"质量占比 {s99.get('massFractionAboveP99', 0) * 100:.1f}%",
                "空间：丝状节点聚集",
            ],
        ),
        (
            "Bottom 1% 低密度 → IGM 空洞",
            [
                OUT / "task4_hist_brush_bottom1.png",
                OUT / "task4_brush_bottom1.png",
            ],
            THEME["cyan"],
            [
                f"ρ ≤ p01 = {s99['p01']:.2f}",
                f"体积占比 {s99['tailMassBelowP01'] * 100:.2f}%",
                f"质量占比 {s99.get('massFractionBelowP01', 0) * 100:.1f}%",
                "空间：弥散空洞背景",
            ],
        ),
    ]
    fig = plt.figure(figsize=(24, 12), facecolor="#0a0e1a")
    gs = gridspec.GridSpec(2, 4, wspace=0.06, hspace=0.14)
    col_titles = ["统计刷选", "XY 投影", "结构要点", "局部放大"]
    for row_i, (row_title, paths, accent, bullets) in enumerate(rows):
        for col_i in range(4):
            ax = fig.add_subplot(gs[row_i, col_i])
            ax.set_facecolor("#0a0e1a")
            if col_i < 2:
                ax.imshow(mpimg.imread(paths[col_i]), interpolation="nearest")
                ax.axis("off")
                if row_i == 0:
                    ax.set_title(col_titles[col_i], fontsize=10, color="#9aa3b8", pad=4)
            elif col_i == 2:
                ax.axis("off")
                y = 0.88
                ax.text(
                    0.05,
                    y,
                    row_title,
                    fontsize=11,
                    color=accent,
                    fontweight="bold",
                    transform=ax.transAxes,
                )
                for line in bullets:
                    y -= 0.2
                    ax.text(0.05, y, f"• {line}", fontsize=9.5, color="#e6edf3", transform=ax.transAxes)
            else:
                ax.axis("off")
                if row_i == 0:
                    img = mpimg.imread(paths[1])
                    h, w = img.shape[:2]
                    cx, cy = w // 2, h // 2
                    half = min(w, h) // 5
                    crop = img[
                        max(0, cy - half) : min(h, cy + half),
                        max(0, cx - half) : min(w, cx + half),
                    ]
                    ax.imshow(crop, interpolation="nearest")
                    if row_i == 0:
                        ax.set_title(col_titles[3], fontsize=10, color="#9aa3b8", pad=4)
                else:
                    ax.axis("off")
    fig.suptitle("04 · 统计↔空间：Top 1% / Bottom 1% 双向验证 (t=99)", fontsize=13, color="#e6edf3")
    save_figure(fig, OUT / "task4_brush_rows.png", has_suptitle=True, pad=0.14)


def task3_story_panel(timeline: dict) -> None:
    """Section 03: overlay + sparklines with real ratios + t=99 KPI strip."""
    steps = timeline["timesteps"]
    s0, s99 = steps[0], steps[99]
    ts = [s["timestep"] for s in steps]
    std = [s["std"] for s in steps]
    span = [s["p99"] - s["p01"] for s in steps]
    tail = [s["tailMassAboveP99"] * 100 for s in steps]

    fig = plt.figure(figsize=(18, 9.5), facecolor="#0a0e1a")
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.2, 0.35], width_ratios=[1.1, 1], hspace=0.22, wspace=0.1)

    ax_hist = fig.add_subplot(gs[0, 0])
    ax_hist.imshow(mpimg.imread(OUT / "task3_hist_overlay.png"))
    ax_hist.axis("off")
    ax_hist.set_title("多时刻 log 直方图叠加", fontsize=11, color="#e6edf3", pad=6)

    specs = [
        (std, THEME["cyan"], "σ(t)", _ratio_label(s0["std"], s99["std"])),
        (span, THEME["purple"], "p99−p01", _ratio_label(span[0], span[-1])),
        (tail, THEME["gold"], "≥p99 体积%", _ratio_label(tail[0], tail[-1])),
    ]
    inner = gridspec.GridSpecFromSubplotSpec(3, 1, subplot_spec=gs[0, 1], hspace=0.35)
    for i, (y, color, title, badge) in enumerate(specs):
        sub = fig.add_subplot(inner[i])
        sub.plot(ts, y, color=color, lw=LINE_WIDTH)
        sub.fill_between(ts, y, alpha=0.12, color=color)
        sub.set_title(f"{title}  t=0→99  {badge}", fontsize=9, color="#e6edf3")
        sub.set_xlim(0, 99)
        style_axes(sub)

    kpi_gs = gridspec.GridSpecFromSubplotSpec(1, 4, subplot_spec=gs[1, :], wspace=0.12)
    kpis = [
        ("均值 μ", f"{s99['mean']:.3f}"),
        ("标准差 σ", f"{s99['std']:.4f}"),
        ("p99", f"{s99['p99']:.3f}"),
        ("≥p99 体积", f"{s99['tailMassAboveP99'] * 100:.2f}%"),
    ]
    for i, (label, val) in enumerate(kpis):
        ax_k = fig.add_subplot(kpi_gs[i])
        ax_k.set_facecolor("#1a2240")
        ax_k.axis("off")
        ax_k.text(0.5, 0.62, label, ha="center", fontsize=10, color="#9aa3b8", transform=ax_k.transAxes)
        ax_k.text(0.5, 0.28, val, ha="center", fontsize=13, color="#e6edf3", fontweight="bold", transform=ax_k.transAxes)
        for spine in ax_k.spines.values():
            spine.set_edgecolor("#3a4558")
    fig.suptitle("03 · 定量：密度两极化 (t=99 KPI)", fontsize=13, color="#e6edf3", y=0.98)
    save_figure(fig, OUT / "task3_story_panel.png", has_suptitle=True, pad=0.12)


def task1_hero_poster(timeline: dict) -> None:
    """Section 01: hero volume + vertical colorbar + metadata strip."""
    vmin, vmax = global_projection_domain(timeline)
    hero_path = resolve_vol_image(99, timeline)
    fig = plt.figure(figsize=(18, 8), facecolor="#0a0e1a")
    gs = gridspec.GridSpec(1, 3, width_ratios=[0.12, 1, 0.06], wspace=0.04)

    ax_meta = fig.add_subplot(gs[0, 0])
    ax_meta.set_facecolor("#0a0e1a")
    ax_meta.axis("off")
    meta_lines = ["128³", "100 步", "t=0…99", "气体密度 ρ", "Nyx 模拟"]
    for i, line in enumerate(meta_lines):
        ax_meta.text(
            0.5,
            0.88 - i * 0.16,
            line,
            ha="center",
            fontsize=11,
            color="#3dd6c6",
            transform=ax_meta.transAxes,
            bbox=dict(boxstyle="round,pad=0.35", facecolor="#1a2240", edgecolor="#3a4558"),
        )

    ax_img = fig.add_subplot(gs[0, 1])
    ax_img.imshow(mpimg.imread(hero_path))
    ax_img.axis("off")
    s99 = timeline["timesteps"][99]
    ax_img.set_title(f"01 · 宇宙网诞生 (t=99, σ={s99['std']:.3f})", fontsize=13, color="#e6edf3", pad=8)

    ax_cb = fig.add_subplot(gs[0, 2])
    sm = plt.cm.ScalarMappable(
        cmap=COSMIC_CMAP,
        norm=LogNorm(vmin=max(vmin, 1e-6), vmax=max(vmax, 1e-6)),
    )
    cb = fig.colorbar(sm, cax=ax_cb)
    cb.set_label("log₁₀ ρ\n(p01–p99)", color="#9aa3b8", fontsize=9)
    cb.ax.tick_params(colors="#9aa3b8", labelsize=8)
    save_figure(fig, OUT / "task1_hero_poster.png", pad=0.1)


def task5_mass_pie(timeline: dict) -> None:
    """Section 05: volume vs mass fraction for top/bottom tails (t=99)."""
    s99 = timeline["timesteps"][99]
    vol_top = s99["tailMassAboveP99"] * 100
    vol_bot = s99["tailMassBelowP01"] * 100
    mass_top = s99.get("massFractionAboveP99", 0) * 100
    mass_bot = s99.get("massFractionBelowP01", 0) * 100

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    pies = [
        (axes[0], vol_top, mass_top, "≥p99 尾区 (t=99)"),
        (axes[1], vol_bot, mass_bot, "≤p01 尾区 (t=99)"),
    ]
    for ax, vol_pct, mass_pct, title in pies:
        sizes = [vol_pct, 100 - vol_pct]
        colors = [THEME["gold"], "#2a3348"]
        ax.pie(
            sizes,
            labels=[f"体积 {vol_pct:.2f}%", f"其余 {100-vol_pct:.2f}%"],
            colors=colors,
            autopct="",
            startangle=90,
            textprops={"color": "#e6edf3", "fontsize": 9},
        )
        ax.set_title(f"{title}\n质量占比 {mass_pct:.1f}%", fontsize=11, color="#e6edf3")
    fig.suptitle("05 · 少数致密区：体积 vs 质量（Σρ 加权）", fontsize=12, color="#e6edf3")
    save_figure(fig, OUT / "task5_mass_pie.png", has_suptitle=True, pad=0.15)


def story_flow_chart() -> None:
    """Section 06: flowchart for reports / poster PNG (larger type than legacy)."""
    steps = [
        ("1", "Nyx 数据", "128³·100步"),
        ("2", "体渲染", "vtk.js"),
        ("3", "时序统计", "precompute"),
        ("4", "相空间刷选", "D3+Worker"),
        ("5", "空间映射", "XY 投影"),
        ("6", "验证分析", "亮脊/节点"),
        ("7", "科学发现", "宇宙网"),
    ]
    n = len(steps)
    fig_w = 22
    fig_h = 4.8
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor="#03030A")
    ax.set_facecolor("#03030A")
    ax.axis("off")
    box_w = 0.11
    gap = 0.018
    total = n * box_w + (n - 1) * gap
    x0 = (1 - total) / 2 + box_w / 2
    for i, (num, title, sub) in enumerate(steps):
        x = x0 + i * (box_w + gap)
        rect = plt.Rectangle(
            (x - box_w / 2, 0.22),
            box_w,
            0.52,
            facecolor="#121e38",
            edgecolor="#4ec4ff",
            linewidth=1.5,
            transform=ax.transAxes,
            zorder=1,
        )
        ax.add_patch(rect)
        ax.text(x, 0.82, num, ha="center", va="center", fontsize=16, color="#ff6b2c", fontweight="bold", transform=ax.transAxes)
        ax.text(x, 0.58, title, ha="center", va="center", fontsize=13, color="#f5f9ff", fontweight="bold", transform=ax.transAxes)
        ax.text(x, 0.38, sub, ha="center", va="center", fontsize=10, color="#8fa3c4", transform=ax.transAxes)
        if i < n - 1:
            xn = x0 + (i + 1) * (box_w + gap)
            ax.annotate(
                "",
                xy=(xn - box_w / 2 - 0.004, 0.48),
                xytext=(x + box_w / 2 + 0.004, 0.48),
                arrowprops=dict(arrowstyle="-|>", color="#ff6b2c", lw=2.2),
                transform=ax.transAxes,
            )
    fig.suptitle("06 · 分析流程：从涨落到宇宙网", fontsize=16, color="#f5f9ff", y=0.96)
    save_figure(fig, OUT / "task0_story_flow.png", has_suptitle=True, pad=0.12)


def _story_poster_panels(timeline: dict, out_name: str, bg: str = "#0a0e1a") -> None:
    s0, s99 = timeline["timesteps"][0], timeline["timesteps"][99]
    span0, span99 = s0["p99"] - s0["p01"], s99["p99"] - s99["p01"]
    header = [
        "宇宙网诞生记 · Nyx 128³ 气体密度",
        f"σ +{(s99['std']-s0['std'])/s0['std']*100:.1f}% · p99−p01 +{(span99-span0)/span0*100:.1f}%",
    ]
    items = [
        ("task1_hero_poster.png", 1.05),
        ("task1_vol_strip.png", 0.55),
        ("task3_story_panel.png", 0.85),
        ("task4_brush_rows.png", 0.95),
        ("task5_mass_pie.png", 0.5),
        ("task0_story_flow.png", 0.35),
    ]
    present = [(OUT / name, w) for name, w in items if (OUT / name).exists()]
    if not present:
        return
    poster = stitch_vertical_weighted(present, max_width=3840, gap=18, bg=bg, header_lines=header)
    save_pil_png(poster, OUT / out_name)
    print(f"Poster (PIL) {out_name}: {poster.width}×{poster.height}px")


def app_infographic_poster(timeline: dict) -> None:
    _story_poster_panels(timeline, "app_infographic_poster.png", bg="#050a14")


def task6_story_poster(timeline: dict) -> None:
    _story_poster_panels(timeline, "task6_story_poster.png")


def representative_poster(timeline: dict) -> None:
    sub = OUT.parent / "submission"
    sub.mkdir(parents=True, exist_ok=True)
    poster = OUT / "cosmic_poster_3840.png"
    if not poster.exists():
        poster = OUT / "task6_story_poster.png"
    if poster.exists():
        img = Image.open(poster).convert("RGB")
        sub.mkdir(parents=True, exist_ok=True)
        out_jpg = sub / "submission_representative.jpg"
        img.save(out_jpg, format="JPEG", quality=92, optimize=True)
        print(f"Representative from story poster: {out_jpg}")
        return

    fig = plt.figure(figsize=(16, 11), facecolor="#0a0e1a")
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.05, 1], hspace=0.1, wspace=0.06)

    hero = OUT / "task1_hero_poster.png"
    ax0 = fig.add_subplot(gs[0, :])
    ax0.imshow(mpimg.imread(hero if hero.exists() else OUT / "task1_vol_strip.png"))
    ax0.axis("off")
    ax0.set_title("任务一 · 体渲染 / Hero", fontsize=13, color="#e6edf3", pad=12)

    ax1 = fig.add_subplot(gs[1, 0])
    ax1.imshow(mpimg.imread(OUT / "task3_story_panel.png" if (OUT / "task3_story_panel.png").exists() else OUT / "task2_evolution_story.png"))
    ax1.axis("off")
    ax1.set_title("任务三 · 定量统计", fontsize=12, color="#e6edf3", pad=8)

    ax2 = fig.add_subplot(gs[1, 1])
    brush = OUT / "task4_brush_rows.png"
    ax2.imshow(mpimg.imread(brush if brush.exists() else OUT / "task4_brush_triptych.png"))
    ax2.axis("off")
    ax2.set_title("任务四 · 刷选验证", fontsize=12, color="#e6edf3", pad=8)

    s0, s99 = timeline["timesteps"][0], timeline["timesteps"][99]
    span0, span99 = s0["p99"] - s0["p01"], s99["p99"] - s99["p01"]
    fig.suptitle(
        f"从涨落到宇宙网 · Nyx 128³ | σ +{(s99['std']-s0['std'])/s0['std']*100:.1f}% | "
        f"p99−p01 +{(span99-span0)/span0*100:.1f}%",
        fontsize=14,
        color="#e6edf3",
        y=0.99,
    )
    save_figure(fig, sub / "submission_representative.jpg", has_suptitle=True, pad=0.12)


def main() -> int:
    if not STATS.exists():
        print("Run precompute first", file=sys.stderr)
        return 1

    OUT.mkdir(parents=True, exist_ok=True)
    timeline = json.loads(STATS.read_text(encoding="utf-8"))

    for t in REP_STEPS:
        vol_png = OUT / f"task1_vol_t{t:04d}.png"
        if not vol_png.exists():
            if not (NYX / f"{t:04d}.dat").exists():
                print(f"Missing Nyx/{t:04d}.dat", file=sys.stderr)
                return 1
            vmin, vmax = global_projection_domain(timeline)
            slice_figure(
                load_volume(NYX / f"{t:04d}.dat"),
                t,
                OUT / f"task1_slice_t{t:04d}.png",
                vmin,
                vmax,
            )
            print(f"Slice fallback: t={t}")
        else:
            print(f"Using vtk volume render: {vol_png}")

    task1_evo_frames(timeline)
    task1_strip(timeline)
    task2_evolution_story(timeline)
    task3_figures(timeline)

    vol99 = load_volume(NYX / "0099.dat")
    s99 = timeline["timesteps"][99]
    highlight = render_xy_projection(vol99, timeline, s99["p99"], s99["max"])
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(highlight, origin="lower")
    ax.set_title(f"Top 1% 体素 XY 投影 (t=99, ρ≥{s99['p99']:.2f})", fontsize=14)
    ax.axis("off")
    save_figure(fig, OUT / "task4_brush_top1.png", pad=0.16)

    highlight_bottom = render_xy_projection(vol99, timeline, s99["min"], s99["p01"])
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(highlight_bottom, origin="lower")
    ax.axis("off")
    save_figure(fig, OUT / "task4_brush_bottom_hl.png", pad=0.02)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(highlight, origin="lower")
    ax.axis("off")
    save_figure(fig, OUT / "task4_brush_top1_viz.png", pad=0.02)

    brush_projection(
        vol99,
        timeline,
        s99["min"],
        s99["p01"],
        "Bottom 1% 低密度 IGM 区域",
        OUT / "task4_brush_bottom1.png",
    )
    task4_histogram_brush(timeline, 99)
    task4_spatial_to_stats(vol99, timeline, 99)
    task4_triptych(timeline)
    task4_brush_rows(timeline)
    task3_story_panel(timeline)
    task1_hero_poster(timeline)
    task5_mass_pie(timeline)
    story_flow_chart()
    task6_story_poster(timeline)
    app_infographic_poster(timeline)
    try:
        from generate_poster_3840 import compose_poster_3840

        compose_poster_3840(timeline)
    except Exception as exc:
        print(f"Poster 3840 skipped: {exc}", file=sys.stderr)
    representative_poster(timeline)

    print(f"Figures written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
