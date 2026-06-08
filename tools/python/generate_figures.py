"""Generate static figures for tasks 1–4 into docs/figures/."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib import image as mpimg
from matplotlib.colors import LogNorm

from brush_analysis import export_brush_validation
from validation_suite import export_validation_extended, lighting_vectors
from projection_render import render_axis_projection, render_projection_rgb, render_xy_projection
from render_spec import (
    COSMIC_COLOR_STOPS,
    COSMIC_OPACITY_STOPS,
    DOMAIN_LENGTH,
    PRESENTATION_QUALITY,
    VOLUME_LIGHTING,
    compute_camera_spec,
    export_render_spec_json,
    value_at_norm_t,
)
from spatial_to_stats import filament_density_band
from viz_style import (
    COSMIC_CMAP,
    LINE_WIDTH,
    THEME,
    PANEL_BG,
    VIZ_BG,
    apply_dark_theme,
    compose_sectioned_poster,
    compose_sheet,
    global_projection_domain,
    hex_to_rgb,
    LABEL_BAR_H,
    PANEL_PAD,
    render_horizontal_colorbar_png,
    render_inset_panel,
    render_kpi_card,
    render_meta_badges,
    render_text_banner,
    render_vertical_colorbar_png,
    save_pil_png,
    stitch_panels_png,
    style_axes,
    save_figure,
    split_panel_label,
    wrap_panel,
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


def task1_transfer_function(timeline: dict) -> None:
    """Cosmic transfer function: color map + opacity vs log10 density."""
    vmin, vmax = global_projection_domain(timeline)
    rho = [value_at_norm_t(t, vmin, vmax) for t, _ in COSMIC_OPACITY_STOPS]
    opacity = [op for _, op in COSMIC_OPACITY_STOPS]

    fig = plt.figure(figsize=(13, 5.5), facecolor=VIZ_BG)
    gs = gridspec.GridSpec(2, 1, height_ratios=[0.42, 1], hspace=0.28)

    ax_c = fig.add_subplot(gs[0])
    ax_c.set_facecolor(PANEL_BG)
    grad = np.linspace(0, 1, 512).reshape(1, -1)
    ax_c.imshow(grad, aspect="auto", cmap=COSMIC_CMAP, extent=[vmin, vmax, 0, 1])
    ax_c.set_xscale("log")
    ax_c.set_yticks([])
    ax_c.set_xlabel("密度 ρ (log10 域映射)")
    ax_c.set_title("cosmic 颜色传递函数（RGB vs ρ）", fontsize=11, color="#e6edf3")
    for spine in ax_c.spines.values():
        spine.set_edgecolor("#3a4558")

    ax_o = fig.add_subplot(gs[1])
    ax_o.set_facecolor(PANEL_BG)
    ax_o.plot(rho, opacity, color=THEME["cyan"], lw=LINE_WIDTH, marker="o", markersize=5)
    ax_o.fill_between(rho, opacity, alpha=0.12, color=THEME["cyan"])
    ax_o.set_xscale("log")
    ax_o.set_ylim(0, 1.05)
    ax_o.set_xlabel("密度 ρ")
    ax_o.set_ylabel("不透明度 α")
    ax_o.set_title(
        f"不透明度传递函数（默认 opacityScale=1，域 p01–p99 ≈ [{vmin:.3f}, {vmax:.3f}]）",
        fontsize=11,
        color="#e6edf3",
    )
    for t, op in COSMIC_OPACITY_STOPS:
        if t in (0.0, 0.35, 0.72, 1.0):
            ax_o.annotate(f"t={t:.2f}\nα={op:.2f}", (value_at_norm_t(t, vmin, vmax), op), fontsize=8, color=THEME["muted"])
    style_axes(ax_o)
    fig.suptitle("任务一：cosmic 传递函数设计图", fontsize=12, color="#e6edf3")
    save_figure(fig, OUT / "task1_transfer_function.png", has_suptitle=True, pad=0.14)
    print(f"Transfer function: {OUT / 'task1_transfer_function.png'}")


def task1_strip(timeline: dict) -> None:
    paths = [resolve_vol_image(t, timeline) for t in REP_STEPS]
    panels = [
        wrap_panel(
            p,
            label=f"t={t}",
            subtitle=f"σ={timeline['timesteps'][t]['std']:.3f}",
            accent=THEME["cyan"],
            content_height=720,
        )
        for p, t in zip(paths, REP_STEPS)
    ]
    row = stitch_panels_png(panels, direction="horizontal", gap=20, max_width=5200)
    vmin, vmax = global_projection_domain(timeline)
    cbar = render_horizontal_colorbar_png(vmin, vmax, row.width, label="密度 ρ (log10, 全局 p01–p99)")
    final = compose_sheet(
        "宇宙网结构演化",
        "体渲染关键帧：气体密度宇宙学演化 (128³)",
        [row],
        max_width=row.width,
        footer=cbar,
    )
    save_pil_png(final, OUT / "task1_vol_strip.png")
    print(f"Vol strip (PIL): {OUT / 'task1_vol_strip.png'} ({final.width}×{final.height}px)")


def task2_spatial_metrics(timeline: dict, ext_val: dict | None = None) -> None:
    """Moran's I, ξ half-length, fractal dim, excess kurtosis — 2×2 sheet + split panels."""
    steps = timeline["timesteps"]
    ts = [s["timestep"] for s in steps]
    if "moransI" not in steps[0]:
        print("Skip task2_spatial_metrics: run npm run precompute", file=sys.stderr)
        return

    panel_specs = [
        ([s["moransI"] for s in steps], THEME["purple"], "Moran's I（6 邻域，3D）", "(a) Moran's I"),
        ([s.get("xiR1", 0) for s in steps], THEME["cyan"], "两点相关 ξ(r=1)（XY 投影）", "(b) ξ(r=1)"),
        ([s.get("fractalDimP90", 0) for s in steps], THEME["gold"], "分形维数 D（P90 亮脊掩膜）", "(c) 分形维 D"),
        ([s["excessKurtosis"] for s in steps], THEME["coral"], "超额峰度 κ−3", "(d) 超额峰度"),
    ]
    panel_paths: list[Path] = []
    for idx, (y, color, title, label) in enumerate(panel_specs):
        fig, ax = plt.subplots(figsize=(6.8, 3.1))
        ax.plot(ts, y, color=color, lw=LINE_WIDTH)
        ax.fill_between(ts, y, alpha=0.12, color=color)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("时间步")
        style_axes(ax)
        out = OUT / f"task2_spatial_panel_{idx}.png"
        save_figure(fig, out, pad=0.16)
        panel_paths.append(out)

    fig, axes = plt.subplots(2, 2, figsize=(14, 5))
    for ax, (y, color, title, _) in zip(axes.flat, panel_specs):
        ax.plot(ts, y, color=color, lw=LINE_WIDTH)
        ax.fill_between(ts, y, alpha=0.1, color=color)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("时间步")
        style_axes(ax)

    fig.suptitle("任务二：空间自相关与高阶统计（团块化空间证据）", fontsize=12)
    save_figure(fig, OUT / "task2_spatial_metrics.png", has_suptitle=True, pad=0.14)

    s0, s99 = steps[0], steps[99]
    boot = (ext_val or {}).get("bootstrapSpatial", {})
    xi_prof = boot.get("xiProfileBootstrap", {})
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8))
    from spatial_stats import max_projection_xy, radial_two_point_profile

    for ax, t, label, prof_key in zip(
        axes,
        [0, 99],
        [f"t=0  σ={s0['std']:.4f}", f"t=99  σ={s99['std']:.4f}"],
        ["t0", "t99"],
    ):
        vol = load_volume(NYX / f"{t:04d}.dat")
        radii, xi = radial_two_point_profile(max_projection_xy(vol))
        ax.plot(radii, xi, color=THEME["cyan"], lw=LINE_WIDTH, label="全域 XY 投影")
        if xi_prof.get("radii") and prof_key in xi_prof:
            br = np.array(xi_prof["radii"])
            mu = np.array(xi_prof[prof_key]["mean"])
            sd = np.array(xi_prof[prof_key]["std"])
            n = min(len(radii), len(br))
            ax.fill_between(
                br[:n],
                mu[:n] - sd[:n],
                mu[:n] + sd[:n],
                color=THEME["gold"],
                alpha=0.22,
                label="64³ 子块 MC ±1σ",
            )
        ax.axhline(0.5, color=THEME["muted"], ls="--", lw=1)
        ax.set_xlabel("r（像素）")
        ax.set_ylabel("ξ(r)")
        ax.set_title(f"两点相关函数 · {label}", fontsize=11)
        ax.legend(fontsize=8, loc="upper right")
        style_axes(ax)
    if boot.get("xiR1Global"):
        g = boot["xiR1Global"]
        fig.text(
            0.5,
            0.01,
            f"ξ(r=1) 全域：{g['t0']:.3f}→{g['t99']:.3f} (Δ={g['delta']:+.3f})；"
            f"子块 bootstrap 合并 σ≈{boot.get('pooledBootstrapStdXiR1', 0):.3f}",
            ha="center",
            fontsize=9,
            color="#9aa3b8",
        )
    fig.suptitle("XY 最大密度投影：ξ(r) 与 64³ 子块 Monte Carlo 误差带", fontsize=12)
    save_figure(fig, OUT / "task2_two_point_xi.png", has_suptitle=True, pad=0.16)


def task2_evolution_story(timeline: dict) -> None:
    steps = timeline["timesteps"]
    ts = [s["timestep"] for s in steps]
    span = [s["p99"] - s["p01"] for s in steps]
    tail = [s["tailMassAboveP99"] * 100 for s in steps]
    std = [s["std"] for s in steps]
    skew = [s["skewness"] for s in steps]

    specs = [
        (span, THEME["purple"], "分位跨度 p99−p01（团块化）"),
        (std, THEME["cyan"], "标准差 σ(t)"),
        (tail, THEME["gold"], "高密度尾体积占比 ≥p99 (%)"),
        (skew, THEME["coral"], "偏度 skew(t)"),
    ]

    for idx, (y, color, title) in enumerate(specs):
        fig, ax = plt.subplots(figsize=(6.8, 3.1))
        ax.fill_between(ts, y, alpha=0.12, color=color)
        ax.plot(ts, y, color=color, lw=LINE_WIDTH)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("时间步", fontsize=10)
        style_axes(ax)
        save_figure(fig, OUT / f"task2_evolution_panel_{idx}.png", pad=0.16)

    fig, axes = plt.subplots(2, 2, figsize=(14, 5))
    for ax, (y, color, title) in zip(axes.flat, specs):
        ax.fill_between(ts, y, alpha=0.12, color=color)
        ax.plot(ts, y, color=color, lw=LINE_WIDTH)
        ax.set_title(title, fontsize=11)
        ax.set_xlabel("时间步", fontsize=10)
        style_axes(ax)

    fig.suptitle("任务二：100 步全域统计揭示的演化规律", fontsize=12)
    save_figure(fig, OUT / "task2_evolution_story.png", has_suptitle=True, pad=0.14)


def _log_hist_for_bins(flat: np.ndarray, bin_count: int, vmin: float, vmax: float) -> tuple[np.ndarray, np.ndarray]:
    edges = np.logspace(np.log10(vmin), np.log10(vmax), bin_count + 1)
    counts, _ = np.histogram(flat, bins=edges)
    centers = np.sqrt(edges[:-1] * edges[1:])
    pct = counts / max(counts.sum(), 1) * 100.0
    return centers, pct


def task3_bin_sensitivity(timeline: dict) -> None:
    """64 / 128 / 256 log-bin overlay at t=0 and t=99."""
    gmin, gmax = timeline["globalMin"], timeline["globalMax"]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    styles = [(64, "-"), (128, "--"), (256, ":")]
    for ax, t in zip(axes, [0, 99]):
        flat = load_volume(NYX / f"{t:04d}.dat").ravel()
        for n_bins, ls in styles:
            centers, pct = _log_hist_for_bins(flat, n_bins, gmin, gmax)
            ax.plot(centers, pct, ls=ls, lw=1.8, label=f"{n_bins} bins")
        ax.set_xscale("log")
        ax.set_xlabel("密度 ρ（log10 轴，线性刻度标签）")
        ax.set_ylabel("Probability mass ×100\n(count/N×100, N=2,097,152)")
        ax.set_title(f"t={t} 分箱敏感度", fontsize=11)
        ax.legend(fontsize=9)
        style_axes(ax)
    fig.suptitle("任务三：log 直方图分箱数 64 / 128 / 256 对比（全域统一边界）", fontsize=12)
    save_figure(fig, OUT / "task3_bin_sensitivity.png", has_suptitle=True, pad=0.14)


def task3_void_evolution(timeline: dict) -> None:
    steps = timeline["timesteps"]
    ts = [s["timestep"] for s in steps]
    if "voidFractionBelowT0P10" not in steps[0]:
        print("Skip task3_void_evolution: rerun precompute", file=sys.stderr)
        return

    fig, axes = plt.subplots(1, 2, figsize=(14, 4.8))
    void_t0p10 = [s["voidFractionBelowT0P10"] * 100 for s in steps]
    void_t0p01 = [s["voidFractionBelowT0P01"] * 100 for s in steps]
    p01_curve = [s["p01"] for s in steps]
    p10_curve = [s.get("p10", s["p01"]) for s in steps]

    ax = axes[0]
    ax.plot(ts, void_t0p10, color=THEME["cyan"], lw=LINE_WIDTH, label="ρ ≤ ρ_p10(t=0)")
    ax.plot(ts, void_t0p01, color=THEME["blue"], lw=LINE_WIDTH, label="ρ ≤ ρ_p01(t=0)")
    ax.fill_between(ts, void_t0p10, alpha=0.12, color=THEME["cyan"])
    ax.set_xlabel("时间步")
    ax.set_ylabel("体积分数 %")
    ax.set_title("void 扩张：固定 t=0 低密度阈值的体素占比", fontsize=11)
    ax.legend(fontsize=9)
    style_axes(ax)

    ax = axes[1]
    ax.plot(ts, p01_curve, color=THEME["cyan"], lw=LINE_WIDTH, label="p01(t)")
    ax.plot(ts, p10_curve, color=THEME["purple"], lw=LINE_WIDTH, label="p10(t)")
    ax.set_xlabel("时间步")
    ax.set_ylabel("密度 ρ（线性刻度）")
    ax.set_title("低密度分位阈值随时间下移（void 深化）", fontsize=11)
    ax.legend(fontsize=9)
    style_axes(ax)

    fig.suptitle("任务三：低密度尾（void）定量追踪", fontsize=12)
    save_figure(fig, OUT / "task3_void_evolution.png", has_suptitle=True, pad=0.14)


def task3_figures(timeline: dict) -> None:
    edges = timeline["logBinEdges"]
    centers = [np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)]
    steps = timeline["timesteps"]
    colors = [THEME["purple"], THEME["blue"], THEME["cyan"], THEME["gold"], THEME["coral"]]

    task3_bin_sensitivity(timeline)
    task3_void_evolution(timeline)

    fig, ax = plt.subplots(figsize=(10, 6))
    ylabel = "Probability mass ×100\n(count/N×100, N=2,097,152)"
    for t, c in zip(REP_STEPS, colors):
        hist = timeline["histograms"][t]
        ax.plot(centers, [h * 100 for h in hist], label=f"t={t}", color=c, lw=LINE_WIDTH)
    ax.set_xscale("log")
    ax.set_ylabel(ylabel)
    ax.set_xlabel("密度 ρ（log10 轴；与表「直方图演化要点」中 p01/p50/p99 同单位）")
    ax.set_title("对数等距分箱直方图叠加（128 bins，代表步）", fontsize=11)
    ax.legend(loc="upper right", bbox_to_anchor=(1.0, 1.0), fontsize=9)
    style_axes(ax)
    save_figure(fig, OUT / "task3_hist_overlay.png", pad=0.14)

    ts = [s["timestep"] for s in steps]
    fig, ax = plt.subplots(figsize=(14, 5))
    means = [s["mean"] for s in steps]
    ax.fill_between(ts, means, alpha=0.15, color=THEME["purple"])
    ax.plot(ts, means, label="均值", color=THEME["purple"], lw=LINE_WIDTH)
    ax.plot(ts, [s["p99"] for s in steps], label="p99", color=THEME["gold"], lw=LINE_WIDTH)
    ax.plot(ts, [s["std"] for s in steps], label="σ", color=THEME["cyan"], lw=LINE_WIDTH)
    ax.set_xlabel("时间步")
    ax.set_ylabel("密度统计量")
    ax.set_title("100 时间步时序指标", fontsize=11)
    ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1.0), fontsize=9)
    style_axes(ax)
    save_figure(fig, OUT / "task3_metrics_timeline.png", pad=0.14)

    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    axes[0].plot(ts, [s["std"] for s in steps], color=THEME["cyan"], lw=LINE_WIDTH)
    axes[0].set_title("σ(t) 持续扩大", fontsize=11)
    axes[1].plot(ts, [s["skewness"] for s in steps], color=THEME["coral"], lw=LINE_WIDTH)
    axes[1].set_title("偏度 — 右尾增厚", fontsize=11)
    axes[2].plot(ts, [s["p99"] - s["p01"] for s in steps], color=THEME["purple"], lw=LINE_WIDTH)
    axes[2].set_title("p99−p01 分位跨度", fontsize=11)
    for ax in axes:
        ax.set_xlabel("t")
        style_axes(ax)
    save_figure(fig, OUT / "task3_evolution_metrics.png", pad=0.14)

    p50 = [s["p50"] for s in steps]
    p25 = [s.get("p25", s["p50"]) for s in steps]
    p75 = [s.get("p75", s["p50"]) for s in steps]
    fig, ax = plt.subplots(figsize=(14, 4.8))
    ax.fill_between(ts, p25, p75, alpha=0.22, color=THEME["gold"], label="p25–p75 四分位带")
    ax.plot(ts, p50, color=THEME["gold"], lw=LINE_WIDTH, label="p50（中位数密度）")
    ax.set_yscale("log")
    ax.set_xlabel("时间步 t")
    ax.set_ylabel("密度 ρ（log10 纵轴，值为线性 ρ）")
    ax.set_title("分布中心漂移：p50 轨迹与 p25–p75 不确定性带", fontsize=11)
    ax.legend(loc="upper right", fontsize=9)
    style_axes(ax)
    fig.suptitle("任务三：主峰/中位密度随时间演化（非直方图 argmax）", fontsize=12)
    save_figure(fig, OUT / "task3_peak_drift.png", has_suptitle=True, pad=0.14)


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


def task4_threshold_comparison(validation: dict) -> None:
    rows = validation["thresholds"]
    labels = [r["label"] for r in rows]
    vol_pct = [r["volumePct"] for r in rows]
    mass_pct = [r["massPct"] for r in rows]
    x = np.arange(len(labels))
    w = 0.35
    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(x - w / 2, vol_pct, w, label="体积占比 %", color=THEME["cyan"], alpha=0.9)
    ax.bar(x + w / 2, mass_pct, w, label="质量占比 %", color=THEME["gold"], alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylabel("占比 %")
    ax.set_title("任务四：右尾与纤维带阈值对比（t=99）")
    for i, r in enumerate(rows):
        ax.text(i - w / 2, vol_pct[i] + 0.3, f"{vol_pct[i]:.2f}%", ha="center", fontsize=7)
        ax.text(i + w / 2, mass_pct[i] + 0.3, f"{mass_pct[i]:.1f}%", ha="center", fontsize=7)
        if r.get("rhoMax") is not None:
            rho_txt = f"ρ∈[{r['rhoMin']:.2f},{r['rhoMax']:.2f}]"
        else:
            rho_txt = f"ρ≥{r['rhoMin']:.2f}"
        ax.text(i, -1.5, rho_txt, ha="center", fontsize=7, color="#9aa5b1")
    ax.legend()
    style_axes(ax)
    save_figure(fig, OUT / "task4_threshold_comparison.png", pad=0.22)


def task4_p88_sensitivity(validation: dict) -> None:
    rows = validation["p88Sweep"]
    pcts = [r["projPercentile"] for r in rows]
    ridge = [r["ridgePixelPct"] for r in rows]
    lo = [r["densityBand"][0] for r in rows]
    hi = [r["densityBand"][1] for r in rows]
    fig, ax1 = plt.subplots(figsize=(8.5, 4.2))
    ax1.plot(pcts, ridge, "o-", color=THEME["gold"], linewidth=LINE_WIDTH, label="亮脊像素占比 %")
    ax1.axvline(88, color=THEME["cyan"], linestyle="--", alpha=0.7, label="默认 P88")
    ax1.set_xlabel("投影百分位阈值")
    ax1.set_ylabel("亮脊像素占比 %")
    ax1.set_title("任务四：P88 亮脊阈值敏感度（t=99 XY）")
    ax2 = ax1.twinx()
    ax2.plot(pcts, lo, "s--", color=THEME["purple"], alpha=0.85, label="密度带下界")
    ax2.plot(pcts, hi, "^--", color=THEME["cyan"], alpha=0.85, label="密度带上界")
    ax2.set_ylabel("反查密度带 ρ")
    lines1, lab1 = ax1.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, lab1 + lab2, loc="upper left", fontsize=9)
    style_axes(ax1)
    save_figure(fig, OUT / "task4_p88_sensitivity.png", pad=0.2)


def task4_projection_axes(vol: np.ndarray, timeline: dict, s99: dict) -> None:
    lo, hi = float(s99["p99"]), float(s99["max"])
    axes_spec = [
        ("xy", "XY（俯视 z）"),
        ("xz", "XZ（侧视 y）"),
        ("yz", "YZ（侧视 x）"),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4.2))
    for ax, (axis, title) in zip(axes, axes_spec):
        rgb = render_axis_projection(vol, timeline, axis, lo, hi)
        ax.imshow(rgb, origin="lower")
        ax.set_title(f"{title} · Top 1% 高亮", fontsize=11)
        ax.axis("off")
    fig.suptitle(f"三向最大密度投影验证（t=99, ρ≥{lo:.2f}）", fontsize=12, color="#e6edf3")
    save_figure(fig, OUT / "task4_projection_axes.png", has_suptitle=True, pad=0.14)


def task4_brush_precision(validation: dict) -> None:
    m = validation["fpFnDefault"]
    labels = ["精确率\n(TP/(TP+FP))", "召回率\n(TP/(TP+FN))", "刷选误报率\n(FP/brush)", "代理漏报率\n(FN/proxy)"]
    vals = [
        m["precision"] * 100,
        m["recall"] * 100,
        m["fpRateInBrush"] * 100,
        m["fnRateInProxy"] * 100,
    ]
    colors = [THEME["gold"], THEME["cyan"], THEME["purple"], THEME["coral"]]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    bars = ax.bar(labels, vals, color=colors, alpha=0.9)
    ax.set_ylim(0, 105)
    ax.set_ylabel("占比 %")
    ax.set_title(
        f"刷选 vs filament 代理（P{m['projPercentile']:.0f}，t=99）\n"
        f"孤立高密体素 {m['isolatedHighDensityInBrush']:,} "
        f"({m['isolatedRateInBrush'] * 100:.2f}% of brush)"
    )
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1.5, f"{v:.1f}%", ha="center", fontsize=9)
    style_axes(ax)
    save_figure(fig, OUT / "task4_brush_precision.png", pad=0.22)


def task1_tf_gain_curve() -> None:
    ts = np.arange(100)
    t_norm = ts / 99.0
    opacity = 0.72 + t_norm * 0.38
    density_gain = np.where(t_norm < 0.45, -0.32 * (1.0 - t_norm / 0.45), 0.0)
    fig, ax1 = plt.subplots(figsize=(8.5, 4.2))
    ax1.plot(ts, opacity, color=THEME["gold"], lw=LINE_WIDTH, label="opacityScale（不透明度乘子）")
    ax1.set_xlabel("时间步 t")
    ax1.set_ylabel("opacityScale", color=THEME["gold"])
    ax2 = ax1.twinx()
    ax2.plot(ts, density_gain, color=THEME["cyan"], lw=LINE_WIDTH, ls="--", label="densityGain（ρ 轴平移；负=压低 IGM）")
    ax2.set_ylabel("densityGain", color=THEME["cyan"])
    ax2.axhline(0, color=THEME["muted"], lw=0.8, alpha=0.5)
    ax2.axvline(45, color=THEME["muted"], ls=":", alpha=0.7, label="t≈45 增益归零")
    lines1, lab1 = ax1.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, lab1 + lab2, loc="lower right", fontsize=9)
    ax1.set_title("capture 专用 TF 增益（仅 capture.html；交互页默认 opacityScale=1.15, densityGain=+0.12）")
    style_axes(ax1)
    save_figure(fig, OUT / "task1_tf_gain_curve.png", pad=0.18)


def task1_lighting_diagram() -> None:
    lit = lighting_vectors()
    fp = np.array(lit["focalPoint"])
    key = np.array(lit["keyLight"]["position"])
    fill = np.array(lit["fillLight"]["position"])
    fig = plt.figure(figsize=(8, 6))
    ax = fig.add_subplot(111, projection="3d")
    ax.scatter(*fp, color=THEME["gold"], s=80, label="焦点 / 体素域中心")
    ax.quiver(
        key[0], key[1], key[2],
        fp[0] - key[0], fp[1] - key[1], fp[2] - key[2],
        color=THEME["cyan"], arrow_length_ratio=0.08, linewidth=2, label="主光→中心",
    )
    ax.quiver(
        fill[0], fill[1], fill[2],
        fp[0] - fill[0], fp[1] - fill[1], fp[2] - fill[2],
        color=THEME["purple"], arrow_length_ratio=0.08, linewidth=2, label="补光→中心",
    )
    ax.set_xlim(0, DOMAIN_LENGTH * 1.6)
    ax.set_ylim(0, DOMAIN_LENGTH * 1.6)
    ax.set_zlim(0, DOMAIN_LENGTH * 1.6)
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    ph = lit["phong"]
    ax.set_title(
        f"Phong 光照示意（Ka={ph['Ka']}, Kd={ph['Kd']}, Ks={ph['Ks']}）",
        fontsize=11,
    )
    ax.legend(loc="upper left", fontsize=9)
    save_figure(fig, OUT / "task1_lighting_diagram.png", pad=0.12)


def task1_resolution_coarsening(ext: dict) -> None:
    rows = ext["resolutionCoarseningT99"]
    jboot = ext.get("resolutionJaccardBootstrapT99", {})
    labels = [r["label"] for r in rows]
    corr = [r["projCorrWith128"] for r in rows]
    jacc_fixed = [r["ridgeJaccardVs128"] for r in rows]
    x = np.arange(len(labels))
    w = 0.32
    fig, ax = plt.subplots(figsize=(9.2, 4.8))
    ax.bar(x - w / 2, corr, w, label="投影相关 r", color=THEME["cyan"])
    ax.bar(x + w / 2, jacc_fixed, w, color=THEME["gold"], alpha=0.45)
    if jboot and len(jacc_fixed) > 1:
        mean_j = jboot.get("jaccardMean", jacc_fixed[1])
        std_j = jboot.get("jaccardStd", 0)
        fixed_64 = jboot.get("jaccardFixedOrigin", jacc_fixed[1])
        xi = x[1] + w / 2
        ax.scatter([xi - 0.12], [fixed_64], marker="D", s=70, color=THEME["gold"], zorder=6, label="64³ 原点对齐")
        ax.errorbar(
            [xi + 0.12],
            mean_j,
            yerr=std_j,
            fmt="o",
            color="white",
            ecolor=THEME["coral"],
            capsize=6,
            lw=2.2,
            markersize=8,
            zorder=7,
            label=f"64³ 8 偏移 均值±1×样本SD (n={jboot.get('nReplicates', 8)})",
        )
        ax.annotate(
            f"原点\n{fixed_64:.2f}",
            xy=(xi - 0.12, fixed_64),
            xytext=(xi - 0.55, min(1.02, fixed_64 + 0.12)),
            fontsize=8,
            color=THEME["gold"],
            arrowprops=dict(arrowstyle="->", color=THEME["gold"], lw=1),
        )
        ax.annotate(
            f"偏移\n{mean_j:.3f}±{std_j:.3f}\n(±1 SD)",
            xy=(xi + 0.12, mean_j),
            xytext=(xi + 0.35, max(0.05, mean_j - 0.14)),
            fontsize=8,
            color=THEME["coral"],
            arrowprops=dict(arrowstyle="->", color=THEME["coral"], lw=1),
        )
    else:
        ax.bar(x + w / 2, jacc_fixed, w, label="filament 脊 Jaccard", color=THEME["gold"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("相对 128³ 保真度")
    ax.set_title("分辨率粗化敏感性（t=99）：原点对齐 vs 随机 lattice 偏移", fontsize=11)
    ax.legend(fontsize=7.5, loc="lower left", ncol=2)
    style_axes(ax)
    save_figure(fig, OUT / "task1_resolution_coarsening.png", pad=0.24)


def task2_bootstrap_ci(ext: dict) -> None:
    b = ext["bootstrapSpatial"]
    labels = ["Moran's I", "ξ(r=1)"]
    t0_means = [b["t0"]["moransI"]["mean"], b["t0"]["xiR1"]["mean"]]
    t0_std = [b["t0"]["moransI"]["std"], b["t0"]["xiR1"]["std"]]
    t99_means = [b["t99"]["moransI"]["mean"], b["t99"]["xiR1"]["mean"]]
    t99_std = [b["t99"]["moransI"]["std"], b["t99"]["xiR1"]["std"]]
    x = np.arange(2)
    w = 0.35
    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.bar(x - w / 2, t0_means, w, yerr=t0_std, capsize=4, label="t=0", color=THEME["purple"], alpha=0.9)
    ax.bar(x + w / 2, t99_means, w, yerr=t99_std, capsize=4, label="t=99", color=THEME["gold"], alpha=0.9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.set_title(f"空间统计 bootstrap 波动（n={b['nBootstrap']} 子窗口）")
    ax.legend()
    style_axes(ax)
    save_figure(fig, OUT / "task2_bootstrap_ci.png", pad=0.18)


def task3_bin_kl(ext: dict) -> None:
    sens = ext.get("binSensitivityT99", {})
    rows = sens.get("binRows", ext.get("binKlT99", []))
    bins = [r["bins"] for r in rows]
    linf = [r.get("cdfLinfVs128", r.get("klToSelf128", 0)) for r in rows]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar([str(b) for b in bins], linf, color=[THEME["purple"], THEME["cyan"], THEME["gold"]])
    ax.set_xlabel("分箱数")
    ax.set_ylabel("CDF L∞ 距（相对 128 bins）")
    ax.set_title("t=99 分箱敏感度：CDF 最大偏差（log 嵌套边界下 KL≈0 为恒等式）")
    style_axes(ax)
    save_figure(fig, OUT / "task3_bin_kl.png", pad=0.18)


def task5_lyalpha_flux(ext: dict) -> None:
    a, b = ext["lyalphaProxy"]["t0"], ext["lyalphaProxy"]["t99"]
    c0 = 0.5 * (np.array(a["edges"][:-1]) + np.array(a["edges"][1:]))
    c1 = 0.5 * (np.array(b["edges"][:-1]) + np.array(b["edges"][1:]))
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.plot(c0, a["hist"], color=THEME["purple"], lw=LINE_WIDTH, label="t=0 列密度 PDF")
    ax.plot(c1, b["hist"], color=THEME["gold"], lw=LINE_WIDTH, label="t=99 列密度 PDF")
    ax.set_xlabel("视线列平均密度（Lyα 通量代理）")
    ax.set_ylabel("概率密度")
    ax.set_title(f"Lyα 通量代理（{a['nSightlines']} 条 +z 视线；非 RT/非各向同性）")
    ax.legend()
    style_axes(ax)
    save_figure(fig, OUT / "task5_lyalpha_flux_proxy.png", pad=0.18)


def task5_lyalpha_direction_sensitivity(ext: dict) -> None:
    sens = ext.get("lyalphaDirectionSensitivity")
    if not sens:
        return
    t99 = sens["t99"]
    cmp = sens.get("t99Comparison", {})
    colors = {"+x": THEME["cyan"], "+y": THEME["purple"], "+z": THEME["gold"]}
    fig, ax = plt.subplots(figsize=(8.8, 4.4))
    for d in sens.get("directions", ["+x", "+y", "+z"]):
        bucket = t99[d]
        centers = 0.5 * (np.array(bucket["edges"][:-1]) + np.array(bucket["edges"][1:]))
        ax.plot(
            centers,
            bucket["hist"],
            color=colors.get(d, THEME["muted"]),
            lw=LINE_WIDTH,
            label=f"{d}  σ={bucket['fluxStd']:.4f}",
        )
    spread = cmp.get("stdSpreadRelPct", 0)
    ax.set_xlabel("视线列平均密度（t=99）")
    ax.set_ylabel("概率密度")
    ax.set_title(
        f"Lyα 代理方向敏感性（n={sens.get('nSightlines', 2000)}；"
        f"σ 极差 {spread:.2f}%；max L1={cmp.get('maxHistL1', 0):.3f}）"
    )
    ax.legend(fontsize=8)
    style_axes(ax)
    save_figure(fig, OUT / "task5_lyalpha_direction_sensitivity.png", pad=0.18)


def task4_brush_sample_recall(brush_val: dict) -> None:
    custom = brush_val.get("benchmark", {}).get("customBrushErrors", [])
    if custom:
        labels = [r["label"].replace("自定义：", "") for r in custom]
        reported_pct = [r["reportedOverTruePct"] for r in custom]
        fig, ax = plt.subplots(figsize=(9.5, 4.5))
        colors = [THEME["gold"] if "对照" in r["label"] else THEME["cyan"] for r in custom]
        bars = ax.barh(labels, reported_pct, color=colors, alpha=0.9)
        ax.axvline(100, color=THEME["muted"], ls="--", lw=1, label="100%（无低估）")
        ax.set_xlabel("仪表盘显示数 / 真值体素数 ×100 %")
        ax.set_title("自定义拖拽刷选：Worker 早停 KPI 相对真值（t=99, stride=2, maxPoints=8000）")
        for bar, r in zip(bars, custom):
            ax.text(
                bar.get_width() + 0.3,
                bar.get_y() + bar.get_height() / 2,
                f"{r['reportedCount']:,}/{r['trueVoxels']:,}",
                va="center",
                fontsize=7,
                color="#9aa5b1",
            )
        ax.legend(fontsize=8)
        style_axes(ax)
        save_figure(fig, OUT / "task4_custom_brush_error.png", pad=0.18)

    sample = brush_val.get("benchmark", {}).get("sampleRecall")
    if not sample:
        return
    fig, ax = plt.subplots(figsize=(7.5, 4))
    labels = ["真值体素召回", "网格覆盖率"]
    vals = [sample["recallVsTrue"] * 100, sample["gridCoverage"] * 100]
    bars = ax.bar(labels, vals, color=[THEME["gold"], THEME["cyan"]])
    ax.set_ylim(0, 105)
    ax.set_ylabel("占比 %")
    ax.set_title(
        f"Top 1% 早停采样（stride={sample['stride']}, max={sample['maxPoints']}）\n"
        f"命中 {sample['uniqueTrueFound']:,}/{sample['trueBrushVoxels']:,} 真值体素"
    )
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2, v + 1, f"{v:.1f}%", ha="center", fontsize=9)
    style_axes(ax)
    save_figure(fig, OUT / "task4_brush_sample_recall.png", pad=0.2)


def task4_ridge_methods(ext: dict) -> None:
    m = ext["ridgeMethodsT99"]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(
        ["Jaccard", "P88与梯度重叠"],
        [m["jaccard"] * 100, m["precisionP88vsGrad"] * 100],
        color=[THEME["gold"], THEME["purple"]],
    )
    ax.set_ylim(0, 105)
    ax.set_ylabel("重叠 %")
    ax.set_title("P88 亮脊 vs 梯度脊线(P92) 自动化对照（t=99）")
    style_axes(ax)
    save_figure(fig, OUT / "task4_ridge_methods.png", pad=0.18)


def compose_figure_stacks() -> None:
    """Merge sub-figures for compact doc (≤5 figs per task)."""
    stacks: list[tuple] = [
        (
            "task1_render_params.png",
            "渲染参数汇总",
            "(a) 传递函数 · (b) 光照 · (c) capture TF 增益",
            ["task1_transfer_function.png", "task1_lighting_diagram.png", "task1_tf_gain_curve.png"],
            "vertical",
            ["(a) 传递函数", "(b) Phong 光照", "(c) capture TF 增益"],
        ),
        (
            "task3_histogram_summary.png",
            "直方图时序指标汇总",
            "(a) σ/span · (b) p50 · (c) void",
            ["task3_evolution_metrics.png", "task3_peak_drift.png", "task3_void_evolution.png"],
            "vertical",
            ["(a) σ / span / 偏度", "(b) p50 轨迹", "(c) void 扩张"],
        ),
        (
            "task4_discovery_summary.png",
            "可视化驱动发现",
            "(a–c) Top 1% 三联 · (d) 空间→统计反查",
            ["task4_brush_triptych.png", "task4_spatial_to_stats.png"],
            "vertical",
            ["(a–c) Top 1% 三联", "(d) 空间→统计反查"],
        ),
        (
            "task4_brush_validation_summary.png",
            "刷选验证汇总",
            "(a) 阈值 · (b) KPI 误差 · (c) 早停召回",
            [
                "task4_threshold_comparison.png",
                "task4_custom_brush_error.png",
                "task4_brush_sample_recall.png",
            ],
            "vertical",
            ["(a) 阈值对比", "(b) 自定义 KPI 误差", "(c) Top 1% 早停召回"],
        ),
        (
            "task4_performance_summary.png",
            "刷选扩展验证",
            "(a) 三向投影 · (b) P88 · (c) 精确率 · (d) 脊线",
            [
                "task4_projection_axes.png",
                "task4_p88_sensitivity.png",
                "task4_brush_precision.png",
                "task4_ridge_methods.png",
            ],
            "grid2x2",
            ["(a) XY/XZ/YZ", "(b) P88 敏感度", "(c) 精确率/召回", "(d) 脊线方法"],
        ),
    ]
    for out_name, title, subtitle, parts, layout, sub_labels in stacks:
        paths = [OUT / p for p in parts if (OUT / p).exists()]
        if len(paths) < 2:
            print(f"Skip composite {out_name}: need ≥2 panels, got {len(paths)}")
            continue
        labels = sub_labels[: len(paths)]
        wrapped = []
        for p, lab in zip(paths, labels):
            letter, caption = split_panel_label(lab)
            wrapped.append(
                wrap_panel(p, label=caption, corner_letter=letter, accent=THEME["cyan"])
            )
        if layout == "grid2x2" and len(wrapped) >= 4:
            top = stitch_panels_png(wrapped[:2], direction="horizontal", gap=16, max_width=4800)
            bot = stitch_panels_png(wrapped[2:4], direction="horizontal", gap=16, max_width=4800)
            body = stitch_panels_png([top, bot], direction="vertical", gap=20, max_width=4800)
        else:
            body = stitch_panels_png(wrapped, direction="vertical", gap=16, max_width=4800)
        final = compose_sheet(title, subtitle, [body], max_width=min(body.width, 3840))
        save_pil_png(final, OUT / out_name)
        print(f"Composite {out_name}: {final.width}×{final.height}px")

    compose_task2_spatial_summary()


def compose_task2_spatial_summary() -> None:
    """(a)–(d) metric timelines + (e) ξ profile + (f) bootstrap."""
    panel_files = [OUT / f"task2_spatial_panel_{i}.png" for i in range(4)]
    if not all(p.exists() for p in panel_files):
        print("Skip task2_spatial_summary: missing split panels")
        return
    row1 = stitch_panels_png(
        [
            wrap_panel(
                panel_files[0],
                label="Moran's I 时序",
                corner_letter="(a)",
            ),
            wrap_panel(
                panel_files[1],
                label="ξ(r=1) 时序",
                corner_letter="(b)",
            ),
        ],
        direction="horizontal",
        gap=16,
        max_width=4800,
    )
    row2 = stitch_panels_png(
        [
            wrap_panel(
                panel_files[2],
                label="分形维 D",
                corner_letter="(c)",
            ),
            wrap_panel(
                panel_files[3],
                label="超额峰度 κ−3",
                corner_letter="(d)",
            ),
        ],
        direction="horizontal",
        gap=16,
        max_width=4800,
    )
    extras: list[Image.Image] = []
    xi = OUT / "task2_two_point_xi.png"
    boot = OUT / "task2_bootstrap_ci.png"
    if xi.exists():
        extras.append(
            wrap_panel(
                xi,
                label="ξ(r) 剖面 + 子块 MC ±1σ",
                corner_letter="(e)",
            )
        )
    if boot.exists():
        extras.append(
            wrap_panel(
                boot,
                label="Moran's I / ξ(r=1) bootstrap ±1σ",
                corner_letter="(f)",
            )
        )
    rows = [row1, row2] + extras
    body = stitch_panels_png(rows, direction="vertical", gap=18, max_width=4800)
    final = compose_sheet(
        "空间统计汇总",
        "(a)–(d) 时序四指标 · (e) ξ 剖面 · (f) bootstrap",
        [body],
        max_width=min(body.width, 3840),
    )
    save_pil_png(final, OUT / "task2_spatial_summary.png")
    print(f"Composite task2_spatial_summary.png: {final.width}×{final.height}px")


def task4_triptych(timeline: dict) -> None:
    paths = [
        OUT / "task4_hist_brush_top1.png",
        resolve_vol_image(99, timeline),
        OUT / "task4_brush_top1.png",
    ]
    labels = ["log 直方图刷选", "体渲染 (t=99)", "XY 投影验证"]
    letters = ["(a)", "(b)", "(c)"]
    accents = [THEME["gold"], THEME["cyan"], THEME["purple"]]
    panels = [
        wrap_panel(p, label=lab, corner_letter=letter, accent=acc, content_height=720)
        for p, lab, letter, acc in zip(paths, labels, letters, accents)
    ]
    row = stitch_panels_png(panels, direction="horizontal", gap=20, max_width=4800)
    final = compose_sheet(
        "相空间联动：Top 1% 高密度尾 → 宇宙网节点",
        "(a) log 直方图 · (b) 体渲染 · (c) XY 投影",
        [row],
        max_width=row.width,
    )
    save_pil_png(final, OUT / "task4_brush_triptych.png")
    print(f"Triptych (PIL): {OUT / 'task4_brush_triptych.png'} ({final.width}×{final.height}px)")


def _ratio_label(v0: float, v99: float) -> str:
    if abs(v0) < 1e-12:
        return "—"
    return f"+{(v99 - v0) / v0 * 100:.1f}%"


def task4_brush_rows(timeline: dict) -> None:
    """Section 04: Top/Bottom 1% rows — hist | projection | KPI | inset (PIL layout)."""
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
            ["统计刷选", "XY 投影", "结构要点", "局部放大"],
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
            ["统计刷选", "XY 投影", "结构要点", "局部放大"],
        ),
    ]
    row_images: list[Image.Image] = []
    content_h = 480
    kpi_w, kpi_h = 380, content_h + LABEL_BAR_H + PANEL_PAD * 2

    for row_title, paths, accent, bullets, col_labels in rows:
        hist = wrap_panel(paths[0], label=col_labels[0], accent=accent, content_height=content_h)
        proj = wrap_panel(paths[1], label=col_labels[1], accent=accent, content_height=content_h)
        kpi = render_kpi_card(row_title, bullets, accent, width=kpi_w, height=kpi_h)
        inset = render_inset_panel(paths[1], label=col_labels[3], accent=accent, crop_ratio=0.22)
        row_images.append(stitch_panels_png([hist, proj, kpi, inset], direction="horizontal", gap=16, max_width=5200))

    body = stitch_panels_png(row_images, direction="vertical", gap=24, max_width=5200)
    final = compose_sheet(
        "04 · 统计→空间：Top 1% / Bottom 1% 双向验证 (t=99)",
        None,
        [body],
        max_width=body.width,
    )
    save_pil_png(final, OUT / "task4_brush_rows.png")
    print(f"Brush rows (PIL): {OUT / 'task4_brush_rows.png'} ({final.width}×{final.height}px)")


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
    """Section 01: hero volume + vertical colorbar + metadata strip (PIL)."""
    vmin, vmax = global_projection_domain(timeline)
    hero_path = resolve_vol_image(99, timeline)
    s99 = timeline["timesteps"][99]

    meta = render_meta_badges(["128³", "100 步", "t=0…99", "气体密度 ρ", "Nyx 模拟"])
    hero = wrap_panel(
        hero_path,
        label=f"01 · 宇宙网诞生 (t=99)",
        subtitle=f"σ={s99['std']:.3f}",
        accent=THEME["cyan"],
        content_height=640,
    )
    cbar = render_vertical_colorbar_png(vmin, vmax, height=hero.height)

    gap = 20
    total_w = meta.width + gap + hero.width + gap + cbar.width
    total_h = max(meta.height, hero.height, cbar.height)
    canvas = Image.new("RGBA", (total_w, total_h), (*hex_to_rgb(VIZ_BG), 255))
    canvas.paste(meta, (0, (total_h - meta.height) // 2), meta)
    canvas.paste(hero, (meta.width + gap, 0), hero)
    canvas.paste(cbar, (meta.width + gap + hero.width + gap, (total_h - cbar.height) // 2), cbar)
    save_pil_png(canvas, OUT / "task1_hero_poster.png")
    print(f"Hero poster (PIL): {OUT / 'task1_hero_poster.png'} ({canvas.width}×{canvas.height}px)")


def task5_mass_pie(timeline: dict) -> None:
    """Section 05: volume vs mass fraction for top/bottom tails (t=99)."""
    s99 = timeline["timesteps"][99]
    vol_top = s99["tailMassAboveP99"] * 100
    vol_bot = s99["tailMassBelowP01"] * 100
    mass_top = s99.get("massFractionAboveP99", 0) * 100
    mass_bot = s99.get("massFractionBelowP01", 0) * 100

    fig, axes = plt.subplots(1, 2, figsize=(13, 5.5))
    pies = [
        (axes[0], vol_top, mass_top, "≥p99 尾区 (t=99)", THEME["gold"]),
        (axes[1], vol_bot, mass_bot, "≤p01 尾区 (t=99)", THEME["cyan"]),
    ]
    for ax, vol_pct, mass_pct, title, accent in pies:
        sizes = [vol_pct, 100 - vol_pct]
        colors = [accent, "#2a3348"]
        _wedges, _texts, _autotexts = ax.pie(
            sizes,
            labels=[f"体积 {vol_pct:.2f}%", f"其余 {100-vol_pct:.2f}%"],
            colors=colors,
            autopct="",
            startangle=90,
            wedgeprops=dict(width=0.42, edgecolor=VIZ_BG, linewidth=2),
            textprops={"color": "#e6edf3", "fontsize": 9},
        )
        ax.text(0, 0, f"质量\n{mass_pct:.1f}%", ha="center", va="center", fontsize=14, color="#e6edf3", fontweight="bold")
        ax.set_title(title, fontsize=11, color="#e6edf3", pad=12)
    axes[0].axvline(x=0, color="#3a4558", linewidth=1, alpha=0)
    fig.suptitle("05 · 少数致密区：体积 vs 质量（Σρ 加权）", fontsize=12, color="#e6edf3")
    fig.subplots_adjust(wspace=0.35)
    save_figure(fig, OUT / "task5_mass_pie.png", has_suptitle=True, pad=0.15)


def story_flow_chart() -> None:
    """Section 06: flowchart for reports / poster PNG."""
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
    fig_h = 5.2
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), facecolor=VIZ_BG)
    ax.set_facecolor(VIZ_BG)
    ax.axis("off")
    box_w = 0.11
    gap = 0.018
    total = n * box_w + (n - 1) * gap
    x0 = (1 - total) / 2 + box_w / 2
    for i, (num, title, sub) in enumerate(steps):
        x = x0 + i * (box_w + gap)
        rect = plt.Rectangle(
            (x - box_w / 2, 0.20),
            box_w,
            0.56,
            facecolor="#121e38",
            edgecolor=THEME["cyan"],
            linewidth=2,
            transform=ax.transAxes,
            zorder=1,
            joinstyle="round",
        )
        ax.add_patch(rect)
        ax.text(x, 0.84, num, ha="center", va="center", fontsize=17, color=THEME["gold"], fontweight="bold", transform=ax.transAxes)
        ax.text(x, 0.58, title, ha="center", va="center", fontsize=14, color="#f5f9ff", fontweight="bold", transform=ax.transAxes)
        ax.text(x, 0.36, sub, ha="center", va="center", fontsize=10, color=THEME["muted"], transform=ax.transAxes)
        if i < n - 1:
            xn = x0 + (i + 1) * (box_w + gap)
            ax.text(
                (x + box_w / 2 + xn - box_w / 2) / 2,
                0.48,
                "→",
                ha="center",
                va="center",
                fontsize=20,
                color=THEME["gold"],
                fontweight="bold",
                transform=ax.transAxes,
            )
    fig.suptitle("06 · 分析流程：从涨落到宇宙网", fontsize=16, color="#f5f9ff", y=0.96)
    save_figure(fig, OUT / "task0_story_flow.png", has_suptitle=True, pad=0.12)


def _story_poster_panels(timeline: dict, out_name: str, bg: str = VIZ_BG) -> None:
    s0, s99 = timeline["timesteps"][0], timeline["timesteps"][99]
    span0, span99 = s0["p99"] - s0["p01"], s99["p99"] - s99["p01"]
    header_title = "宇宙网诞生记 · Nyx 128³ 气体密度"
    header_sub = f"σ +{(s99['std']-s0['std'])/s0['std']*100:.1f}% · p99−p01 +{(span99-span0)/span0*100:.1f}%"

    sections: list[tuple[str, str | None, list[Path | str]]] = []
    mapping = [
        ("01 · 体渲染 Hero", "t=99 代表帧与 log 色标", "task1_hero_poster.png"),
        ("02 · 五帧演化条带", "统一相机与色标", "task1_vol_strip.png"),
        ("03 · 定量统计", "直方图叠加与时序 KPI", "task3_story_panel.png"),
        ("04 · 刷选验证", "Top/Bottom 1% 双向联动", "task4_brush_rows.png"),
        ("05 · 质量占比", "体积 vs 质量（Σρ 加权）", "task5_mass_pie.png"),
        ("06 · 分析流程", "从数据到科学发现", "task0_story_flow.png"),
    ]
    for title, sub, fname in mapping:
        p = OUT / fname
        if p.exists():
            sections.append((title, sub, [p]))

    if not sections:
        return

    poster = compose_sectioned_poster(
        sections,
        header_title=header_title,
        header_subtitle=header_sub,
        max_width=3840,
        bg=bg,
    )
    save_pil_png(poster, OUT / out_name)
    print(f"Poster (PIL) {out_name}: {poster.width}×{poster.height}px")


def app_infographic_poster(timeline: dict) -> None:
    _story_poster_panels(timeline, "app_infographic_poster.png", bg="#050a14")


def task6_story_poster(timeline: dict) -> None:
    _story_poster_panels(timeline, "task6_story_poster.png")


def capture_app_html_poster() -> bool:
    """Playwright 全页截取 /app.html → _app_poster_capture_resized + task6 副本。"""
    is_win = sys.platform == "win32"
    try:
        subprocess.run(
            ["npm", "run", "capture-app-poster"],
            cwd=ROOT,
            check=True,
            shell=is_win,
        )
    except subprocess.CalledProcessError as exc:
        print(f"app.html capture failed: {exc}", file=sys.stderr)
        return False
    ok = (OUT / "_app_poster_capture_resized.png").is_file()
    if ok:
        print(f"app.html capture OK: {OUT / '_app_poster_capture_resized.png'}")
    return ok


def representative_poster(timeline: dict) -> None:
    sub = OUT.parent / "submission"
    sub.mkdir(parents=True, exist_ok=True)
    # 赛题代表图：/app.html 交互长卷 Playwright 全页截取（与 run.py 默认入口一致）
    poster_candidates = (
        OUT / "_app_poster_capture_resized.png",
        OUT / "task6_story_poster.png",
        OUT / "app_infographic_poster.png",
        OUT / "cosmic_poster_3840.png",
    )
    poster = next((p for p in poster_candidates if p.exists()), None)
    if poster is not None:
        img = Image.open(poster).convert("RGB")
        out_jpg = sub / "submission_representative.jpg"
        img.save(out_jpg, format="JPEG", quality=92, optimize=True)
        mb = out_jpg.stat().st_size / (1024 * 1024)
        print(f"Representative from {poster.name}: {out_jpg} ({mb:.2f} MB)")
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

    export_render_spec_json(OUT / "render_spec.json")
    export_render_spec_json(ROOT / "public" / "stats" / "render_spec.json")
    print(f"Render spec: {OUT / 'render_spec.json'}")

    task1_evo_frames(timeline)
    task1_transfer_function(timeline)
    task1_strip(timeline)
    task2_evolution_story(timeline)
    ext_val = export_validation_extended(timeline, ROOT / "public" / "stats" / "validation_extended.json")
    export_validation_extended(timeline, OUT / "validation_extended.json")
    task2_spatial_metrics(timeline, ext_val)
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
    brush_val = export_brush_validation(timeline, ROOT / "public" / "stats" / "brush_validation.json")
    export_brush_validation(timeline, OUT / "brush_validation.json")
    task1_lighting_diagram()
    task1_tf_gain_curve()
    task1_resolution_coarsening(ext_val)
    task2_bootstrap_ci(ext_val)
    task3_bin_kl(ext_val)
    task5_lyalpha_flux(ext_val)
    task5_lyalpha_direction_sensitivity(ext_val)
    task4_threshold_comparison(brush_val)
    task4_p88_sensitivity(brush_val)
    task4_projection_axes(vol99, timeline, s99)
    task4_brush_precision(brush_val)
    task4_brush_sample_recall(brush_val)
    task4_ridge_methods(ext_val)
    task4_triptych(timeline)
    task4_brush_rows(timeline)
    compose_figure_stacks()
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
    if not capture_app_html_poster():
        print(
            "Warning: /app.html capture unavailable — representative falls back to PIL story poster",
            file=sys.stderr,
        )
    representative_poster(timeline)

    print(f"Figures written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
