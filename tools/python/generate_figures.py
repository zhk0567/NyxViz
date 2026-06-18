"""Generate static figures for tasks 1–4 into docs/figures/."""
from __future__ import annotations

import io
import json
import subprocess
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from matplotlib import image as mpimg
from matplotlib.colors import LogNorm
from matplotlib.ticker import FixedFormatter, FixedLocator, MultipleLocator, NullFormatter

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
    FIG_DPI,
    LINE_WIDTH,
    THEME,
    PANEL_BG,
    VIZ_BG,
    apply_dark_theme,
    center_crop_box,
    draw_zoom_crop_marker,
    draw_zoom_connector_lines,
    estimate_inline_header_h,
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
    flow_connector_vertical,
    fit_panel_height,
    fit_panel_width,
    fit_panel_contain,
    load_ui_font,
    pad_panel_to_height,
    stitch_panels_flow,
    stitch_panels_png,
    style_axes,
    set_tick_density,
    save_figure,
    split_panel_label,
    wrap_panel,
)
from PIL import Image, ImageDraw

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

    fig = plt.figure(figsize=(13, 7.0), facecolor=VIZ_BG)
    gs = gridspec.GridSpec(2, 1, height_ratios=[0.36, 1], hspace=0.52)

    ax_c = fig.add_subplot(gs[0])
    ax_c.set_facecolor(PANEL_BG)
    grad = np.linspace(0, 1, 512).reshape(1, -1)
    ax_c.imshow(grad, aspect="auto", cmap=COSMIC_CMAP, extent=[vmin, vmax, 0, 1])
    ax_c.set_xscale("log")
    ax_c.set_yticks([])
    ax_c.set_xlabel("密度 ρ (log10 域映射)", fontsize=16, color=THEME["muted"], labelpad=8)
    ax_c.set_title("cosmic 颜色传递函数（RGB vs ρ）", fontsize=18, color="#e6edf3", pad=12)
    ax_c.tick_params(colors=THEME["muted"], labelsize=14)
    for spine in ax_c.spines.values():
        spine.set_edgecolor("#3a4558")
    set_tick_density(ax_c, factor=2.5, axes="x")

    ax_o = fig.add_subplot(gs[1])
    ax_o.set_facecolor(PANEL_BG)
    ax_o.plot(rho, opacity, color=THEME["cyan"], lw=LINE_WIDTH, marker="o", markersize=6, zorder=2)
    ax_o.fill_between(rho, opacity, alpha=0.12, color=THEME["cyan"], zorder=1)
    ax_o.set_xscale("log")
    ax_o.set_ylim(-0.02, 1.14)
    ax_o.set_xlabel("密度 ρ", fontsize=16, color=THEME["muted"], labelpad=10)
    ax_o.set_ylabel("不透明度 α", fontsize=16, color=THEME["muted"], labelpad=10)
    ax_o.set_title(
        f"不透明度传递函数（opacityScale=1 · p01–p99 ≈ [{vmin:.3f}, {vmax:.3f}]）",
        fontsize=17,
        color="#e6edf3",
        pad=16,
    )
    # Leader-line callouts: (normalized knot t, offset pt, ha, va)
    callouts: list[tuple[float, tuple[int, int], str, str]] = [
        (0.0, (22, 34), "left", "bottom"),
        (0.35, (22, 38), "left", "bottom"),
        (0.72, (-12, 42), "right", "bottom"),
        (1.0, (26, 36), "left", "bottom"),
    ]
    callout_ts = {t for t, *_ in callouts}
    for t_norm, op in COSMIC_OPACITY_STOPS:
        if t_norm not in callout_ts:
            continue
        x = value_at_norm_t(t_norm, vmin, vmax)
        spec = next(c for c in callouts if c[0] == t_norm)
        _, (dx, dy), ha, va = spec
        ax_o.scatter([x], [op], s=72, color=THEME["cyan"], edgecolors="#e6edf3", linewidths=1.2, zorder=4)
        ax_o.annotate(
            f"ρ={x:.2f}\nα={op:.2f}",
            xy=(x, op),
            xytext=(dx, dy),
            textcoords="offset points",
            fontsize=14,
            color="#e6edf3",
            ha=ha,
            va=va,
            zorder=5,
            bbox=dict(
                boxstyle="round,pad=0.35",
                fc=(15 / 255, 20 / 255, 36 / 255, 0.92),
                ec=THEME["cyan"],
                lw=1.0,
            ),
            arrowprops=dict(
                arrowstyle="-|>",
                color=THEME["cyan"],
                lw=1.4,
                shrinkA=0,
                shrinkB=5,
                connectionstyle="arc3,rad=0.08",
            ),
        )
    style_axes(ax_o, labelsize=14)
    set_tick_density(ax_o, factor=2.5, axes="xy")
    save_figure(fig, OUT / "task1_transfer_function.png", pad=0.16)
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
            label_font_size=64,
            subtitle_font_size=48,
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
        title_font_size=80,
        subtitle_font_size=54,
        title_pad_y=44,
        title_pad_x=36,
    )
    save_pil_png(final, OUT / "task1_vol_strip.png")
    print(f"Vol strip (PIL): {OUT / 'task1_vol_strip.png'} ({final.width}×{final.height}px)")


def _style_spatial_timeline_ax(
    ax,
    ts: list[int],
    y: list[float],
    color: str,
    *,
    fmt: str = "{:.4f}",
    flat_note: str | None = None,
) -> None:
    """Tight Y + t=0/t=99 callouts for spatial metric timelines."""
    ax.set_facecolor(PANEL_BG)
    ax.fill_between(ts, y, alpha=0.15, color=color)
    ax.plot(ts, y, color=color, lw=LINE_WIDTH, zorder=3)
    lo, hi = min(y), max(y)
    margin = max((hi - lo) * 0.22, abs(hi) * 0.020 if hi else 1e-6, 1e-6)
    ax.set_ylim(lo - margin, hi + margin)

    _callout_bbox = dict(
        boxstyle="round,pad=0.28",
        fc=(15 / 255, 20 / 255, 36 / 255, 0.94),
        lw=0.8,
    )
    ax.axvline(0, color=THEME["muted"], ls=":", lw=0.9, alpha=0.45, zorder=1)
    ax.axvline(99, color=THEME["muted"], ls=":", lw=0.9, alpha=0.45, zorder=1)
    for t, val in ((0, y[0]), (99, y[-1])):
        ax.scatter([t], [val], color=color, s=48, zorder=6, edgecolors="#e6edf3", linewidths=0.9)
    bbox = {**_callout_bbox, "ec": color}
    arrow = dict(arrowstyle="-", color=color, lw=0.8, shrinkA=0, shrinkB=1)
    ylo, yhi = ax.get_ylim()
    dy0 = (yhi - ylo) * 0.042
    dy99 = (yhi - ylo) * 0.030
    ax.annotate(
        f"t=0\n{fmt.format(y[0])}",
        xy=(0, y[0]),
        xytext=(2.2, y[0] + dy0),
        textcoords="data",
        fontsize=11,
        color=color,
        ha="left",
        va="bottom",
        bbox=bbox,
        arrowprops=arrow,
        zorder=8,
    )
    ax.annotate(
        f"t=99\n{fmt.format(y[-1])}",
        xy=(99, y[-1]),
        xytext=(96.8, y[-1] + dy99),
        textcoords="data",
        fontsize=11,
        color=color,
        ha="right",
        va="bottom",
        bbox=bbox,
        arrowprops=arrow,
        zorder=8,
    )

    if flat_note:
        badge = flat_note
    elif abs(y[0]) > 1e-12:
        pct = (y[-1] - y[0]) / abs(y[0]) * 100
        badge = f"t=0→99  {pct:+.2f}%" if abs(pct) >= 0.01 else f"≈{fmt.format(y[-1])} 维持"
    else:
        badge = f"Δ={y[-1] - y[0]:+.4f}"
    ax.text(
        0.97,
        0.08,
        badge,
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=12,
        color="#e6edf3",
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.32", fc=(15 / 255, 20 / 255, 36 / 255, 0.9), ec="#3a4558", lw=1),
    )
    ax.set_xlabel("时间步 t", fontsize=13, color=THEME["muted"], labelpad=4)
    style_axes(ax, labelsize=12)
    set_tick_density(ax, factor=2.5, axes="y")


def task2_spatial_metrics(timeline: dict, ext_val: dict | None = None) -> None:
    """Moran's I, ξ half-length, fractal dim, excess kurtosis — 2×2 sheet + split panels."""
    steps = timeline["timesteps"]
    ts = [s["timestep"] for s in steps]
    if "moransI" not in steps[0]:
        print("Skip task2_spatial_metrics: run npm run precompute", file=sys.stderr)
        return

    XI_COMPARE_MAX_R = 32

    panel_specs = [
        ([s["moransI"] for s in steps], THEME["purple"], "Moran's I（6 邻域，3D）", "{:.4f}", None),
        ([s.get("xiR1", 0) for s in steps], THEME["cyan"], "两点相关 ξ(r=1)（XY 投影）", "{:.4f}", None),
        ([s.get("fractalDimP90", 0) for s in steps], THEME["gold"], "分形维数 D（P90 亮脊掩膜）", "{:.3f}", "≈2.0 维持"),
        ([s["excessKurtosis"] for s in steps], THEME["coral"], "超额峰度 κ−3", "{:.3f}", None),
    ]
    for idx, (y, color, title, fmt, flat_note) in enumerate(panel_specs):
        fig, ax = plt.subplots(figsize=(7.4, 2.75), facecolor=VIZ_BG)
        _style_spatial_timeline_ax(ax, ts, y, color, fmt=fmt, flat_note=flat_note)
        fig.subplots_adjust(top=0.97, bottom=0.17, left=0.12, right=0.97)
        save_figure(fig, OUT / f"task2_spatial_panel_{idx}.png", pad=0.08, skip_tight=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 5.8), facecolor=VIZ_BG)
    for ax, (y, color, title, fmt, flat_note) in zip(axes.flat, panel_specs):
        _style_spatial_timeline_ax(ax, ts, y, color, fmt=fmt, flat_note=flat_note)
    fig.suptitle("任务二：空间自相关与高阶统计（团块化空间证据）", fontsize=14, color="#e6edf3", y=0.98)
    fig.subplots_adjust(top=0.90, bottom=0.10, left=0.08, right=0.98, hspace=0.38, wspace=0.28)
    save_figure(fig, OUT / "task2_spatial_metrics.png", pad=0.12, skip_tight=True)

    s0, s99 = steps[0], steps[99]
    boot = (ext_val or {}).get("bootstrapSpatial", {})
    xi_prof = boot.get("xiProfileBootstrap", {})
    xi_note = ""
    if boot.get("xiR1Global"):
        g = boot["xiR1Global"]
        xi_note = (
            f"ξ(r=1) 全域 {g['t0']:.3f}→{g['t99']:.3f} (Δ={g['delta']:+.3f}) · "
            f"bootstrap σ≈{boot.get('pooledBootstrapStdXiR1', 0):.3f}"
        )

    from spatial_stats import max_projection_xy, radial_two_point_profile

    fig, axes = plt.subplots(1, 2, figsize=(13.5, 3.85), facecolor=VIZ_BG)
    for ax, t, label, prof_key in zip(
        axes,
        [0, 99],
        [f"t=0  σ={s0['std']:.4f}", f"t=99  σ={s99['std']:.4f}"],
        ["t0", "t99"],
    ):
        ax.set_facecolor(PANEL_BG)
        vol = load_volume(NYX / f"{t:04d}.dat")
        radii, xi = radial_two_point_profile(max_projection_xy(vol), max_r=XI_COMPARE_MAX_R)
        ax.plot(radii, xi, color=THEME["cyan"], lw=LINE_WIDTH, label="全域 128³ XY 投影", zorder=3)
        if xi_prof.get("radii") and prof_key in xi_prof:
            br = np.array(xi_prof["radii"])
            mu = np.array(xi_prof[prof_key]["mean"])
            sd = np.array(xi_prof[prof_key]["std"])
            lo_band = mu - sd
            hi_band = mu + sd
            ax.fill_between(
                br,
                lo_band,
                hi_band,
                color=THEME["gold"],
                alpha=0.38,
                label="64³ 子块 MC ±1σ",
                zorder=2,
            )
            ax.plot(
                br,
                hi_band,
                color=THEME["gold"],
                lw=1.4,
                alpha=0.92,
                ls=(0, (4, 3)),
                zorder=2,
            )
            ax.plot(
                br,
                lo_band,
                color=THEME["gold"],
                lw=1.4,
                alpha=0.92,
                ls=(0, (4, 3)),
                zorder=2,
            )
        ax.axhline(0.5, color=THEME["muted"], ls="--", lw=1, alpha=0.7, zorder=1)
        ax.set_xlim(0.8, XI_COMPARE_MAX_R + 0.6)
        ax.set_xlabel("r（像素）", fontsize=13, color=THEME["muted"])
        ax.set_ylabel("ξ(r)", fontsize=13, color=THEME["muted"])
        ax.set_title(f"两点相关 · {label}", fontsize=12, color="#e6edf3", pad=4)
        ax.legend(fontsize=11, loc="upper right", framealpha=0.92, facecolor=(12 / 255, 16 / 255, 28 / 255, 0.92), edgecolor="#3a4558")
        style_axes(ax, labelsize=12)
        set_tick_density(ax, factor=2.0, axes="y")

    fig.subplots_adjust(top=0.90, bottom=0.16, left=0.07, right=0.98, wspace=0.26)
    save_figure(fig, OUT / "task2_two_point_xi.png", pad=0.08, skip_tight=True)
    xi_sub = f"对比区间 r≤{XI_COMPARE_MAX_R}（全域线截断至与子块 bootstrap 一致）"
    if xi_note:
        xi_sub += f" · {xi_note}"
    (OUT / "task2_spatial_wrap_meta.json").write_text(
        json.dumps({"xi_subtitle": xi_sub}, ensure_ascii=False),
        encoding="utf-8",
    )


def task2_evolution_story(timeline: dict) -> None:
    steps = timeline["timesteps"]
    ts = [s["timestep"] for s in steps]
    span = [s["p99"] - s["p01"] for s in steps]
    tail = [s["tailMassAboveP99"] * 100 for s in steps]
    std = [s["std"] for s in steps]
    skew = [s["skewness"] for s in steps]
    s0, s99 = steps[0], steps[-1]
    span_pct = (span[-1] - span[0]) / span[0] * 100
    std_pct = (std[-1] - std[0]) / std[0] * 100

    fig = plt.figure(figsize=(12, 7.2), facecolor=VIZ_BG)
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.15, 0.72], hspace=0.42, wspace=0.30)
    axes = [fig.add_subplot(gs[i, j]) for i in range(2) for j in range(2)]

    def _tight_ylim(ax, y: list[float], *, pad_frac: float = 0.14) -> None:
        lo, hi = min(y), max(y)
        margin = max((hi - lo) * pad_frac, abs(hi) * 0.02, 1e-6)
        ax.set_ylim(lo - margin, hi + margin)

    _callout_bbox = dict(
        boxstyle="round,pad=0.28",
        fc=(15 / 255, 20 / 255, 36 / 255, 0.94),
        lw=0.8,
    )

    def _mark_key_steps(ax, y: list[float], color: str, *, fmt: str) -> None:
        ax.axvline(0, color=THEME["muted"], ls=":", lw=0.9, alpha=0.45, zorder=1)
        ax.axvline(99, color=THEME["muted"], ls=":", lw=0.9, alpha=0.45, zorder=1)
        for t, val in ((0, y[0]), (99, y[-1])):
            ax.scatter([t], [val], color=color, s=52, zorder=6, edgecolors="#e6edf3", linewidths=0.9)
        bbox = {**_callout_bbox, "ec": color}
        arrow = dict(arrowstyle="-", color=color, lw=0.8, shrinkA=0, shrinkB=1)
        ylo, yhi = ax.get_ylim()
        dy_start = (yhi - ylo) * 0.040
        dy_end = (yhi - ylo) * 0.026
        dx = 2.0
        ax.annotate(
            f"t=0\n{fmt.format(y[0])}",
            xy=(0, y[0]),
            xytext=(dx, y[0] + dy_start),
            textcoords="data",
            fontsize=11,
            color=color,
            ha="left",
            va="bottom",
            bbox=bbox,
            arrowprops=arrow,
            zorder=8,
        )
        ax.annotate(
            f"t=99\n{fmt.format(y[-1])}",
            xy=(99, y[-1]),
            xytext=(99 - dx, y[-1] + dy_end),
            textcoords="data",
            fontsize=11,
            color=color,
            ha="right",
            va="bottom",
            bbox=bbox,
            arrowprops=arrow,
            zorder=8,
        )

    def _delta_badge(ax, pct: float) -> None:
        ax.text(
            0.97,
            0.08,
            f"t=0→99  +{pct:.1f}%",
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=12,
            color="#e6edf3",
            fontweight="bold",
            bbox=dict(boxstyle="round,pad=0.35", fc=(15 / 255, 20 / 255, 36 / 255, 0.9), ec="#3a4558", lw=1),
        )

    # Primary trends — zoomed Y so evolution is visible
    ax_span, ax_std, ax_tail, ax_skew = axes
    for ax in axes:
        ax.set_facecolor(PANEL_BG)

    ax_span.fill_between(ts, span, alpha=0.15, color=THEME["purple"])
    ax_span.plot(ts, span, color=THEME["purple"], lw=LINE_WIDTH)
    _tight_ylim(ax_span, span)
    _mark_key_steps(ax_span, span, THEME["purple"], fmt="{:.3f}")
    _delta_badge(ax_span, span_pct)
    ax_span.set_title("分位跨度 p99−p01（团块化）", fontsize=14, color="#e6edf3", pad=10)
    ax_span.set_ylabel("log10 密度跨度", fontsize=12, color=THEME["muted"], labelpad=8)
    style_axes(ax_span, labelsize=12)
    set_tick_density(ax_span, factor=2.5, axes="y")

    ax_std.fill_between(ts, std, alpha=0.15, color=THEME["cyan"])
    ax_std.plot(ts, std, color=THEME["cyan"], lw=LINE_WIDTH)
    _tight_ylim(ax_std, std)
    _mark_key_steps(ax_std, std, THEME["cyan"], fmt="{:.4f}")
    _delta_badge(ax_std, std_pct)
    ax_std.set_title("标准差 σ(t)", fontsize=14, color="#e6edf3", pad=10)
    ax_std.set_ylabel("σ", fontsize=12, color=THEME["muted"], labelpad=8)
    style_axes(ax_std, labelsize=12)
    set_tick_density(ax_std, factor=2.5, axes="y")

    # Secondary metrics — tight Y + absolute delta (change too small for % badge)
    ax_tail.fill_between(ts, tail, alpha=0.15, color=THEME["gold"])
    ax_tail.plot(ts, tail, color=THEME["gold"], lw=LINE_WIDTH)
    _tight_ylim(ax_tail, tail, pad_frac=0.35)
    _mark_key_steps(ax_tail, tail, THEME["gold"], fmt="{:.3f}%")
    ax_tail.set_title("高密度尾体积占比 ≥p99", fontsize=14, color="#e6edf3", pad=10)
    ax_tail.set_xlabel("时间步 t", fontsize=13, color=THEME["muted"], labelpad=8)
    ax_tail.set_ylabel("体积占比 (%)", fontsize=12, color=THEME["muted"], labelpad=8)
    ax_tail.text(
        0.97,
        0.08,
        f"≈{tail[-1]:.2f}% 维持",
        transform=ax_tail.transAxes,
        ha="right",
        va="bottom",
        fontsize=11,
        color=THEME["gold"],
        bbox=dict(boxstyle="round,pad=0.35", fc=(15 / 255, 20 / 255, 36 / 255, 0.9), ec="#3a4558", lw=1),
    )
    style_axes(ax_tail, labelsize=12)
    set_tick_density(ax_tail, factor=2.5, axes="y")

    ax_skew.fill_between(ts, skew, alpha=0.15, color=THEME["coral"])
    ax_skew.plot(ts, skew, color=THEME["coral"], lw=LINE_WIDTH)
    _tight_ylim(ax_skew, skew, pad_frac=0.35)
    _mark_key_steps(ax_skew, skew, THEME["coral"], fmt="{:.4f}")
    ax_skew.set_title("偏度 skew(t)", fontsize=14, color="#e6edf3", pad=10)
    ax_skew.set_xlabel("时间步 t", fontsize=13, color=THEME["muted"], labelpad=8)
    ax_skew.set_ylabel("偏度", fontsize=12, color=THEME["muted"], labelpad=8)
    d_skew = skew[-1] - skew[0]
    ax_skew.text(
        0.97,
        0.08,
        f"Δ={d_skew:+.4f}",
        transform=ax_skew.transAxes,
        ha="right",
        va="bottom",
        fontsize=11,
        color=THEME["coral"],
        bbox=dict(boxstyle="round,pad=0.35", fc=(15 / 255, 20 / 255, 36 / 255, 0.9), ec="#3a4558", lw=1),
    )
    style_axes(ax_skew, labelsize=12)
    set_tick_density(ax_skew, factor=2.5, axes="y")

    fig.suptitle(
        "任务二：100 步全域统计揭示的演化规律",
        fontsize=17,
        color="#e6edf3",
        fontweight="bold",
        y=0.98,
    )
    fig.text(
        0.5,
        0.935,
        "引力团块化：σ 与 p99−p01 同步上升；≥p99 尾体积约 1% 维持，偏度右偏稳定",
        ha="center",
        va="top",
        fontsize=12,
        color=THEME["muted"],
    )
    fig.subplots_adjust(top=0.86, bottom=0.10, left=0.08, right=0.97)
    save_figure(fig, OUT / "task2_evolution_story.png", pad=0.12, skip_tight=True)
    print(f"Evolution story: {OUT / 'task2_evolution_story.png'}")


def _log_hist_for_bins(flat: np.ndarray, bin_count: int, vmin: float, vmax: float) -> tuple[np.ndarray, np.ndarray]:
    edges = np.logspace(np.log10(vmin), np.log10(vmax), bin_count + 1)
    counts, _ = np.histogram(flat, bins=edges)
    centers = np.sqrt(edges[:-1] * edges[1:])
    pct = counts / max(counts.sum(), 1) * 100.0
    return centers, pct


# 任务三 void 合成标题 — 单题双图，主标题小于 task4 四联（88px）
_TASK3_VOID_COMPOSE = dict(
    main_title=36,
    sheet_sub=22,
    panel_label=36,
    panel_corner=32,
    panel_sub=24,
    title_subtitle_gap=16,
    title_pad_y=24,
    title_pad_x=36,
)

# 任务三 void 图内 matplotlib 字号（图例 / 刻度加大，避免拥挤）
_TASK3_VOID_CHART = dict(
    axis=15,
    tick=16,
    legend=14,
    badge=12,
)


def _mpl_figure_to_pil(fig, w: int | None = None, h: int | None = None) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=120,
        facecolor=VIZ_BG,
        edgecolor="none",
        bbox_inches="tight",
        pad_inches=0.08,
    )
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    if w is not None and h is not None:
        return img.resize((w, h), Image.Resampling.LANCZOS)
    return img


def _task3_void_legend(ax) -> None:
    ax.legend(
        fontsize=_TASK3_VOID_CHART["legend"],
        loc="upper left",
        handlelength=2.4,
        handletextpad=0.7,
        borderpad=0.55,
        labelspacing=0.45,
        framealpha=0.92,
        facecolor=(12 / 255, 16 / 255, 28 / 255, 0.92),
        edgecolor="#3a4558",
    )


def _render_task3_void_expansion(
    ts: list[int],
    void_t0p10: list[float],
    void_t0p01: list[float],
) -> Image.Image:
    typo = _TASK3_VOID_CHART
    fig, ax = plt.subplots(figsize=(11.2, 3.65), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)
    ax.plot(ts, void_t0p10, color=THEME["cyan"], lw=LINE_WIDTH, label="ρ ≤ ρ_p10(t=0)")
    ax.plot(ts, void_t0p01, color=THEME["blue"], lw=LINE_WIDTH, label="ρ ≤ ρ_p01(t=0)")
    ax.fill_between(ts, void_t0p10, alpha=0.12, color=THEME["cyan"])
    ax.set_xlabel("时间步", fontsize=typo["axis"], color=THEME["muted"], labelpad=10)
    ax.set_ylabel("体积分数 %", fontsize=typo["axis"], color=THEME["muted"], labelpad=12)
    ax.text(
        0.97,
        0.08,
        f"t=0→99  {void_t0p10[0]:.2f}%→{void_t0p10[-1]:.2f}%",
        transform=ax.transAxes,
        ha="right",
        va="bottom",
        fontsize=typo["badge"],
        color="#e6edf3",
        fontweight="bold",
        bbox=dict(boxstyle="round,pad=0.35", fc=(15 / 255, 20 / 255, 36 / 255, 0.9), ec="#3a4558", lw=1),
    )
    _task3_void_legend(ax)
    style_axes(ax, labelsize=typo["tick"])
    ax.tick_params(axis="both", which="major", pad=6)
    set_tick_density(ax, factor=2.0, axes="xy")
    return _mpl_figure_to_pil(fig)


def _render_task3_void_deepening(
    ts: list[int],
    p01_curve: list[float],
    p10_curve: list[float],
) -> Image.Image:
    typo = _TASK3_VOID_CHART
    fig, ax = plt.subplots(figsize=(11.2, 3.65), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)
    ax.plot(ts, p01_curve, color=THEME["cyan"], lw=LINE_WIDTH, label="p01(t)")
    ax.plot(ts, p10_curve, color=THEME["purple"], lw=LINE_WIDTH, label="p10(t)")
    ax.set_xlabel("时间步", fontsize=typo["axis"], color=THEME["muted"], labelpad=10)
    ax.set_ylabel("密度 ρ（线性刻度）", fontsize=typo["axis"], color=THEME["muted"], labelpad=12)
    _task3_void_legend(ax)
    style_axes(ax, labelsize=typo["tick"])
    ax.tick_params(axis="both", which="major", pad=6)
    set_tick_density(ax, factor=2.0, axes="xy")
    return _mpl_figure_to_pil(fig)


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


def task3_log_hist_bars(timeline: dict) -> None:
    """128-bin log 直方图（柱状）t=0 vs t=99，供信息图/答辩一眼可认。"""
    edges = np.array(timeline["logBinEdges"], dtype=float)
    centers = np.array([np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)])
    widths = _log_hist_bin_widths(edges)
    steps = timeline["timesteps"]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5.4), facecolor=VIZ_BG)
    bar_colors = {0: THEME["purple"], 99: THEME["coral"]}
    for ax, t in zip(axes, [0, 99]):
        ax.set_facecolor(PANEL_BG)
        pct = np.array(timeline["histograms"][t], dtype=float) * 100.0
        s = steps[t]
        ax.bar(
            centers,
            pct,
            width=widths,
            align="center",
            color=bar_colors[t],
            alpha=0.88,
            edgecolor=(1, 1, 1, 0.22),
            linewidth=0.35,
            zorder=2,
        )
        ax.set_xscale("log")
        x_lo = float(s["p01"]) * 0.992
        x_hi = float(s["p99"]) * 1.012
        ax.set_xlim(x_lo, x_hi)
        y_top = max(5.5, float(np.ceil((pct.max() + 0.6) * 10) / 10))
        ax.set_ylim(0, y_top)
        ax.set_title(f"t={t} · 128 bins", fontsize=13, color="#e6edf3", fontweight="bold", pad=10)
        ax.set_xlabel("密度 ρ（log10 轴）", fontsize=12, color=THEME["muted"], labelpad=8)
        if t == 0:
            ax.set_ylabel("体素占比 %", fontsize=12, color=THEME["muted"], labelpad=10)
        ticks, labels = _task4_hist_x_ticks(x_lo, x_hi)
        ax.xaxis.set_major_locator(FixedLocator(ticks))
        ax.xaxis.set_major_formatter(FixedFormatter(labels))
        ax.tick_params(axis="x", which="minor", bottom=False)
        style_axes(ax, labelsize=11)
        pk = int(np.argmax(pct))
        ax.annotate(
            f"峰 {centers[pk]:.2f}\n{pct[pk]:.2f}%",
            xy=(centers[pk], pct[pk]),
            xytext=(12, 14),
            textcoords="offset points",
            fontsize=10,
            color=bar_colors[t],
            ha="left",
            va="bottom",
            bbox=dict(boxstyle="round,pad=0.3", fc=(12 / 255, 16 / 255, 28 / 255, 0.92), ec=bar_colors[t], lw=0.8),
        )

    fig.suptitle(
        "任务三：密度对数直方图（128 bins · 全域统一边界）",
        fontsize=16,
        color="#f8fbff",
        fontweight="bold",
        y=0.98,
    )
    fig.text(
        0.5,
        0.91,
        "早期峰更高更窄 → 末期展宽 · 团块化与两极分化",
        ha="center",
        va="top",
        fontsize=12,
        color=THEME["muted"],
    )
    fig.subplots_adjust(top=0.82, bottom=0.14, left=0.07, right=0.98, wspace=0.22)
    save_figure(fig, OUT / "task3_log_hist_bars.png", pad=0.08, skip_tight=True)
    print(f"Log hist bars: {OUT / 'task3_log_hist_bars.png'}")


def task3_void_evolution(timeline: dict) -> None:
    """PIL 合成：双图竖排，子图保持自然比例不拉伸；主标题小于四联合成。"""
    steps = timeline["timesteps"]
    ts = [s["timestep"] for s in steps]
    if "voidFractionBelowT0P10" not in steps[0]:
        print("Skip task3_void_evolution: rerun precompute", file=sys.stderr)
        return

    void_t0p10 = [s["voidFractionBelowT0P10"] * 100 for s in steps]
    void_t0p01 = [s["voidFractionBelowT0P01"] * 100 for s in steps]
    p01_curve = [s["p01"] for s in steps]
    p10_curve = [s.get("p10", s["p01"]) for s in steps]

    ctypo = _TASK3_VOID_COMPOSE
    _fs = dict(
        header="inline",
        label_font_size=ctypo["panel_label"],
        corner_font_size=ctypo["panel_corner"],
        subtitle_font_size=ctypo["panel_sub"],
    )

    expansion_img = _render_task3_void_expansion(ts, void_t0p10, void_t0p01)
    deepening_img = _render_task3_void_deepening(ts, p01_curve, p10_curve)
    col_panels = [
        wrap_panel(
            expansion_img,
            corner_letter="(a)",
            label="void 扩张",
            subtitle="固定 t=0 低密度阈值的体素占比",
            **_fs,
        ),
        wrap_panel(
            deepening_img,
            corner_letter="(b)",
            label="void 深化",
            subtitle="低密度分位阈值 p01/p10 随时间下移",
            **_fs,
        ),
    ]
    panel_w = max(p.width for p in col_panels)
    col = stitch_panels_png(
        [fit_panel_width(p, panel_w) for p in col_panels],
        direction="vertical",
        gap=14,
        max_width=3200,
    )
    final = compose_sheet(
        "任务三：低密度尾（void）定量追踪",
        "固定 t=0 分位阈值 · 100 步 void 扩张与低密度尾下移",
        [col],
        max_width=min(col.width, 3200),
        title_font_size=ctypo["main_title"],
        subtitle_font_size=ctypo["sheet_sub"],
        title_pad_y=ctypo["title_pad_y"],
        title_pad_x=ctypo["title_pad_x"],
        title_subtitle_gap=ctypo["title_subtitle_gap"],
        title_align="center",
    )
    save_pil_png(final, OUT / "task3_void_evolution.png")
    print(f"Composite task3_void_evolution.png: {final.width}×{final.height}px")


def task3_figures(timeline: dict) -> None:
    edges = timeline["logBinEdges"]
    centers = [np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)]
    steps = timeline["timesteps"]
    colors = [THEME["purple"], THEME["blue"], THEME["cyan"], THEME["gold"], THEME["coral"]]

    task3_bin_sensitivity(timeline)
    task3_log_hist_bars(timeline)
    task3_void_evolution(timeline)

    p50_0 = steps[0]["p50"]
    p50_99 = steps[99]["p50"]
    pk0 = int(np.argmax(timeline["histograms"][0]))
    pk99 = int(np.argmax(timeline["histograms"][99]))
    y0 = [h * 100 for h in timeline["histograms"][0]]
    y99 = [h * 100 for h in timeline["histograms"][99]]
    rho0 = centers[pk0]
    rho99 = centers[pk99]
    mass0 = y0[pk0]
    mass99 = y99[pk99]
    x_lo = min(steps[t]["p01"] for t in REP_STEPS) * 0.992
    x_hi = max(steps[t]["p99"] for t in REP_STEPS) * 1.008
    ymax = max(max(y0), max(y99))

    _callout_bbox = dict(
        boxstyle="round,pad=0.32",
        fc=(12 / 255, 16 / 255, 28 / 255, 0.94),
        lw=0.8,
    )

    fig = plt.figure(figsize=(11.2, 6.2), facecolor=VIZ_BG)
    ax = fig.add_subplot(111)
    ax.set_facecolor(PANEL_BG)

    ax.fill_between(centers, y99, y0, alpha=0.07, color="#6a7fa8", interpolate=True, zorder=0)

    for t, c in zip(REP_STEPS, colors):
        hist = timeline["histograms"][t]
        y = [h * 100 for h in hist]
        if t in (0, 99):
            ax.plot(centers, y, color=c, lw=5.5, alpha=0.12, zorder=2, solid_capstyle="round")
        lw = 3.0 if t in (0, 99) else 1.5
        alpha = 1.0 if t in (0, 99) else 0.55
        z = 5 if t in (0, 99) else 3
        ax.plot(centers, y, label=f"t={t}", color=c, lw=lw, alpha=alpha, zorder=z, solid_capstyle="round")

    ax.set_xscale("log")
    ax.set_xlim(x_lo, x_hi)
    y_top = max(5.5, np.ceil((ymax + 0.9) * 10) / 10)
    ax.set_ylim(0, y_top)

    ax.plot(rho0, mass0, "o", color=THEME["purple"], ms=9, mew=0.9, mec="#e6edf3", zorder=8)
    ax.plot(rho99, mass99, "o", color=THEME["coral"], ms=9, mew=0.9, mec="#e6edf3", zorder=8)

    ax.annotate(
        f"t=99 主峰\nρ={rho99:.2f}",
        xy=(rho99, mass99),
        xycoords="data",
        xytext=(0, 12),
        textcoords="offset points",
        fontsize=11,
        color=THEME["coral"],
        ha="center",
        va="bottom",
        bbox={**_callout_bbox, "ec": THEME["coral"]},
        arrowprops=dict(arrowstyle="-", color=THEME["coral"], lw=0.9, shrinkA=0, shrinkB=3),
        zorder=9,
    )
    ax.annotate(
        f"t=0 主峰\nρ={rho0:.2f}",
        xy=(rho0, mass0),
        xycoords="data",
        xytext=(0, 26),
        textcoords="offset points",
        fontsize=11,
        color=THEME["purple"],
        ha="center",
        va="bottom",
        bbox={**_callout_bbox, "ec": THEME["purple"]},
        arrowprops=dict(arrowstyle="-", color=THEME["purple"], lw=0.9, shrinkA=0, shrinkB=3),
        zorder=9,
    )

    ax.set_ylabel("概率质量 ×100", fontsize=14, color=THEME["muted"], labelpad=10)
    ax.set_xlabel("密度 ρ（log10 轴）", fontsize=14, color=THEME["muted"], labelpad=8)

    style_axes(ax, labelsize=13)
    ax.yaxis.set_major_locator(MultipleLocator(1.0))
    _x_ticks = [8.5, 9.0, 9.5, 10.0, 10.5, 11.0]
    _x_ticks = [v for v in _x_ticks if x_lo <= v <= x_hi]
    ax.xaxis.set_major_locator(FixedLocator(_x_ticks))
    ax.xaxis.set_major_formatter(FixedFormatter([f"{v:.1f}" for v in _x_ticks]))
    ax.tick_params(axis="x", which="minor", bottom=False)

    ax.legend(
        loc="upper left",
        fontsize=11,
        framealpha=0.90,
        facecolor=(12 / 255, 16 / 255, 28 / 255, 0.92),
        edgecolor="#3a4558",
        handlelength=2.2,
        labelspacing=0.50,
    )

    fig.suptitle(
        "对数等距分箱直方图叠加（128 bins，代表步）",
        fontsize=18,
        color="#e6edf3",
        fontweight="bold",
        y=0.98,
    )
    fig.text(
        0.5,
        0.905,
        f"100 步演化 · 主峰 ρ {rho0:.2f}→{rho99:.2f} · p50 {p50_0:.2f}→{p50_99:.2f} · 峰高 {mass0:.2f}%→{mass99:.2f}%",
        ha="center",
        va="top",
        fontsize=13,
        color=THEME["muted"],
    )
    fig.subplots_adjust(top=0.80, bottom=0.14, left=0.11, right=0.97)
    save_figure(fig, OUT / "task3_hist_overlay.png", pad=0.10, skip_tight=True)
    print(f"Hist overlay: {OUT / 'task3_hist_overlay.png'}")

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


def _log_hist_bin_widths(edges: np.ndarray, *, gap: float = 0.92) -> np.ndarray:
    """Log 轴直方图柱宽：按 bin 边距，避免 centers×0.08 在 log 尺度下重叠 ~30 倍抹平峰顶。"""
    return np.diff(edges) * gap


def _task4_hist_xlim(centers: np.ndarray, pct: np.ndarray, lo: float, hi: float) -> tuple[float, float]:
    """聚焦刷选区间与主峰，裁掉远端空尾。"""
    pk = int(np.argmax(pct))
    x_lo = min(float(centers[max(0, pk - 6)]), lo) * 0.996
    x_hi = max(float(centers[min(len(centers) - 1, pk + 6)]), hi) * 1.010
    x_lo = max(x_lo, float(centers[0]) * 0.998)
    x_hi = min(x_hi, float(centers[-1]) * 1.004)
    return x_lo, x_hi


def _fmt_task4_hist_tick(v: float) -> str:
    if abs(v - round(v)) < 1e-6:
        return f"{int(round(v))}" if v >= 10 else f"{v:.1f}"
    return f"{v:.1f}"


def _task4_hist_x_ticks(x_lo: float, x_hi: float) -> tuple[list[float], list[str]]:
    candidates = [8.0, 8.5, 9.0, 9.5, 10.0, 10.5, 11.0, 11.5, 12.0, 12.5, 13.0, 14.0, 15.0]
    ticks = [v for v in candidates if x_lo * 0.999 <= v <= x_hi * 1.001]
    if len(ticks) > 7:
        ticks = [ticks[0], *ticks[1:-1:2], ticks[-1]]
    if len(ticks) < 3:
        ticks = list(np.geomspace(x_lo, x_hi, 4))
    labels = [_fmt_task4_hist_tick(v) for v in ticks]
    return ticks, labels


def _task4_discovery_hist_xlim(
    s: dict,
    centers: np.ndarray,
    pct: np.ndarray,
    *,
    brush_hi: float | None = None,
) -> tuple[float, float]:
    """统一 discovery 直方图 X 范围；Top1 不拉到 ρ_max，避免右侧空轴。"""
    x_lo = float(s["p01"]) * 0.992
    pk_max = float(np.max(pct))
    vis = centers[(pct >= pk_max * 0.012) | ((centers >= s["p99"]) & (pct >= 0.05))]
    natural_hi = float(vis[-1]) * 1.035 if len(vis) else float(s["p99"]) * 1.12
    if brush_hi is not None:
        natural_hi = max(natural_hi, float(brush_hi) * 1.03)
    x_hi = max(natural_hi, float(s["p99"]) * 1.06)
    if brush_hi is None or float(brush_hi) <= float(s["p99"]) * 1.35:
        x_hi = min(x_hi, float(s["p99"]) * 1.18)
    return x_lo, x_hi


def _task4_hist_pct_ylim(
    ax,
    pct: np.ndarray,
    centers: np.ndarray | None = None,
    x_lo: float | None = None,
    x_hi: float | None = None,
    *,
    tail_mode: bool = False,
) -> None:
    """Y 轴留足 headroom；tail_mode 时按可见右尾自适应（用于 (d) zoom）。"""
    if centers is not None and x_lo is not None and x_hi is not None:
        vis = (centers >= x_lo) & (centers <= x_hi)
        ymax = float(np.max(pct[vis])) if vis.any() else float(np.max(pct))
    else:
        ymax = float(np.max(pct))
    if tail_mode:
        y_top = max(0.14, float(np.ceil((ymax + 0.022) * 100) / 100))
        step = 0.04 if y_top <= 0.22 else 0.10
    else:
        y_top = max(5.5, float(np.ceil((ymax + 0.75) * 10) / 10))
        step = 0.5 if y_top <= 6.5 else 1.0
    ax.set_ylim(0, y_top)
    ax.yaxis.set_major_locator(MultipleLocator(step))


def _style_task4_hist_axis(ax, x_lo: float, x_hi: float, *, labelsize: int = 14) -> None:
    ticks, labels = _task4_hist_x_ticks(x_lo, x_hi)
    ax.set_xscale("log")
    ax.set_xlim(x_lo, x_hi)
    style_axes(ax, labelsize=labelsize)
    ax.xaxis.set_major_locator(FixedLocator(ticks))
    ax.xaxis.set_major_formatter(FixedFormatter(labels))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.tick_params(axis="x", which="minor", bottom=False, labelbottom=False)
    ax.tick_params(axis="both", which="major", labelsize=labelsize)
    ax.grid(True, alpha=0.12, which="major")
    ax.grid(True, alpha=0.04, which="minor", axis="y")


_TASK4_CALLOUT = dict(
    boxstyle="round,pad=0.30",
    fc=(12 / 255, 16 / 255, 28 / 255, 0.93),
    lw=0.75,
)

# 合成图（compose_sheet / wrap_panel）统一字号层级 — 与 task4_discovery_summary 一致
_COMPOSE_TYPO = dict(
    main_title=88,
    sheet_sub=38,
    panel_label=52,
    panel_corner=48,
    panel_sub=38,
    title_subtitle_gap=36,
    title_pad_y=44,
    title_pad_x=44,
)

# 图表内同类型字号（合成后视觉一致需按显示缩放补偿）
_TASK4_CHART_TYPO = dict(
    legend=10,
    axis=15,
    tick=14,
    annotate=11,
    caption=10,
)
_TASK4_A_COMPOSE_H = 640
_TASK4_D_COMPOSE_H = 1200
_TASK4_IMG_COMPOSE_H = 640

# 刷选验证汇总（图12）专用：matplotlib 子图 + PIL 合成
# 标题只在合成层出现两级：总标题 + (a)/(b) 分区标题与一行说明；子图内不再 set_title
_TASK4_VALIDATION_TYPO = dict(
    axis=11,
    tick=11,
    legend=10,
    annotate=10,
    table=10,
    table_muted=9,
)
_TASK4_VALIDATION_COMPOSE = dict(
    main_title=64,
    panel_label=52,
    panel_corner=44,
    panel_sub=40,
    content_w=3200,
    stack_gap=10,
    title_pad_y=40,
    title_pad_x=40,
    panel_header_content_gap=18,
    panel_subtitle_gap=10,
    panel_subtitle_tail_pad=22,
)

# 图13 刷选扩展验证 2×2 专用（子图按合成区原生导出，避免放大糊字）
_TASK4_PERF_FIG_CHART = (6.2, 3.15)
_TASK4_PERF_FIG_PROJ = (6.2, 2.85)
_TASK4_PERFORMANCE_TYPO = dict(
    axis=13,
    tick=12,
    legend=11,
    annotate=12,
    subplot=13,
)
_TASK4_PERFORMANCE_COMPOSE = dict(
    main_title=60,
    sheet_sub=32,
    panel_label=44,
    panel_corner=36,
    panel_sub=28,
    content_h=680,
    col_w=1580,
    grid_gap=14,
    row_gap=24,
    title_pad_y=32,
    title_pad_x=34,
    title_subtitle_gap=20,
)


def _style_performance_chart(ax, *, tick: int | None = None, twin=None) -> None:
    fs = tick or _TASK4_PERFORMANCE_TYPO["tick"]
    style_axes(ax, labelsize=fs)
    ax.xaxis.label.set_size(_TASK4_PERFORMANCE_TYPO["axis"])
    ax.yaxis.label.set_size(_TASK4_PERFORMANCE_TYPO["axis"])
    if twin is not None:
        twin.tick_params(colors=THEME["muted"], labelsize=fs)
        twin.yaxis.label.set_size(_TASK4_PERFORMANCE_TYPO["axis"])


def _style_validation_chart(ax, *, tick: int | None = None) -> None:
    fs = tick or _TASK4_VALIDATION_TYPO["tick"]
    style_axes(ax, labelsize=fs)
    if ax.get_title():
        ax.title.set_fontsize(_TASK4_VALIDATION_TYPO["axis"] + 1)
    ax.xaxis.label.set_size(_TASK4_VALIDATION_TYPO["axis"])
    ax.yaxis.label.set_size(_TASK4_VALIDATION_TYPO["axis"])


def _validation_section_caption(ax, text: str, *, y: float = 0.5) -> None:
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.text(
        0.0,
        y,
        text,
        fontsize=_TASK4_VALIDATION_TYPO["table"],
        color=THEME["muted"],
        va="center",
        ha="left",
    )


def _smart_bar_label_y(val: float, ymax: float, *, floor_frac: float = 0.12) -> float:
    if val < ymax * 0.14:
        return ymax * floor_frac
    return val + ymax * 0.035


def _task4_chart_fs(kind: str, source_h: int, display_h: int) -> int:
    """按合成缩放补偿，使同类型文字在最终图里视觉大小一致。"""
    target = _TASK4_CHART_TYPO[kind]
    raw = round(target * source_h / max(display_h, 1))
    caps = {
        "legend": (10, 12),
        "annotate": (12, 15),
        "caption": (17, 20),
        "axis": (14, 16),
        "tick": (12, 15),
    }
    lo, hi = caps.get(kind, (10, 20))
    return max(lo, min(hi, raw))


def _task4_legend_fs(source_h: int, display_h: int) -> int:
    return _task4_chart_fs("legend", source_h, display_h)


def _log_hist_pct(values: np.ndarray, edges: list | np.ndarray) -> np.ndarray:
    """Bin scalar samples into log-spaced edges; return percentage per bin."""
    counts, _ = np.histogram(values, bins=edges)
    total = counts.sum() or 1
    return counts / total * 100


def _task4_reverse_lookup_xlim(
    s: dict,
    lo: float,
    hi: float,
    centers: np.ndarray,
    pct: np.ndarray,
) -> tuple[float, float]:
    """(d) 全场坐标右尾 zoom：从 Top 1% 起点到反查带右端，与 (a) 全宽视图区分。"""
    p99 = float(s["p99"])
    tail_bins = centers[(centers >= p99 * 0.94) & (pct >= 0.008)]
    x_lo = float(tail_bins[0]) * 0.992 if len(tail_bins) else p99 * 0.972
    x_hi = max(float(hi), p99) * 1.085
    tail = (centers >= x_lo) & (pct >= 0.003)
    if tail.any():
        x_hi = max(x_hi, float(centers[np.where(tail)[0][-1]]) * 1.035)
    return x_lo, min(x_hi, float(centers[-1]) * 1.004)


def _draw_task4_pct_hist(
    ax,
    centers: np.ndarray,
    pct: np.ndarray,
    *,
    brush_lo: float,
    brush_hi: float,
    brush_color: str,
    brush_label: str,
    threshold_line: float | None = None,
    x_lo: float | None = None,
    x_hi: float | None = None,
    base_color: str = THEME["purple"],
    base_label: str | None = None,
    show_peak: bool = True,
    peak_annotate: bool = True,
    peak_annotate_xytext: tuple[int, int] | None = None,
    peak_annotate_ha: str = "right",
    peak_annotate_va: str = "bottom",
    legend_loc: str = "upper right",
    legend_anchor: tuple[float, float] = (0.99, 0.98),
    context_lo: float | None = None,
    context_hi: float | None = None,
    context_color: str | None = None,
    context_label: str | None = None,
    tail_mode: bool = False,
    legend_fontsize: int | None = None,
    annotate_fontsize: int | None = None,
) -> None:
    """真实 bin 占比曲线：渐变填充 + 刷选高亮 + 可选峰顶标注。"""
    if x_lo is None or x_hi is None:
        x_lo, x_hi = _task4_hist_xlim(centers, pct, brush_lo, brush_hi)

    vis = (centers >= x_lo) & (centers <= x_hi)
    vis_pct = np.where(vis, pct, 0.0)
    pk = int(np.argmax(vis_pct)) if vis.any() else int(np.argmax(pct))
    brush_mask = (centers >= brush_lo) & (centers <= brush_hi * 1.001)

    if context_lo is not None and context_hi is not None and context_color:
        ax.axvspan(
            context_lo,
            min(context_hi, x_hi),
            color=context_color,
            alpha=0.07,
            zorder=0,
            label=context_label or "_ctx",
        )
    ax.axvspan(brush_lo, min(brush_hi, x_hi), color=brush_color, alpha=0.04, zorder=0)
    ax.fill_between(centers, 0, pct, color=base_color, alpha=0.14, interpolate=True, zorder=1)
    ax.plot(centers, pct, color=base_color, lw=5.5, alpha=0.10, solid_capstyle="round", zorder=2)
    ax.plot(centers, pct, color=base_color, lw=2.6, alpha=0.98, solid_capstyle="round", zorder=3, label=base_label or "_base")

    if np.any(brush_mask):
        ax.fill_between(
            centers[brush_mask],
            0,
            pct[brush_mask],
            color=brush_color,
            alpha=0.36,
            interpolate=True,
            zorder=4,
        )
        ax.plot(
            centers[brush_mask],
            pct[brush_mask],
            color=brush_color,
            lw=2.8,
            alpha=1.0,
            solid_capstyle="round",
            zorder=5,
            label=brush_label,
        )

    if threshold_line is not None:
        ax.axvline(
            threshold_line,
            color=brush_color,
            ls=(0, (5, 4)),
            lw=1.0,
            alpha=0.68,
            zorder=6,
        )

    if show_peak and vis_pct[pk] > 0:
        ax.plot(
            centers[pk],
            pct[pk],
            "o",
            color=base_color,
            ms=6.0,
            mew=0.85,
            mec="#e6edf3",
            zorder=7,
        )
        if peak_annotate:
            ann_fs = annotate_fontsize if annotate_fontsize is not None else _TASK4_CHART_TYPO["annotate"]
            xy_off = peak_annotate_xytext if peak_annotate_xytext is not None else (-52, 18)
            ax.annotate(
                f"{'右尾峰' if tail_mode else '主峰'} ρ={centers[pk]:.2f} · {pct[pk]:.2f}%",
                xy=(centers[pk], pct[pk]),
                xycoords="data",
                xytext=xy_off,
                textcoords="offset points",
                fontsize=ann_fs,
                color=base_color,
                ha=peak_annotate_ha,
                va=peak_annotate_va,
                bbox={**_TASK4_CALLOUT, "ec": base_color, "pad": 0.28},
                arrowprops=dict(arrowstyle="-", color=base_color, lw=0.75, shrinkA=0, shrinkB=3),
                zorder=8,
            )

    leg_fs = legend_fontsize if legend_fontsize is not None else _TASK4_CHART_TYPO["legend"]
    _style_task4_hist_axis(ax, x_lo, x_hi, labelsize=_TASK4_CHART_TYPO["tick"])
    _task4_hist_pct_ylim(ax, pct, centers, x_lo, x_hi, tail_mode=tail_mode)
    if brush_label and brush_label != "_base":
        handles, labels = ax.get_legend_handles_labels()
        handles = [h for h, lab in zip(handles, labels) if lab and not lab.startswith("_")]
        labels = [lab for lab in labels if lab and not lab.startswith("_")]
        if handles:
            ax.legend(
                handles,
                labels,
                fontsize=leg_fs,
                loc=legend_loc,
                bbox_to_anchor=legend_anchor,
                framealpha=0.88,
                facecolor=(12 / 255, 16 / 255, 28 / 255, 0.92),
                edgecolor="#3a4558",
                handlelength=2.0,
                borderpad=0.42,
                labelspacing=0.35,
            )


def task4_histogram_brush(timeline: dict, t: int = 99) -> None:
    edges = timeline["logBinEdges"]
    centers = np.array([np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)])
    hist = np.array(timeline["histograms"][t])
    s = timeline["timesteps"][t]
    total = hist.sum() or 1
    pct = hist / total * 100

    def one_brush(lo: float, hi: float, hi_color: str, label: str, fname: str, *, threshold: float | None = None) -> None:
        fig, ax = plt.subplots(figsize=(9.4, 3.35), facecolor=VIZ_BG)
        ax.set_facecolor(PANEL_BG)
        if threshold == s["p99"]:
            x_lo, x_hi = _task4_discovery_hist_xlim(s, centers, pct)
        elif threshold == s["p01"]:
            x_lo = float(s["min"]) * 0.988
            x_hi = float(s["p50"]) * 1.015
        else:
            x_lo, x_hi = _task4_hist_xlim(centers, pct, lo, hi)
        _draw_task4_pct_hist(
            ax,
            centers,
            pct,
            brush_lo=lo,
            brush_hi=hi,
            brush_color=hi_color,
            brush_label=label,
            threshold_line=threshold,
            x_lo=x_lo,
            x_hi=x_hi,
            base_label="全场 128³ 体素",
            peak_annotate=True,
            legend_loc="upper right",
            legend_anchor=(0.99, 0.98),
            legend_fontsize=_task4_legend_fs(997, _TASK4_A_COMPOSE_H),
            annotate_fontsize=_task4_chart_fs("annotate", 997, _TASK4_A_COMPOSE_H),
        )
        ax.set_xlabel("密度 ρ (log)", fontsize=_TASK4_CHART_TYPO["axis"], color=THEME["muted"], labelpad=8)
        ax.set_ylabel("全场体素占比 %", fontsize=_TASK4_CHART_TYPO["axis"], color=THEME["muted"], labelpad=8)
        fig.subplots_adjust(top=0.90, bottom=0.18, left=0.12, right=0.98)
        save_figure(fig, OUT / fname, pad=0.10, skip_tight=True)

    one_brush(s["p99"], s["max"], THEME["gold"], f"Top 1%: ρ≥{s['p99']:.2f}", "task4_hist_brush_top1.png", threshold=s["p99"])
    one_brush(s["min"], s["p01"], THEME["cyan"], f"Bottom 1%: ρ≤{s['p01']:.2f}", "task4_hist_brush_bottom1.png", threshold=s["p01"])


def _task4_img_caption(fig, text: str, *, x: float, ha: str, color: str, fontsize: int = 15) -> None:
    fig.text(
        x,
        0.96,
        text,
        ha=ha,
        va="top",
        fontsize=fontsize,
        color=color,
        fontweight="bold",
        transform=fig.transFigure,
        bbox=dict(
            boxstyle="round,pad=0.32",
            fc=(12 / 255, 16 / 255, 28 / 255, 0.88),
            ec=(120 / 255, 220 / 255, 255 / 255, 0.35),
            lw=0.8,
        ),
    )


def task4_discovery_context_panel(vol: np.ndarray, timeline: dict, t: int = 99) -> None:
    """(b) 全场 XY 投影 — 与 (c) 同色系，无刷选高亮。"""
    rgb = render_xy_projection(vol, timeline)
    fig, ax = plt.subplots(figsize=(5.6, 5.6), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)
    ax.imshow(rgb, origin="lower", interpolation="bilinear")
    ax.axis("off")
    cap_fs = _task4_chart_fs("caption", 1476, _TASK4_IMG_COMPOSE_H)
    _task4_img_caption(fig, f"t={t} · XY max proj", x=0.04, ha="left", color=THEME["muted"], fontsize=cap_fs)
    save_figure(fig, OUT / f"task4_discovery_context_t{t:02d}.png", pad=0.08, skip_tight=True)


def task4_discovery_brush_panel(vol: np.ndarray, timeline: dict, t: int = 99) -> None:
    """(c) Top 1% 刷选投影 — cosmic 底图 + 金色高亮。"""
    s = timeline["timesteps"][t]
    rgb = render_xy_projection(vol, timeline, s["p99"], s["max"])
    fig, ax = plt.subplots(figsize=(5.6, 5.6), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)
    ax.imshow(rgb, origin="lower", interpolation="bilinear")
    ax.axis("off")
    cap_fs = _task4_chart_fs("caption", 1476, _TASK4_IMG_COMPOSE_H)
    _task4_img_caption(fig, f"ρ≥{s['p99']:.2f}", x=0.96, ha="right", color=THEME["gold"], fontsize=cap_fs)
    save_figure(fig, OUT / "task4_brush_top1.png", pad=0.08, skip_tight=True)


def task4_brush_bottom_panel(vol: np.ndarray, timeline: dict, t: int = 99) -> None:
    """Bottom 1% 刷选投影 — 与 Top 单图格式一致（供 brush_rows 双行对比）。"""
    s = timeline["timesteps"][t]
    rgb = render_xy_projection(vol, timeline, s["min"], s["p01"])
    fig, ax = plt.subplots(figsize=(5.6, 5.6), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)
    ax.imshow(rgb, origin="lower", interpolation="bilinear")
    ax.axis("off")
    cap_fs = _task4_chart_fs("caption", 1476, _TASK4_IMG_COMPOSE_H)
    _task4_img_caption(fig, f"ρ≤{s['p01']:.2f}", x=0.96, ha="right", color=THEME["cyan"], fontsize=cap_fs)
    save_figure(fig, OUT / "task4_brush_bottom_proj.png", pad=0.08, skip_tight=True)


def task4_spatial_to_stats(vol: np.ndarray, timeline: dict, t: int = 99) -> tuple[float, float]:
    """Spatial → statistical: filament on projection → band on global density axis (tail zoom)."""
    lo, hi, filament_mask = filament_density_band(vol)
    vmin, vmax = global_projection_domain(timeline)
    proj = np.max(vol, axis=2)
    rgb = render_projection_rgb(proj, vmin, vmax)
    gold = np.array([0.96, 0.78, 0.26])
    rgb[filament_mask] = rgb[filament_mask] * 0.25 + gold * 0.75

    edges = timeline["logBinEdges"]
    centers = np.array([np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)])
    hist = np.array(timeline["histograms"][t])
    pct = hist / (hist.sum() or 1) * 100
    n_fil = int(filament_mask.sum())
    s = timeline["timesteps"][t]
    band_mask = (centers >= lo) & (centers <= hi)
    band_vol_pct = float(pct[band_mask].sum())

    fig = plt.figure(figsize=(13.2, 4.5), facecolor=VIZ_BG)
    gs = gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1.05, 1.55], wspace=0.07)
    ax_img = fig.add_subplot(gs[0])
    ax_h = fig.add_subplot(gs[1])
    ax_img.set_facecolor(PANEL_BG)
    ax_h.set_facecolor(PANEL_BG)
    ax_img.imshow(rgb, origin="lower", interpolation="bilinear")
    ax_img.set_title(f"filament 亮脊 · t={t} · 投影 ≥ P88 · n={n_fil}", fontsize=15, color="#e6edf3", pad=8)
    ax_img.axis("off")

    ann_fs = _task4_chart_fs("annotate", 1365, _TASK4_D_COMPOSE_H)
    x_lo, x_hi = _task4_reverse_lookup_xlim(s, lo, hi, centers, pct)
    _draw_task4_pct_hist(
        ax_h,
        centers,
        pct,
        brush_lo=lo,
        brush_hi=hi,
        brush_color=THEME["gold"],
        brush_label=f"反查密度带 ρ∈[{lo:.2f}, {hi:.2f}]",
        x_lo=x_lo,
        x_hi=x_hi,
        base_color=THEME["purple"],
        base_label="全场 128³ 体素（右尾 zoom）",
        show_peak=True,
        peak_annotate=False,
        legend_loc="upper right",
        legend_anchor=(0.99, 0.98),
        context_lo=float(s["p99"]),
        context_hi=x_hi,
        context_color=THEME["cyan"],
        context_label=f"Top 1% 尾段（同 a · ρ≥{s['p99']:.2f}）",
        tail_mode=True,
        legend_fontsize=_task4_legend_fs(1365, _TASK4_D_COMPOSE_H),
        annotate_fontsize=ann_fs,
    )
    ax_h.axvline(float(s["p99"]), color=THEME["cyan"], ls=(0, (4, 3)), lw=1.15, alpha=0.72, zorder=6)
    y_top = ax_h.get_ylim()[1]
    ax_h.text(
        float(s["p99"]),
        y_top * 0.04,
        f"(a) Top 1%\nρ={s['p99']:.2f}",
        fontsize=ann_fs,
        color=THEME["cyan"],
        ha="center",
        va="bottom",
        rotation=0,
        zorder=9,
        bbox={**_TASK4_CALLOUT, "ec": THEME["cyan"], "pad": 0.22},
    )
    vis = (centers >= x_lo) & (centers <= x_hi)
    tail_pk = int(np.argmax(np.where(vis, pct, 0.0)))
    ax_h.annotate(
        f"尾段入口 ρ={centers[tail_pk]:.2f}\n（(a) 主峰 9.23 在左侧）",
        xy=(centers[tail_pk], pct[tail_pk]),
        xycoords="data",
        xytext=(28, -32),
        textcoords="offset points",
        fontsize=ann_fs,
        color=THEME["purple"],
        ha="left",
        va="top",
        bbox={**_TASK4_CALLOUT, "ec": THEME["purple"], "pad": 0.22},
        arrowprops=dict(arrowstyle="-", color=THEME["purple"], lw=0.75, shrinkA=0, shrinkB=3),
        zorder=9,
    )
    band_mid = float(np.sqrt(lo * hi))
    band_y = float(pct[band_mask].max()) if band_mask.any() else y_top * 0.35
    ax_h.annotate(
        f"反查带 · 全场 {band_vol_pct:.2f}%\nρ∈[{lo:.2f}, {hi:.2f}]",
        xy=(band_mid, band_y),
        xycoords="data",
        xytext=(0, 36),
        textcoords="offset points",
        fontsize=ann_fs,
        color=THEME["gold"],
        ha="center",
        va="bottom",
        bbox={**_TASK4_CALLOUT, "ec": THEME["gold"], "pad": 0.22},
        arrowprops=dict(arrowstyle="-", color=THEME["gold"], lw=0.75, shrinkA=0, shrinkB=3),
        zorder=9,
    )
    ax_h.set_xlabel("密度 ρ (log)", fontsize=_TASK4_CHART_TYPO["axis"], color=THEME["muted"], labelpad=8)
    ax_h.set_ylabel("全场体素占比 %", fontsize=_TASK4_CHART_TYPO["axis"], color=THEME["muted"], labelpad=8)
    fig.subplots_adjust(top=0.92, bottom=0.15, left=0.05, right=0.98)
    save_figure(fig, OUT / "task4_spatial_to_stats.png", pad=0.08, skip_tight=True)
    return lo, hi


def task4_threshold_comparison(validation: dict) -> None:
    rows = validation["thresholds"]
    xtick_labels = []
    for r in rows:
        lbl = r["label"]
        if "纤维带" in lbl:
            name = "90–99% 纤维带"
        elif "p95" in lbl:
            name = "p95 (Top 5%)"
        elif "p99.9" in lbl:
            name = "p99.9 (Top 0.1%)"
        elif "p99" in lbl:
            name = "p99 (Top 1%)"
        else:
            name = lbl
        if r.get("rhoMax") is not None:
            rho_txt = f"ρ∈[{r['rhoMin']:.2f}, {r['rhoMax']:.2f}]"
        else:
            rho_txt = f"ρ≥{r['rhoMin']:.2f}"
        xtick_labels.append(f"{name}\n{rho_txt}")
    vol_pct = [r["volumePct"] for r in rows]
    mass_pct = [r["massPct"] for r in rows]
    x = np.arange(len(xtick_labels))
    w = 0.34
    peak = max(max(vol_pct), max(mass_pct))
    ymax = min(peak * 1.16 + 0.55, 11.0)
    ymax = max(ymax, peak + 0.8)

    fig, ax = plt.subplots(figsize=(10.2, 4.0), facecolor=VIZ_BG)
    ax.bar(
        x - w / 2,
        vol_pct,
        w,
        label="体积占比 %",
        color=THEME["cyan"],
        alpha=0.92,
        zorder=3,
    )
    ax.bar(
        x + w / 2,
        mass_pct,
        w,
        label="质量占比 %",
        color=THEME["gold"],
        alpha=0.92,
        zorder=3,
    )
    ax.set_xticks(x)
    ax.set_xticklabels(xtick_labels, fontsize=_TASK4_VALIDATION_TYPO["tick"], linespacing=0.95)
    ax.set_ylabel("占比 %", fontsize=_TASK4_VALIDATION_TYPO["axis"])
    ax.set_ylim(0, ymax)
    ax.margins(x=0.06)

    ann_fs = _TASK4_VALIDATION_TYPO["annotate"]
    for i, r in enumerate(rows):
        vy = _smart_bar_label_y(vol_pct[i], ymax)
        my = _smart_bar_label_y(mass_pct[i], ymax)
        if vy > vol_pct[i] + ymax * 0.05:
            ax.plot(
                [i - w / 2, i - w / 2],
                [vol_pct[i], vy - ymax * 0.02],
                color=THEME["cyan"],
                lw=0.8,
                alpha=0.55,
                zorder=2,
            )
        if my > mass_pct[i] + ymax * 0.05:
            ax.plot(
                [i + w / 2, i + w / 2],
                [mass_pct[i], my - ymax * 0.02],
                color=THEME["gold"],
                lw=0.8,
                alpha=0.55,
                zorder=2,
            )
        ax.text(
            i - w / 2,
            vy,
            f"{vol_pct[i]:.2f}%",
            ha="center",
            va="bottom",
            fontsize=ann_fs,
            color=THEME["cyan"],
            clip_on=True,
            zorder=4,
        )
        ax.text(
            i + w / 2,
            my,
            f"{mass_pct[i]:.1f}%",
            ha="center",
            va="bottom",
            fontsize=ann_fs,
            color=THEME["gold"],
            clip_on=True,
            zorder=4,
        )
    ax.legend(
        fontsize=_TASK4_VALIDATION_TYPO["legend"],
        loc="upper right",
        framealpha=0.92,
        borderpad=0.35,
    )
    _style_validation_chart(ax)
    fig.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.22)
    save_figure(fig, OUT / "task4_threshold_comparison.png", pad=0.02, skip_tight=True)


def task4_p88_sensitivity(validation: dict) -> None:
    rows = validation["p88Sweep"]
    pcts = [r["projPercentile"] for r in rows]
    ridge = [r["ridgePixelPct"] for r in rows]
    lo = [r["densityBand"][0] for r in rows]
    hi = [r["densityBand"][1] for r in rows]
    fw, fh = _TASK4_PERF_FIG_CHART
    fig, ax1 = plt.subplots(figsize=(fw, fh), facecolor=VIZ_BG)
    ax1.set_facecolor(PANEL_BG)
    ax1.plot(pcts, ridge, "o-", color=THEME["gold"], linewidth=LINE_WIDTH, label="亮脊像素占比 %")
    ax1.axvline(88, color=THEME["cyan"], linestyle="--", alpha=0.7, label="默认 P88")
    ax1.set_xlabel("投影百分位阈值", fontsize=_TASK4_PERFORMANCE_TYPO["axis"], labelpad=6)
    ax1.set_ylabel("亮脊像素占比 %", fontsize=_TASK4_PERFORMANCE_TYPO["axis"], labelpad=6)
    ax2 = ax1.twinx()
    ax2.plot(pcts, lo, "s--", color=THEME["purple"], alpha=0.85, label="密度带下界")
    ax2.plot(pcts, hi, "^--", color=THEME["cyan"], alpha=0.85, label="密度带上界")
    ax2.set_ylabel("反查密度带 ρ", fontsize=_TASK4_PERFORMANCE_TYPO["axis"], labelpad=8)
    lines1, lab1 = ax1.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines1 + lines2,
        lab1 + lab2,
        loc="upper center",
        bbox_to_anchor=(0.48, -0.26),
        ncol=2,
        fontsize=_TASK4_PERFORMANCE_TYPO["legend"],
        framealpha=0.92,
        borderpad=0.45,
        columnspacing=1.0,
    )
    _style_performance_chart(ax1, twin=ax2)
    fig.subplots_adjust(left=0.12, right=0.86, top=0.94, bottom=0.34)
    save_figure(fig, OUT / "task4_p88_sensitivity.png", pad=0.04, skip_tight=True)


def task4_projection_axes(vol: np.ndarray, timeline: dict, s99: dict) -> None:
    lo, hi = float(s99["p99"]), float(s99["max"])
    axes_spec = [
        ("xy", "XY（俯视 z）"),
        ("xz", "XZ（侧视 y）"),
        ("yz", "YZ（侧视 x）"),
    ]
    fw, fh = _TASK4_PERF_FIG_PROJ
    fig, axes = plt.subplots(1, 3, figsize=(fw, fh), facecolor=VIZ_BG)
    fig.subplots_adjust(left=0.02, right=0.98, top=0.90, bottom=0.06, wspace=0.06)
    for ax, (axis, title) in zip(axes, axes_spec):
        ax.set_facecolor(PANEL_BG)
        rgb = render_axis_projection(vol, timeline, axis, lo, hi)
        ax.imshow(rgb, origin="lower")
        ax.set_title(title, fontsize=_TASK4_PERFORMANCE_TYPO["subplot"], pad=6)
        ax.axis("off")
    save_figure(fig, OUT / "task4_projection_axes.png", pad=0.04, skip_tight=True)


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
    ymax = min(108, max(max(vals) * 1.18, 32))
    fw, fh = _TASK4_PERF_FIG_CHART
    fig, ax = plt.subplots(figsize=(fw, fh), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)
    bars = ax.bar(labels, vals, color=colors, alpha=0.9, width=0.62)
    ax.set_ylim(0, ymax)
    ax.set_ylabel("占比 %", fontsize=_TASK4_PERFORMANCE_TYPO["axis"], labelpad=6)
    ax.tick_params(axis="x", labelsize=_TASK4_PERFORMANCE_TYPO["tick"], pad=4)
    ann_fs = _TASK4_PERFORMANCE_TYPO["annotate"]
    for bar, v in zip(bars, vals):
        inside = v >= ymax * 0.72
        y_pos = v * 0.52 if inside else min(v + ymax * 0.035, ymax * 0.96)
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y_pos,
            f"{v:.1f}%",
            ha="center",
            va="center" if inside else "bottom",
            fontsize=ann_fs,
            color="#0a1020" if inside else "#e6edf3",
            clip_on=True,
        )
    _style_performance_chart(ax)
    fig.subplots_adjust(left=0.11, right=0.98, top=0.94, bottom=0.30)
    save_figure(fig, OUT / "task4_brush_precision.png", pad=0.04, skip_tight=True)


def task1_tf_gain_curve() -> None:
    ts = np.arange(100)
    t_norm = ts / 99.0
    opacity = 0.72 + t_norm * 0.38
    density_gain = np.where(t_norm < 0.45, -0.32 * (1.0 - t_norm / 0.45), 0.0)
    fig = plt.figure(figsize=(13, 6.2), facecolor=VIZ_BG)
    fig.subplots_adjust(top=0.72, bottom=0.13, left=0.08, right=0.90)
    ax1 = fig.add_subplot(111)
    ax1.set_facecolor(PANEL_BG)
    ax1.plot(ts, opacity, color=THEME["gold"], lw=LINE_WIDTH, label="opacityScale（不透明度乘子）")
    ax1.set_xlabel("时间步 t", fontsize=17, color=THEME["muted"], labelpad=10)
    ax1.set_ylabel("opacityScale", color=THEME["gold"], fontsize=17, labelpad=10)
    ax2 = ax1.twinx()
    ax2.plot(ts, density_gain, color=THEME["cyan"], lw=LINE_WIDTH, ls="--", label="densityGain（ρ 轴平移；负=压低 IGM）")
    ax2.set_ylabel("densityGain", color=THEME["cyan"], fontsize=17, labelpad=12)
    ax2.tick_params(colors=THEME["muted"], labelsize=14)
    ax2.axhline(0, color=THEME["muted"], lw=0.8, alpha=0.5)
    ax2.axvline(45, color=THEME["muted"], ls=":", alpha=0.7, label="t≈45 增益归零")
    lines1, lab1 = ax1.get_legend_handles_labels()
    lines2, lab2 = ax2.get_legend_handles_labels()
    ax1.legend(
        lines1 + lines2,
        lab1 + lab2,
        loc="lower right",
        fontsize=14,
        framealpha=0.92,
        facecolor=PANEL_BG,
        edgecolor="#3a4558",
    )
    fig.text(
        0.5,
        0.968,
        "capture 专用 TF 增益",
        ha="center",
        va="top",
        fontsize=20,
        color="#e6edf3",
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.875,
        "仅 capture.html · 交互页默认 opacityScale=1.15, densityGain=+0.12",
        ha="center",
        va="top",
        fontsize=15,
        color=THEME["muted"],
    )
    style_axes(ax1, labelsize=14)
    set_tick_density(ax1, factor=2.5, axes="xy")
    set_tick_density(ax2, factor=2.5, axes="y")
    save_figure(fig, OUT / "task1_tf_gain_curve.png", pad=0.18, skip_tight=True)
    print(f"TF gain curve: {OUT / 'task1_tf_gain_curve.png'}")


def task1_lighting_diagram() -> None:
    lit = lighting_vectors()
    fp = np.array(lit["focalPoint"])
    key = np.array(lit["keyLight"]["position"])
    fill = np.array(lit["fillLight"]["position"])
    lim = DOMAIN_LENGTH * 1.6
    ph = lit["phong"]
    fig = plt.figure(figsize=(7.6, 5.6))
    fig.patch.set_facecolor(VIZ_BG)
    ax = fig.add_subplot(111, projection="3d")
    ax.set_facecolor(PANEL_BG)
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
    ax.set_xlim(0, lim)
    ax.set_ylim(0, lim)
    ax.set_zlim(0, lim)
    ax.set_xlabel("X", labelpad=6)
    ax.set_ylabel("Y", labelpad=6)
    ax.set_zlabel("Z", labelpad=14)
    ax.tick_params(axis="z", pad=4)
    ax.view_init(elev=24, azim=-56)
    ax.set_title(
        f"Phong 光照示意（Ka={ph['Ka']}, Kd={ph['Kd']}, Ks={ph['Ks']}）",
        fontsize=11,
        pad=10,
    )
    ax.legend(loc="upper left", fontsize=9)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.fill = False
        axis.pane.set_edgecolor((78 / 255, 196 / 255, 255 / 255, 0.18))
    ax.grid(True, alpha=0.12)
    fig.subplots_adjust(left=0.02, right=0.84, bottom=0.06, top=0.90)
    fig.savefig(
        OUT / "task1_lighting_diagram.png",
        dpi=FIG_DPI,
        bbox_inches="tight",
        pad_inches=0.22,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
        pil_kwargs={"compress_level": 3},
    )
    plt.close(fig)
    print(f"Lighting diagram: {OUT / 'task1_lighting_diagram.png'}")


def task1_resolution_coarsening(ext: dict) -> None:
    rows = ext["resolutionCoarseningT99"]
    jboot = ext.get("resolutionJaccardBootstrapT99", {})
    labels = [r["label"] for r in rows]
    corr = [r["projCorrWith128"] for r in rows]
    jacc_fixed = [r["ridgeJaccardVs128"] for r in rows]
    x = np.arange(len(labels))
    w = 0.34

    fig, ax = plt.subplots(figsize=(11.5, 5.8), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)

    x_corr = x - w / 2
    x_jacc = x + w / 2
    bars_r = ax.bar(
        x_corr,
        corr,
        w,
        label="投影相关 r",
        color=THEME["cyan"],
        edgecolor="#3a4558",
        linewidth=0.9,
        zorder=2,
    )
    bars_j = ax.bar(
        x_jacc,
        jacc_fixed,
        w,
        label="脊 Jaccard",
        color=THEME["gold"],
        alpha=0.78,
        edgecolor="#3a4558",
        linewidth=0.9,
        zorder=2,
    )

    def _bar_label(bar, val: float, *, color: str = "#e6edf3") -> None:
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.016,
            f"{val:.3f}",
            ha="center",
            va="bottom",
            fontsize=13,
            color=color,
            fontweight="bold",
            zorder=8,
        )

    for bar, val in zip(bars_r, corr):
        _bar_label(bar, val)
    for i, (bar, val) in enumerate(zip(bars_j, jacc_fixed)):
        if i == 1 and jboot:
            continue
        _bar_label(bar, val, color=THEME["gold"])

    if jboot and len(jacc_fixed) > 1:
        mean_j = jboot.get("jaccardMean", jacc_fixed[1])
        std_j = jboot.get("jaccardStd", 0)
        fixed_64 = jboot.get("jaccardFixedOrigin", jacc_fixed[1])
        xi = x_jacc[1]
        ax.axvspan(x[1] - 0.46, x[1] + 0.46, color=THEME["gold"], alpha=0.07, zorder=1)
        ax.scatter(
            [xi - 0.13],
            [fixed_64],
            marker="D",
            s=110,
            color=THEME["gold"],
            edgecolors="#e6edf3",
            linewidths=1.0,
            zorder=6,
            label="64³ 原点对齐",
        )
        ax.errorbar(
            [xi + 0.13],
            mean_j,
            yerr=std_j,
            fmt="o",
            color="white",
            ecolor=THEME["coral"],
            capsize=7,
            lw=2.4,
            markersize=9,
            zorder=7,
            label=f"64³ 8 偏移 均值±1×样本 SD (n={jboot.get('nReplicates', 8)})",
        )
        ax.annotate(
            f"原点 {fixed_64:.2f}",
            xy=(xi - 0.13, fixed_64),
            xytext=(xi - 0.13, 0.97),
            fontsize=12,
            color=THEME["gold"],
            ha="center",
            va="bottom",
            bbox=dict(
                boxstyle="round,pad=0.35",
                fc=(15 / 255, 20 / 255, 36 / 255, 0.92),
                ec=THEME["gold"],
                lw=1.0,
            ),
            arrowprops=dict(arrowstyle="-|>", color=THEME["gold"], lw=1.3, shrinkA=0, shrinkB=5),
            zorder=9,
        )
        ax.annotate(
            f"偏移 {mean_j:.3f}±{std_j:.3f}\n(±1 SD)",
            xy=(xi + 0.13, mean_j),
            xytext=(xi + 0.13, 0.30),
            fontsize=12,
            color=THEME["coral"],
            ha="center",
            va="top",
            bbox=dict(
                boxstyle="round,pad=0.35",
                fc=(15 / 255, 20 / 255, 36 / 255, 0.92),
                ec=THEME["coral"],
                lw=1.0,
            ),
            arrowprops=dict(arrowstyle="-|>", color=THEME["coral"], lw=1.3, shrinkA=0, shrinkB=5),
            zorder=9,
        )

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=13)
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("相对 128³ 保真度", fontsize=15, color=THEME["muted"], labelpad=10)
    ax.set_title(
        "分辨率粗化敏感性（t=99）：原点对齐 vs 随机 lattice 偏移",
        fontsize=18,
        color="#e6edf3",
        fontweight="bold",
        pad=22,
        loc="center",
    )
    ax.text(
        0.5,
        1.015,
        "均匀粗化 ≠ AMR；64³ 组内对比投影相关 r（左柱）与脊 Jaccard（右柱），含原点对齐与 8 组 lattice 偏移",
        transform=ax.transAxes,
        fontsize=12,
        color=THEME["muted"],
        ha="center",
        va="bottom",
    )
    ax.axhline(1.0, color=THEME["muted"], lw=0.8, ls="--", alpha=0.35, zorder=0)
    ax.legend(
        fontsize=12,
        loc="lower left",
        ncol=2,
        framealpha=0.92,
        facecolor=PANEL_BG,
        edgecolor="#3a4558",
        columnspacing=1.2,
        handlelength=1.6,
    )
    style_axes(ax, labelsize=13)
    set_tick_density(ax, factor=2.5, axes="y")
    fig.subplots_adjust(top=0.82, bottom=0.12, left=0.08, right=0.98)
    save_figure(fig, OUT / "task1_resolution_coarsening.png", pad=0.14, skip_tight=True)
    print(f"Resolution coarsening: {OUT / 'task1_resolution_coarsening.png'}")


def task2_bootstrap_ci(ext: dict) -> None:
    b = ext["bootstrapSpatial"]
    labels = ["Moran's I", "ξ(r=1)"]
    t0_means = [b["t0"]["moransI"]["mean"], b["t0"]["xiR1"]["mean"]]
    t0_std = [b["t0"]["moransI"]["std"], b["t0"]["xiR1"]["std"]]
    t99_means = [b["t99"]["moransI"]["mean"], b["t99"]["xiR1"]["mean"]]
    t99_std = [b["t99"]["moransI"]["std"], b["t99"]["xiR1"]["std"]]
    x = np.arange(2)
    w = 0.35
    fig, ax = plt.subplots(figsize=(8.8, 3.6), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)
    _err_kw = dict(elinewidth=2.6, capthick=2.6, alpha=1.0)
    ax.bar(
        x - w / 2,
        t0_means,
        w,
        yerr=t0_std,
        capsize=7,
        label="t=0",
        color=THEME["purple"],
        alpha=0.92,
        error_kw={**_err_kw, "ecolor": "#ddd6ff"},
    )
    ax.bar(
        x + w / 2,
        t99_means,
        w,
        yerr=t99_std,
        capsize=7,
        label="t=99",
        color=THEME["gold"],
        alpha=0.92,
        error_kw={**_err_kw, "ecolor": "#ffe566"},
    )
    ylo = min(t0_means + t99_means) - max(t0_std + t99_std) * 2.5
    yhi = max(t0_means + t99_means) + max(t0_std + t99_std) * 3.5
    ax.set_ylim(max(0, ylo), yhi)
    for i, (v0, v99) in enumerate(zip(t0_means, t99_means)):
        d = v99 - v0
        ax.text(
            x[i],
            max(v0 + t0_std[i], v99 + t99_std[i]) + (yhi - ylo) * 0.04,
            f"Δ={d:+.4f}",
            ha="center",
            va="bottom",
            fontsize=11,
            color=THEME["cyan"],
            fontweight="bold",
        )
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=13)
    ax.set_ylabel("子块 bootstrap 均值 ±1σ", fontsize=13, color=THEME["muted"])
    ax.legend(loc="upper right", fontsize=12, framealpha=0.92, facecolor=(12 / 255, 16 / 255, 28 / 255, 0.92), edgecolor="#3a4558")
    style_axes(ax, labelsize=12)
    set_tick_density(ax, factor=2.0, axes="y")
    fig.subplots_adjust(top=0.94, bottom=0.16, left=0.12, right=0.97)
    save_figure(fig, OUT / "task2_bootstrap_ci.png", pad=0.08, skip_tight=True)


def task3_bin_kl(ext: dict) -> None:
    """CDF L∞ bin sensitivity — Figure 22 (polished bar panel)."""
    import matplotlib.patches as mpatches
    from matplotlib.lines import Line2D

    sens = ext.get("binSensitivityT99", {})
    rows = sorted(sens.get("binRows", ext.get("binKlT99", [])), key=lambda r: r["bins"])
    if not rows:
        return

    bins = [r["bins"] for r in rows]
    linf = [r.get("cdfLinfVs128", r.get("klToSelf128", 0)) for r in rows]
    fill = {64: THEME["purple"], 128: THEME["cyan"], 256: THEME["gold"]}
    edge = {64: "#a898f8", 128: "#6ef0e4", 256: "#ffe066"}

    fig, ax = plt.subplots(figsize=(5.0, 3.6))
    fig.patch.set_facecolor(VIZ_BG)

    x = np.arange(len(bins))
    width = 0.52
    x_pad = 0.32
    y_max = max(linf) if max(linf) > 0 else 0.0012
    y_top = y_max * 1.22

    ax.axhspan(0, 0.0015, color=THEME["cyan"], alpha=0.07, zorder=0)
    ax.axhline(0.0012, color=THEME["gold"], ls=(0, (4, 3)), lw=1.1, alpha=0.65, zorder=1)

    for i, (b, val) in enumerate(zip(bins, linf)):
        c, ec = fill.get(b, THEME["blue"]), edge.get(b, "#c8d8f0")
        if b == 128:
            ax.scatter(
                [i],
                [0],
                s=90,
                c=c,
                edgecolors=ec,
                linewidths=1.8,
                marker="D",
                zorder=4,
            )
            ax.annotate(
                "基准 0.0000",
                (i, 0),
                xytext=(0, 10),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8.5,
                color=ec,
                fontweight="bold",
            )
        else:
            ax.bar(
                i,
                val,
                width=width,
                color=c,
                edgecolor=ec,
                linewidth=1.6,
                alpha=0.93,
                zorder=3,
            )
            ax.annotate(
                f"{val:.4f}",
                (i, val),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9.5,
                color=ec,
                fontweight="bold",
            )

    ax.set_xlim(x[0] - width / 2 - x_pad, x[-1] + width / 2 + x_pad)
    ax.set_ylim(0, y_top)
    ax.set_xticks(x)
    ax.set_xticklabels([str(b) for b in bins], fontsize=10)
    ax.set_xlabel("分箱数（log 等距边界，全域统一）", fontsize=9.5, labelpad=4)
    ax.set_ylabel("CDF L∞ 距（相对 128 bins）", fontsize=9.5, labelpad=4)
    ax.tick_params(axis="both", labelsize=8.5, pad=2)

    style_axes(ax)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _p: f"{v:.4f}"))

    ax.legend(
        handles=[
            mpatches.Patch(facecolor=THEME["cyan"], alpha=0.18, edgecolor="none", label="可接受带 (<0.0015)"),
            Line2D([0], [0], color=THEME["gold"], ls="--", lw=1.1, label="引用上界 0.0012"),
        ],
        loc="upper right",
        fontsize=7.5,
        framealpha=0.9,
        borderpad=0.4,
        labelspacing=0.35,
        handlelength=1.4,
    )

    fig.suptitle(
        "t=99 分箱敏感度：CDF 最大偏差",
        fontsize=11.5,
        fontweight="bold",
        color="#f8fbff",
        y=0.99,
    )
    fig.text(
        0.5,
        0.925,
        "log 嵌套边界下 KL≈0 为恒等式",
        ha="center",
        va="top",
        fontsize=8.5,
        color=THEME["muted"],
    )

    fig.tight_layout(rect=[0, 0, 1, 0.86])
    fig.savefig(
        OUT / "task3_bin_kl.png",
        dpi=FIG_DPI,
        bbox_inches="tight",
        pad_inches=0.08,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
        pil_kwargs={"compress_level": 3},
    )
    plt.close(fig)


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


def _brush_kpi_bar_label(r: dict) -> str:
    return r["label"].replace("自定义：", "").replace("区间（对照）", "")


def _draw_brush_kpi_detail_table(ax, custom: list[dict]) -> None:
    """右侧明细表：避免条形图上的文字重叠。"""
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    row_h = 1.0 / (len(custom) + 1.1)
    y_hdr = 0.97
    ax.text(0.0, y_hdr, "区间", fontsize=_TASK4_VALIDATION_TYPO["table"], color=THEME["muted"], va="top")
    ax.text(0.52, y_hdr, "占比", fontsize=_TASK4_VALIDATION_TYPO["table"], color=THEME["muted"], va="top", ha="right")
    ax.text(1.0, y_hdr, "显示/真值", fontsize=_TASK4_VALIDATION_TYPO["table"], color=THEME["muted"], va="top", ha="right")
    for i, r in enumerate(custom):
        y = y_hdr - (i + 1) * row_h
        label = _brush_kpi_bar_label(r)
        color = THEME["gold"] if "对照" in r["label"] else THEME["cyan"]
        pct = r["reportedOverTruePct"]
        ax.text(0.0, y, label, fontsize=_TASK4_VALIDATION_TYPO["table"], color=color, va="top")
        ax.text(
            0.52,
            y,
            f"{pct:.2f}%",
            fontsize=_TASK4_VALIDATION_TYPO["table"],
            color="#e6edf3",
            va="top",
            ha="right",
        )
        ax.text(
            1.0,
            y,
            f"{r['reportedCount']:,}/{r['trueVoxels']:,}",
            fontsize=_TASK4_VALIDATION_TYPO["table_muted"],
            color=THEME["muted"],
            va="top",
            ha="right",
        )


def task4_brush_kpi_sampling(brush_val: dict) -> None:
    """早停 KPI + 采样召回；①/② 分区标题与图表分槽，避免重叠遮挡。"""
    bench = brush_val.get("benchmark", {})
    custom = bench.get("customBrushErrors", [])
    sample = bench.get("sampleRecall")
    if not custom and not sample:
        return

    fig = plt.figure(figsize=(10.0, 5.25), facecolor=VIZ_BG)
    # ① 标题 / ① 图 / 留白 / ② 块：留白行避免 ② 标题与 ① 轴标叠字
    gs_outer = gridspec.GridSpec(
        4,
        1,
        height_ratios=[0.10, 2.18, 0.15, 0.98],
        hspace=0.10,
        left=0.08,
        right=0.98,
        top=0.975,
        bottom=0.08,
    )

    if custom:
        _validation_section_caption(
            fig.add_subplot(gs_outer[0]),
            "① 各刷选区间 · 显示/真值占比（对数轴；虚线=100% 全网格）",
        )
        gs_bar_tbl = gridspec.GridSpecFromSubplotSpec(
            1,
            2,
            subplot_spec=gs_outer[1],
            width_ratios=[1.08, 0.68],
            wspace=0.05,
        )
        ax_bar = fig.add_subplot(gs_bar_tbl[0])
        ax_tbl = fig.add_subplot(gs_bar_tbl[1])

        labels = [_brush_kpi_bar_label(r) for r in custom]
        reported_pct = [max(r["reportedOverTruePct"], 0.35) for r in custom]
        colors = [THEME["gold"] if "对照" in r["label"] else THEME["cyan"] for r in custom]
        ax_bar.barh(labels, reported_pct, color=colors, alpha=0.92, height=0.56)
        ax_bar.set_xscale("log")
        ax_bar.set_xlim(0.35, 150)
        ax_bar.axvline(100, color=THEME["muted"], ls="--", lw=1.0, zorder=0)
        ax_bar.set_xlabel("×100 %", fontsize=_TASK4_VALIDATION_TYPO["axis"], labelpad=2)
        ax_bar.xaxis.set_label_coords(0.42, -0.06)
        ax_bar.tick_params(axis="x", pad=1)
        log_ticks = FixedLocator([0.5, 1, 2, 5, 10, 100])
        ax_bar.xaxis.set_major_locator(log_ticks)
        ax_bar.xaxis.set_major_formatter(FixedFormatter(["0.5", "1", "2", "5", "10", "100"]))
        _style_validation_chart(ax_bar)
        _draw_brush_kpi_detail_table(ax_tbl, custom)
        spacer = fig.add_subplot(gs_outer[2])
        spacer.set_axis_off()

    if sample:
        gs_bot = gridspec.GridSpecFromSubplotSpec(
            2,
            1,
            subplot_spec=gs_outer[3],
            height_ratios=[0.12, 1.0],
            hspace=0.10,
        )
        _validation_section_caption(
            fig.add_subplot(gs_bot[0]),
            "② Top 1% · 真值体素召回与网格覆盖率",
        )
        ax_sub = fig.add_subplot(gs_bot[1])
        sub_labels = ["真值体素召回", "网格覆盖率"]
        sub_vals = [sample["recallVsTrue"] * 100, sample["gridCoverage"] * 100]
        peak = max(sub_vals)
        ymax = float(np.ceil(max(peak * 1.22, 15.0) / 5.0) * 5.0)
        xpos = np.arange(len(sub_labels))
        sub_bars = ax_sub.bar(
            xpos,
            sub_vals,
            color=[THEME["gold"], THEME["cyan"]],
            width=0.40,
            zorder=3,
        )
        ax_sub.set_xticks(xpos)
        ax_sub.set_xticklabels(sub_labels, fontsize=_TASK4_VALIDATION_TYPO["tick"])
        ax_sub.set_ylabel("占比 %", fontsize=_TASK4_VALIDATION_TYPO["axis"], labelpad=4)
        ax_sub.set_xlim(-0.55, len(sub_labels) - 0.45)
        ax_sub.margins(x=0.02)
        _style_validation_chart(ax_sub)
        ax_sub.set_autoscaley_on(False)
        ax_sub.set_ylim(0, ymax)
        y_ticks = list(range(0, int(ymax) + 1, 5))
        ax_sub.yaxis.set_major_locator(FixedLocator(y_ticks))
        ax_sub.yaxis.set_major_formatter(FixedFormatter([str(t) for t in y_ticks]))
        for bar, v in zip(sub_bars, sub_vals):
            ax_sub.text(
                bar.get_x() + bar.get_width() / 2,
                min(v + ymax * 0.035, ymax * 0.96),
                f"{v:.1f}%",
                ha="center",
                va="bottom",
                fontsize=_TASK4_VALIDATION_TYPO["annotate"],
                color="#e6edf3",
                clip_on=False,
            )

    save_figure(fig, OUT / "task4_brush_kpi_sampling.png", pad=0.02, skip_tight=True)


def task4_brush_sample_recall(brush_val: dict) -> None:
    """生成合并 KPI 图及附录用子图原件。"""
    task4_brush_kpi_sampling(brush_val)

    custom = brush_val.get("benchmark", {}).get("customBrushErrors", [])
    if custom:
        fig = plt.figure(figsize=(9.2, 4.6), facecolor=VIZ_BG)
        gs = gridspec.GridSpec(1, 2, width_ratios=[1.05, 0.72], wspace=0.06)
        fig.subplots_adjust(left=0.09, right=0.98, top=0.90, bottom=0.14)
        ax_bar = fig.add_subplot(gs[0])
        ax_tbl = fig.add_subplot(gs[1])
        labels = [_brush_kpi_bar_label(r) for r in custom]
        reported_pct = [max(r["reportedOverTruePct"], 0.35) for r in custom]
        colors = [THEME["gold"] if "对照" in r["label"] else THEME["cyan"] for r in custom]
        ax_bar.barh(labels, reported_pct, color=colors, alpha=0.92, height=0.58)
        ax_bar.set_xscale("log")
        ax_bar.set_xlim(0.35, 150)
        ax_bar.axvline(100, color=THEME["muted"], ls="--", lw=1.1, label="100%（全网格）")
        ax_bar.set_xlabel(
            "显示数 / 真值体素数 ×100 %（对数轴）",
            fontsize=_TASK4_VALIDATION_TYPO["axis"],
        )
        ax_bar.set_title(
            "自定义拖拽刷选 KPI（t=99, stride=2, maxPoints=8000）",
            fontsize=_TASK4_VALIDATION_TYPO["axis"] + 1,
            pad=8,
        )
        ax_bar.legend(fontsize=_TASK4_VALIDATION_TYPO["legend"], loc="lower left")
        log_ticks = FixedLocator([0.5, 1, 2, 5, 10, 100])
        ax_bar.xaxis.set_major_locator(log_ticks)
        ax_bar.xaxis.set_major_formatter(FixedFormatter(["0.5", "1", "2", "5", "10", "100"]))
        _style_validation_chart(ax_bar)
        _draw_brush_kpi_detail_table(ax_tbl, custom)
        save_figure(fig, OUT / "task4_custom_brush_error.png", pad=0.06, skip_tight=True)

    sample = brush_val.get("benchmark", {}).get("sampleRecall")
    if not sample:
        return
    ymax = max(sample["recallVsTrue"] * 100, sample["gridCoverage"] * 100) * 1.42
    ymax = max(ymax, 17.5)
    fig, ax = plt.subplots(figsize=(7.2, 3.2), facecolor=VIZ_BG)
    labels = ["真值体素召回", "网格覆盖率"]
    vals = [sample["recallVsTrue"] * 100, sample["gridCoverage"] * 100]
    xpos = np.arange(len(labels))
    bars = ax.bar(xpos, vals, color=[THEME["gold"], THEME["cyan"]], width=0.42)
    ax.set_xticks(xpos)
    ax.set_xticklabels(labels, fontsize=_TASK4_VALIDATION_TYPO["tick"])
    ax.set_ylim(0, ymax)
    ax.set_ylabel("占比 %", fontsize=_TASK4_VALIDATION_TYPO["axis"])
    ax.set_title(
        f"Top 1% 早停（stride={sample['stride']}, max={sample['maxPoints']}）"
        f" · 命中 {sample['uniqueTrueFound']:,}/{sample['trueBrushVoxels']:,}",
        fontsize=_TASK4_VALIDATION_TYPO["axis"] + 1,
        pad=8,
    )
    for bar, v in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + ymax * 0.035,
            f"{v:.1f}%",
            ha="center",
            va="bottom",
            fontsize=_TASK4_VALIDATION_TYPO["annotate"],
        )
    _style_validation_chart(ax)
    fig.subplots_adjust(left=0.12, right=0.96, top=0.84, bottom=0.18)
    save_figure(fig, OUT / "task4_brush_sample_recall.png", pad=0.06, skip_tight=True)


def task4_ridge_methods(ext: dict) -> None:
    m = ext["ridgeMethodsT99"]
    vals = [m["jaccard"] * 100, m["precisionP88vsGrad"] * 100]
    ymax = min(52, max(max(vals) * 1.42, 28))
    fw, fh = _TASK4_PERF_FIG_CHART
    fig, ax = plt.subplots(figsize=(fw, fh), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)
    bars = ax.bar(
        ["Jaccard", "P88与梯度重叠"],
        vals,
        color=[THEME["gold"], THEME["purple"]],
        width=0.48,
    )
    ax.set_ylim(0, ymax)
    ax.set_ylabel("重叠 %", fontsize=_TASK4_PERFORMANCE_TYPO["axis"], labelpad=6)
    ax.tick_params(axis="x", labelsize=_TASK4_PERFORMANCE_TYPO["tick"], pad=4)
    for bar, v in zip(bars, vals):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            v + ymax * 0.04,
            f"{v:.1f}%",
            ha="center",
            va="bottom",
            fontsize=_TASK4_PERFORMANCE_TYPO["annotate"],
            clip_on=True,
        )
    _style_performance_chart(ax)
    fig.subplots_adjust(left=0.13, right=0.96, top=0.94, bottom=0.22)
    save_figure(fig, OUT / "task4_ridge_methods.png", pad=0.04, skip_tight=True)


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
    ]
    for out_name, title, subtitle, parts, layout, sub_labels in stacks:
        paths = [OUT / p for p in parts if (OUT / p).exists()]
        if len(paths) < 2:
            print(f"Skip composite {out_name}: need ≥2 panels, got {len(paths)}")
            continue
        labels = sub_labels[: len(paths)]
        wrapped = []
        stack_gap = 28 if out_name == "task1_render_params.png" else 16
        wrap_kwargs: dict = {}
        if out_name == "task1_render_params.png":
            from PIL import Image as PILImage

            max_w = min(3840, max(PILImage.open(p).width for p in paths))
            panel_h = 980
            half_w = (max_w - 24) // 2
            wrap_common = dict(
                label_font_size=72,
                corner_font_size=48,
                content_height=panel_h,
            )
            for i, (p, lab) in enumerate(zip(paths, labels)):
                letter, caption = split_panel_label(lab)
                kw = {
                    **wrap_common,
                    "max_content_width": max_w if i == 0 else half_w,
                }
                wrapped.append(
                    wrap_panel(
                        p,
                        label=caption,
                        corner_letter=letter,
                        accent=THEME["cyan"],
                        **kw,
                    )
                )
            row_bot = stitch_panels_png(
                wrapped[1:3],
                direction="horizontal",
                gap=24,
                max_width=max_w,
            )
            body = stitch_panels_png(
                [wrapped[0], row_bot],
                direction="vertical",
                gap=16,
                max_width=max_w,
            )
        else:
            for p, lab in zip(paths, labels):
                letter, caption = split_panel_label(lab)
                wrapped.append(
                    wrap_panel(
                        p,
                        label=caption,
                        corner_letter=letter,
                        accent=THEME["cyan"],
                        **wrap_kwargs,
                    )
                )
            if layout == "grid2x2" and len(wrapped) >= 4:
                top = stitch_panels_png(wrapped[:2], direction="horizontal", gap=16, max_width=4800)
                bot = stitch_panels_png(wrapped[2:4], direction="horizontal", gap=16, max_width=4800)
                body = stitch_panels_png([top, bot], direction="vertical", gap=20, max_width=4800)
            else:
                body = stitch_panels_png(
                    wrapped,
                    direction="vertical",
                    gap=stack_gap,
                    max_width=4800,
                )
        if out_name == "task1_render_params.png":
            final = compose_sheet(
                title,
                subtitle,
                [body],
                max_width=min(body.width, 3840),
                title_font_size=96,
                subtitle_font_size=52,
                title_pad_y=44,
                title_pad_x=52,
            )
        else:
            final = compose_sheet(title, subtitle, [body], max_width=min(body.width, 3840))
        save_pil_png(final, OUT / out_name)
        print(f"Composite {out_name}: {final.width}×{final.height}px")

    compose_task2_spatial_summary()
    compose_task4_brush_validation_summary()
    compose_task4_performance_summary()
    compose_task4_discovery_summary()


def _vol_content_mask(rgb: np.ndarray) -> np.ndarray:
    """体渲染截图中非暗背景像素（半透明蓝雾 + 亮丝）。"""
    return ~(
        (rgb[:, :, 0] < 35) & (rgb[:, :, 1] < 45) & (rgb[:, :, 2] < 70)
    )


def _crop_vol_content(img: Image.Image, *, pad_frac: float = 0.012) -> Image.Image:
    """以内容质心为中心裁成正方形，避免原图右侧留白导致立方体偏右。"""
    rgb = np.array(img.convert("RGB"))
    content = _vol_content_mask(rgb)
    if not content.any():
        return img
    ys, xs = np.where(content)
    cx, cy = float(xs.mean()), float(ys.mean())
    x0, x1 = float(np.percentile(xs, 2)), float(np.percentile(xs, 98))
    y0, y1 = float(np.percentile(ys, 2)), float(np.percentile(ys, 98))
    half = max(x1 - x0, y1 - y0) / 2.0 * (1.0 + pad_frac * 2)
    h, w = rgb.shape[:2]
    side = int(round(half * 2))
    left = int(round(cx - side / 2))
    top = int(round(cy - side / 2))
    left = max(0, min(left, w - side))
    top = max(0, min(top, h - side))
    side = min(side, w - left, h - top)
    return img.crop((left, top, left + side, top + side))


def _fit_cover(img: Image.Image, tw: int, th: int, *, zoom: float = 1.0) -> Image.Image:
    """等比放大后按内容质心居中裁剪，填满目标框。"""
    iw, ih = img.size
    scale = max(tw / iw, th / ih) * zoom
    sw, sh = max(1, int(iw * scale)), max(1, int(ih * scale))
    scaled = img.resize((sw, sh), Image.Resampling.LANCZOS)
    rgb = np.array(scaled.convert("RGB"))
    content = _vol_content_mask(rgb)
    if content.any():
        ys, xs = np.where(content)
        cx, cy = float(xs.mean()), float(ys.mean())
    else:
        cx, cy = sw / 2.0, sh / 2.0
    left = int(round(cx - tw / 2))
    top = int(round(cy - th / 2))
    left = max(0, min(left, sw - tw))
    top = max(0, min(top, sh - th))
    return scaled.crop((left, top, left + tw, top + th))


def _trim_image_margins(img: Image.Image, *, bg: str = VIZ_BG, pad: int = 6) -> Image.Image:
    """裁掉 matplotlib 导出图四周近背景空白。"""
    rgb = np.array(img.convert("RGB"))
    bg_rgb = np.array(hex_to_rgb(bg), dtype=np.int16)
    diff = np.abs(rgb.astype(np.int16) - bg_rgb).max(axis=2)
    mask = diff > 14
    if not mask.any():
        return img
    ys, xs = np.where(mask)
    x0 = max(0, int(xs.min()) - pad)
    y0 = max(0, int(ys.min()) - pad)
    x1 = min(img.width, int(xs.max()) + pad + 1)
    y1 = min(img.height, int(ys.max()) + pad + 1)
    return img.crop((x0, y0, x1, y1))


def _performance_panel_content(path: Path, content_w: int, content_h: int, *, trim: bool = True) -> Image.Image:
    raw = Image.open(path).convert("RGBA")
    if trim:
        raw = _trim_image_margins(raw, pad=10)
    return fit_panel_contain(raw, content_w, content_h, allow_upscale=False, valign="center")


def compose_task4_performance_summary() -> None:
    """图13：刷选扩展验证 2×2 — 统一列宽/内容高，裁边减空白。"""
    paths = [
        OUT / "task4_projection_axes.png",
        OUT / "task4_p88_sensitivity.png",
        OUT / "task4_brush_precision.png",
        OUT / "task4_ridge_methods.png",
    ]
    if not all(p.exists() for p in paths):
        print("Skip task4_performance_summary: missing panels")
        return

    cfg = _TASK4_PERFORMANCE_COMPOSE
    col_w = cfg["col_w"]
    content_w = col_w - PANEL_PAD * 2
    content_h = cfg["content_h"]
    _fs = dict(
        header="inline",
        label_font_size=cfg["panel_label"],
        corner_font_size=cfg["panel_corner"],
        subtitle_font_size=cfg["panel_sub"],
    )

    sub_a = "XY / XZ / YZ · Top 1% 高亮"
    sub_b = "投影百分位 · 亮脊占比 · 反查密度带"
    sub_c = "精确率 / 召回 / 误报 / 漏报"
    sub_d = "Jaccard · P88 vs 梯度脊"
    if STATS.exists():
        try:
            timeline = json.loads(STATS.read_text(encoding="utf-8"))
            p99 = timeline["timesteps"][99]["p99"]
            sub_a = f"XY / XZ / YZ · ρ≥{p99:.2f}"
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
    val_path = OUT / "brush_validation.json"
    if val_path.exists():
        try:
            m = json.loads(val_path.read_text(encoding="utf-8"))["fpFnDefault"]
            sub_c = (
                f"孤立高密 {m['isolatedHighDensityInBrush']:,} "
                f"({m['isolatedRateInBrush'] * 100:.2f}% of brush)"
            )
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    specs = [
        (paths[0], "(a)", "三向最大密度投影", sub_a),
        (paths[1], "(b)", "P88 亮脊阈值敏感度", sub_b),
        (paths[2], "(c)", "刷选 vs filament 代理", sub_c),
        (paths[3], "(d)", "脊线方法对照", sub_d),
    ]
    wrapped: list[Image.Image] = []
    for path, letter, label, subtitle in specs:
        inner = _performance_panel_content(path, content_w, content_h)
        wrapped.append(
            wrap_panel(
                inner,
                corner_letter=letter,
                label=label,
                subtitle=subtitle,
                accent=THEME["cyan"],
                **_fs,
            )
        )

    row_top_h = max(wrapped[0].height, wrapped[1].height)
    row_bot_h = max(wrapped[2].height, wrapped[3].height)
    grid_w = col_w * 2 + cfg["grid_gap"]
    top = stitch_panels_png(
        [
            fit_panel_contain(wrapped[0], col_w, row_top_h),
            fit_panel_contain(wrapped[1], col_w, row_top_h),
        ],
        direction="horizontal",
        gap=cfg["grid_gap"],
        max_width=grid_w,
        draw_dividers=False,
    )
    bot = stitch_panels_png(
        [
            fit_panel_contain(wrapped[2], col_w, row_bot_h),
            fit_panel_contain(wrapped[3], col_w, row_bot_h),
        ],
        direction="horizontal",
        gap=cfg["grid_gap"],
        max_width=grid_w,
        draw_dividers=False,
    )
    body = stitch_panels_png(
        [top, bot],
        direction="vertical",
        gap=cfg["row_gap"],
        max_width=grid_w,
        draw_dividers=False,
    )
    final = compose_sheet(
        "刷选扩展验证",
        "(a) 三向投影 · (b) P88 敏感度 · (c) 精确率/召回 · (d) 脊线方法",
        [body],
        max_width=min(body.width, 3840),
        title_font_size=cfg["main_title"],
        subtitle_font_size=cfg["sheet_sub"],
        title_pad_y=cfg["title_pad_y"],
        title_pad_x=cfg["title_pad_x"],
        title_subtitle_gap=cfg["title_subtitle_gap"],
        title_align="center",
    )
    save_pil_png(final, OUT / "task4_performance_summary.png")
    print(f"Composite task4_performance_summary.png: {final.width}×{final.height}px")


def _validation_chart_raster(path: Path, content_w: int) -> Image.Image:
    """裁边后按目标宽度缩放，高度随内容，避免固定框留白。"""
    raw = _trim_image_margins(Image.open(path).convert("RGBA"), pad=3)
    scale = content_w / raw.width
    nh = max(1, int(raw.height * scale))
    return raw.resize((content_w, nh), Image.Resampling.LANCZOS)


def compose_task4_brush_validation_summary() -> None:
    """图12：两级标题（总标题 + 分区标题/说明），子图无重复标题，裁边减底部空白。"""
    a_path = OUT / "task4_threshold_comparison.png"
    b_path = OUT / "task4_brush_kpi_sampling.png"
    if not a_path.exists() or not b_path.exists():
        print("Skip task4_brush_validation_summary: missing panels")
        return

    cfg = _TASK4_VALIDATION_COMPOSE
    content_w = cfg["content_w"]
    inner_w = content_w
    _fs = dict(
        header="inline",
        label_font_size=cfg["panel_label"],
        corner_font_size=cfg["panel_corner"],
        subtitle_font_size=cfg["panel_sub"],
        header_content_gap=cfg["panel_header_content_gap"],
        subtitle_gap=cfg["panel_subtitle_gap"],
        subtitle_tail_pad=cfg["panel_subtitle_tail_pad"],
    )

    sub_a = "t=99 · p95 / 90–99% 纤维带 / Top 1% 的体积与质量占比"
    sub_b = "t=99 · stride=2, maxPoints=8000 · 显示数相对全网格真值"
    val_path = OUT / "brush_validation.json"
    if val_path.exists():
        try:
            bench = json.loads(val_path.read_text(encoding="utf-8")).get("benchmark", {})
            sample = bench.get("sampleRecall", {})
            early = bench.get("top1_earlyExit", {})
            full = bench.get("top1_fullCount", {})
            hit = f"{sample.get('uniqueTrueFound', 0):,}/{sample.get('trueBrushVoxels', 0):,}"
            t_early = f"{float(early.get('elapsedMs', 0)):.0f}"
            t_full = f"{float(full.get('elapsedMs', 0)):.0f}"
            sub_b = (
                f"命中 {hit} · 早停 {t_early} ms / 全网格 {t_full} ms · "
                "体渲染/投影高亮不受采样限制"
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError):
            pass

    specs = [
        (a_path, "(a)", "阈值对比", sub_a),
        (b_path, "(b)", "早停采样 KPI", sub_b),
    ]
    panels = []
    for path, letter, caption, subtitle in specs:
        inner = _validation_chart_raster(path, inner_w)
        panels.append(
            wrap_panel(
                inner,
                corner_letter=letter,
                label=caption,
                subtitle=subtitle,
                **_fs,
            )
        )
    card_w = max(p.width for p in panels)
    panels = [fit_panel_width(p, card_w) for p in panels]
    body = stitch_panels_png(
        panels,
        direction="vertical",
        gap=cfg["stack_gap"],
        max_width=card_w,
        draw_dividers=False,
    )
    body = _trim_image_margins(body, pad=1)
    final = compose_sheet(
        "刷选验证汇总",
        None,
        [body],
        max_width=min(body.width, 3840),
        title_font_size=cfg["main_title"],
        title_pad_y=cfg["title_pad_y"],
        title_pad_x=cfg["title_pad_x"],
        title_subtitle_gap=10,
        title_align="center",
    )
    final = _trim_image_margins(final, pad=cfg["title_pad_y"])
    save_pil_png(final, OUT / "task4_brush_validation_summary.png")
    print(f"Composite task4_brush_validation_summary.png: {final.width}×{final.height}px")


def compose_task4_discovery_summary() -> None:
    """(a)(b)(c) 上排等高；(b) 体渲染；(c)(d) XY 投影。下排 (d) 与上排等宽。"""
    vol_b = OUT / "task1_vol_t0099.png"
    brush = OUT / "task4_brush_top1.png"
    hist = OUT / "task4_hist_brush_top1.png"
    spatial = OUT / "task4_spatial_to_stats.png"
    if not all(p.exists() for p in (vol_b, brush, hist, spatial)):
        print("Skip task4_discovery_summary: missing panels")
        return

    timeline_path = STATS if STATS.exists() else ROOT / "public" / "stats" / "timeline.json"
    if not timeline_path.exists():
        print("Skip task4_discovery_summary: missing timeline.json")
        return
    timeline = json.loads(timeline_path.read_text(encoding="utf-8"))
    s99 = timeline["timesteps"][99]

    # 同类型字号统一：主标题 > 面板标题 > 角标；副标题（总/面板）同级
    typo = _COMPOSE_TYPO
    _fs = dict(
        header="inline",
        label_font_size=typo["panel_label"],
        corner_font_size=typo["panel_corner"],
        subtitle_font_size=typo["panel_sub"],
    )
    panel_content_h = 640
    vol_img = _fit_cover(
        _crop_vol_content(Image.open(vol_b).convert("RGBA"), pad_frac=0.04),
        panel_content_h,
        panel_content_h,
        zoom=1.05,
    )
    row_specs = [
        (hist, "(a)", "统计刷选 · Top 1%"),
        (vol_img, "(b)", "体渲染 (t=99)"),
        (brush, "(c)", "投影验证 · Top 1%"),
    ]
    row_panels = [
        wrap_panel(p, corner_letter=letter, label=title, content_height=panel_content_h, **_fs)
        for p, letter, title in row_specs
    ]
    card_h = max(p.height for p in row_panels)
    row_panels = [fit_panel_height(p, card_h) for p in row_panels]
    row = stitch_panels_flow(row_panels, gap=10, arrow_w=42, uniform_height=card_h)
    row_w, row_h = row.size

    d_sub = (
        f"同 (a) 全场坐标 · 右尾 zoom · 反查带在 Top 1% 内（ρ≥{s99['p99']:.2f}）"
    )
    content_w = row_w - PANEL_PAD * 2
    spatial_img = Image.open(spatial).convert("RGBA")
    scale = content_w / spatial_img.width
    spatial_scaled = spatial_img.resize(
        (content_w, max(1, int(spatial_img.height * scale))),
        Image.Resampling.LANCZOS,
    )
    d_panel = wrap_panel(
        spatial_scaled,
        corner_letter="(d)",
        label="空间→统计：filament 亮脊反查密度带",
        subtitle=d_sub,
        **_fs,
    )

    connector = flow_connector_vertical(row_w, height=48)
    gap = 10
    body_h = row_h + gap + connector.height + gap + d_panel.height
    body = Image.new("RGBA", (row_w, body_h), (*hex_to_rgb(VIZ_BG), 255))
    body.paste(row, (0, 0), row)
    y = row_h + gap
    body.paste(connector, (0, y), connector)
    body.paste(d_panel, (0, y + connector.height + gap), d_panel)

    final = compose_sheet(
        "可视化驱动发现",
        "(a) 统计刷选 → (b) 体渲染 → (c) 投影验证 → (d) 亮脊反查",
        [body],
        max_width=min(body.width, 3840),
        title_font_size=typo["main_title"],
        subtitle_font_size=typo["sheet_sub"],
        title_pad_y=typo["title_pad_y"],
        title_pad_x=typo["title_pad_x"],
        title_subtitle_gap=typo["title_subtitle_gap"],
    )
    save_pil_png(final, OUT / "task4_discovery_summary.png")
    print(f"Composite task4_discovery_summary.png: {final.width}×{final.height}px")


def compose_task2_spatial_summary() -> None:
    """(a)–(d) metric timelines + (e) ξ profile + (f) bootstrap."""
    panel_files = [OUT / f"task2_spatial_panel_{i}.png" for i in range(4)]
    if not all(p.exists() for p in panel_files):
        print("Skip task2_spatial_summary: missing split panels")
        return

    panel_titles = [
        "Moran's I（6 邻域，3D）",
        "两点相关 ξ(r=1)（XY 投影）",
        "分形维数 D（P90 亮脊掩膜）",
        "超额峰度 κ−3",
    ]
    letters = ["(a)", "(b)", "(c)", "(d)", "(e)", "(f)"]

    meta_path = OUT / "task2_spatial_wrap_meta.json"
    xi_subtitle = None
    if meta_path.exists():
        xi_subtitle = json.loads(meta_path.read_text(encoding="utf-8")).get("xi_subtitle")

    n_boot = 40
    ext_path = OUT / "validation_extended.json"
    if ext_path.exists():
        n_boot = json.loads(ext_path.read_text(encoding="utf-8")).get("bootstrapSpatial", {}).get("nBootstrap", 40)

    _fs = dict(header="inline", label_font_size=34, corner_font_size=32, subtitle_font_size=22)

    def _wrap(path: Path, letter: str, title: str, *, subtitle: str | None = None, height: int) -> Image.Image:
        return wrap_panel(
            path,
            corner_letter=letter,
            label=title,
            subtitle=subtitle,
            content_height=height,
            **_fs,
        )

    row1 = stitch_panels_png(
        [
            _wrap(panel_files[0], letters[0], panel_titles[0], height=660),
            _wrap(panel_files[1], letters[1], panel_titles[1], height=660),
        ],
        direction="horizontal",
        gap=14,
        max_width=4800,
    )
    row2 = stitch_panels_png(
        [
            _wrap(panel_files[2], letters[2], panel_titles[2], height=660),
            _wrap(panel_files[3], letters[3], panel_titles[3], height=660),
        ],
        direction="horizontal",
        gap=14,
        max_width=4800,
    )
    extras: list[Image.Image] = []
    xi = OUT / "task2_two_point_xi.png"
    boot = OUT / "task2_bootstrap_ci.png"
    if xi.exists():
        extras.append(
            _wrap(
                xi,
                letters[4],
                "XY 最大密度投影：ξ(r) 与 64³ 子块 Monte Carlo 误差带",
                subtitle=xi_subtitle,
                height=620,
            )
        )
    if boot.exists():
        extras.append(
            _wrap(
                boot,
                letters[5],
                f"空间统计 bootstrap 波动（n={n_boot} 子窗口）",
                height=520,
            )
        )
    rows = [row1, row2] + extras
    body = stitch_panels_png(rows, direction="vertical", gap=12, max_width=4800)
    final = compose_sheet(
        "空间统计汇总",
        "(a)–(d) 时序四指标 · (e) ξ 剖面 r≤32 · (f) bootstrap ±1σ",
        [body],
        max_width=min(body.width, 3840),
        title_font_size=48,
        subtitle_font_size=28,
        title_pad_y=24,
        title_pad_x=32,
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
    _fs = dict(header="inline", label_font_size=30, corner_font_size=28)
    panels = [
        wrap_panel(p, label=lab, corner_letter=letter, accent=acc, content_height=580, **_fs)
        for p, lab, letter, acc in zip(paths, labels, letters, accents)
    ]
    row = stitch_panels_png(panels, direction="horizontal", gap=14, max_width=4800)
    save_pil_png(row, OUT / "task4_brush_triptych_row.png")
    final = compose_sheet(
        "相空间联动：Top 1% 高密度尾 → 宇宙网节点",
        "(a) log 直方图 · (b) 体渲染 · (c) XY 投影",
        [row],
        max_width=row.width,
        title_font_size=40,
        subtitle_font_size=24,
        title_pad_y=22,
    )
    save_pil_png(final, OUT / "task4_brush_triptych.png")
    print(f"Triptych (PIL): {OUT / 'task4_brush_triptych.png'} ({final.width}×{final.height}px)")


def _ratio_label(v0: float, v99: float) -> str:
    if abs(v0) < 1e-12:
        return "—"
    return f"+{(v99 - v0) / v0 * 100:.1f}%"


_TASK4_BRUSH_ROWS_COMPOSE = dict(
    main_title=32,
    sheet_sub=18,
    panel_label=24,
    panel_corner=22,
    panel_sub=17,
    kpi_title=20,
    kpi_body=16,
    title_subtitle_gap=12,
    title_pad_y=20,
    title_pad_x=32,
)
_TASK4_BRUSH_ROWS_COL_W = [1180, 600, 600]
_TASK4_BRUSH_ROWS_GAP = 12
_TASK4_BRUSH_ROWS_HIST_H = 432
_TASK4_BRUSH_ROWS_MID_GAP = 10
_TASK4_BRUSH_ROWS_CROP_RATIO = 0.36
_TASK4_BRUSH_ROWS_HIST_TYPO = dict(axis=14, tick=13, legend=13, annotate=12)


def _brush_rows_strip_proj_caption(img: Image.Image, *, top_ratio: float = 0.075) -> Image.Image:
    """裁掉投影图顶部 ρ 标注，避免与 panel 副标题重复。"""
    w, h = img.size
    cut = max(1, int(h * top_ratio))
    return img.crop((0, cut, w, h - cut))


def _brush_rows_proj_square(img: Image.Image, side: int) -> Image.Image:
    w, h = img.size
    scale = side / max(w, h)
    nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
    scaled = img.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (side, side), (*hex_to_rgb(PANEL_BG), 255))
    canvas.paste(scaled, ((side - nw) // 2, (side - nh) // 2), scaled)
    return canvas


def _brush_rows_hist_pil(timeline: dict, t: int, side: str) -> Image.Image:
    """Rows 专用直方图：图例/峰标注错开，不覆盖 discovery 用 PNG。"""
    edges = timeline["logBinEdges"]
    centers = np.array([np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)])
    hist = np.array(timeline["histograms"][t])
    s = timeline["timesteps"][t]
    pct = hist / (hist.sum() or 1) * 100
    typo = _TASK4_BRUSH_ROWS_HIST_TYPO

    if side == "top":
        lo, hi, color = s["p99"], s["max"], THEME["gold"]
        label = f"Top 1%: ρ≥{s['p99']:.2f}"
        threshold = s["p99"]
        x_lo, x_hi = _task4_discovery_hist_xlim(s, centers, pct)
        legend_loc, legend_anchor = "upper left", (0.02, 0.97)
        peak_xytext = (52, -28)
        peak_ha = "left"
    else:
        lo, hi, color = s["min"], s["p01"], THEME["cyan"]
        label = f"Bottom 1%: ρ≤{s['p01']:.2f}"
        threshold = s["p01"]
        x_lo = float(s["min"]) * 0.988
        x_hi = float(s["p50"]) * 1.015
        legend_loc, legend_anchor = "upper left", (0.02, 0.97)
        peak_xytext = (-72, 10)
        peak_ha = "right"
        peak_va = "center"

    fig, ax = plt.subplots(figsize=(10.6, 3.12), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)
    _draw_task4_pct_hist(
        ax,
        centers,
        pct,
        brush_lo=lo,
        brush_hi=hi,
        brush_color=color,
        brush_label=label,
        threshold_line=threshold,
        x_lo=x_lo,
        x_hi=x_hi,
        base_label="全场 128³ 体素",
        peak_annotate=True,
        peak_annotate_xytext=peak_xytext,
        peak_annotate_ha=peak_ha,
        peak_annotate_va=peak_va if side != "top" else "bottom",
        legend_loc=legend_loc,
        legend_anchor=legend_anchor,
        legend_fontsize=typo["legend"],
        annotate_fontsize=typo["annotate"],
    )
    ax.set_xlabel("密度 ρ (log)", fontsize=typo["axis"], color=THEME["muted"], labelpad=7)
    ax.set_ylabel("全场体素占比 %", fontsize=typo["axis"], color=THEME["muted"], labelpad=7)
    fig.subplots_adjust(top=0.92, bottom=0.20, left=0.11, right=0.98)
    return _mpl_figure_to_pil(fig)


def _brush_rows_row_divider(width: int) -> Image.Image:
    h = 10
    img = Image.new("RGBA", (width, h), (*hex_to_rgb(VIZ_BG), 255))
    draw = ImageDraw.Draw(img)
    draw.line([(56, h // 2), (width - 56, h // 2)], fill=(120, 220, 255, 85), width=2)
    return img


def _stitch_brush_row_top(panels: list[Image.Image], col_w: list[int], gap: int) -> Image.Image:
    """多列顶对齐拼接。"""
    row_h = max(p.height for p in panels)
    total_w = sum(col_w) + gap * (len(col_w) - 1)
    canvas = Image.new("RGBA", (total_w, row_h), (*hex_to_rgb(VIZ_BG), 255))
    x = 0
    for panel, w in zip(panels, col_w):
        px = x + max(0, (w - panel.width) // 2)
        canvas.paste(panel.convert("RGBA"), (px, 0), panel.convert("RGBA"))
        x += w + gap
    return canvas


def _overlay_brush_row_zoom_links(
    row: Image.Image,
    *,
    col_w: list[int],
    gap: int,
    proj: Image.Image,
    mid_stack: Image.Image,
    mid_stack_orig: Image.Image,
    inset_orig: Image.Image,
    inset: Image.Image,
    crop_rect: tuple[int, int, int, int],
    proj_sub: str,
    accent: str,
    ctypo: dict,
    proj_letter: str,
) -> Image.Image:
    """在 (b)→(d) / (f)→(h) 间绘制框选区域与连接线。"""
    row = row.convert("RGBA")
    draw = ImageDraw.Draw(row)

    x_mid = col_w[0] + gap
    x_inset = col_w[0] + gap + col_w[1] + gap
    mid_fitted = mid_stack
    inset_fitted = inset
    mid_slot_x = x_mid + max(0, (col_w[1] - mid_fitted.width) // 2)
    inset_slot_x = x_inset + max(0, (col_w[2] - inset_fitted.width) // 2)
    proj_paste_x = max(0, (mid_fitted.width - mid_stack_orig.width) // 2)
    inset_paste_x = max(0, (inset_fitted.width - inset_orig.width) // 2)
    proj_x = mid_slot_x + proj_paste_x + max(0, (mid_stack_orig.width - proj.width) // 2)
    inset_x = inset_slot_x + inset_paste_x

    hdr_proj = estimate_inline_header_h(
        "XY 投影",
        proj_sub,
        corner_font_size=ctypo["panel_corner"],
        label_font_size=ctypo["panel_label"],
        subtitle_font_size=ctypo["panel_sub"],
    )
    hdr_inset = estimate_inline_header_h(
        "局部放大",
        f"↔ {proj_letter} 框选区域",
        corner_font_size=ctypo["panel_corner"],
        label_font_size=ctypo["panel_label"],
        subtitle_font_size=ctypo["panel_sub"],
    )
    cx = proj_x + PANEL_PAD
    cy = PANEL_PAD + hdr_proj
    x1, y1, x2, y2 = crop_rect
    src_box = (cx + x1, cy + y1, cx + x2, cy + y2)

    ix = inset_x + PANEL_PAD
    iy = PANEL_PAD + hdr_inset
    inset_cw = inset_orig.width - 2 * PANEL_PAD
    inset_ch = inset_orig.height - 2 * PANEL_PAD - hdr_inset
    dst_box = (ix, iy, ix + inset_cw, iy + inset_ch)

    draw_zoom_connector_lines(draw, src_box, dst_box, accent)
    return row


def _build_brush_row(
    *,
    letters: tuple[str, str, str, str],
    hist_img: Image.Image,
    proj_path: Path,
    accent: str,
    row_title: str,
    bullets: list[str],
    hist_sub: str,
    proj_sub: str,
    ctypo: dict,
    _fs: dict,
) -> Image.Image:
    """三列布局：直方图 | XY 投影 + KPI 叠放 | 局部放大。"""
    hist_h = _TASK4_BRUSH_ROWS_HIST_H
    col_w = _TASK4_BRUSH_ROWS_COL_W
    inner_w = [w - PANEL_PAD * 2 for w in col_w]

    hist_raw = fit_panel_contain(hist_img, inner_w[0], hist_h)
    hist = wrap_panel(
        hist_raw,
        corner_letter=letters[0],
        label="直方图刷选",
        subtitle=hist_sub,
        accent=accent,
        **_fs,
    )
    kpi_inner = render_kpi_card(
        row_title,
        bullets,
        accent,
        width=inner_w[1],
        border=False,
        layout="grid",
        title_font_size=ctypo["kpi_title"],
        body_font_size=ctypo["kpi_body"],
        pad_x=12,
        pad_y=8,
    )
    kpi = wrap_panel(
        kpi_inner,
        corner_letter=letters[2],
        label="结构 KPI",
        subtitle="体积·质量·空间",
        accent=accent,
        **_fs,
    )
    # 投影高度自适应：使 (b)+(c) 叠放后与 (a) 等高
    _proj_header_est = ctypo["panel_corner"] + ctypo["panel_label"] + ctypo["panel_sub"] + 36
    proj_h = max(
        280,
        hist.height - kpi.height - _TASK4_BRUSH_ROWS_MID_GAP - _proj_header_est - PANEL_PAD * 2,
    )
    proj_h = min(proj_h, _TASK4_BRUSH_ROWS_HIST_H - 40)
    proj_raw = _brush_rows_proj_square(
        _brush_rows_strip_proj_caption(Image.open(proj_path).convert("RGBA")),
        int(proj_h),
    )
    crop_rect = center_crop_box(proj_raw.width, proj_raw.height, _TASK4_BRUSH_ROWS_CROP_RATIO)
    proj_marked = draw_zoom_crop_marker(proj_raw, crop_rect, accent)
    proj = wrap_panel(
        proj_marked,
        corner_letter=letters[1],
        label="XY 投影",
        subtitle=proj_sub,
        accent=accent,
        **_fs,
    )
    crop_img = proj_raw.crop(crop_rect)
    inset = wrap_panel(
        crop_img,
        corner_letter=letters[3],
        label="局部放大",
        subtitle=f"↔ {letters[1]} 框选区域",
        accent=accent,
        content_height=hist_h,
        header="inline",
        label_font_size=ctypo["panel_label"],
        subtitle_font_size=ctypo["panel_sub"],
        corner_font_size=ctypo["panel_corner"],
    )

    mid_stack = stitch_panels_png(
        [proj, kpi],
        direction="vertical",
        gap=_TASK4_BRUSH_ROWS_MID_GAP,
        max_width=col_w[1],
        draw_dividers=False,
    )

    row_h = max(hist.height, mid_stack.height, inset.height)
    panels = [
        fit_panel_contain(hist, col_w[0], row_h),
        fit_panel_contain(mid_stack, col_w[1], row_h, valign="top"),
        fit_panel_contain(inset, col_w[2], row_h),
    ]
    row = _stitch_brush_row_top(panels, col_w, _TASK4_BRUSH_ROWS_GAP)
    return _overlay_brush_row_zoom_links(
        row,
        col_w=col_w,
        gap=_TASK4_BRUSH_ROWS_GAP,
        proj=proj,
        mid_stack=panels[1],
        mid_stack_orig=mid_stack,
        inset_orig=inset,
        inset=panels[2],
        crop_rect=crop_rect,
        proj_sub=proj_sub,
        accent=accent,
        ctypo=ctypo,
        proj_letter=letters[1],
    )


def task4_brush_rows(timeline: dict) -> None:
    """Top/Bottom 1% 双行：直方图 | 投影+KPI 叠放 | 局部放大（PIL，与图9 互补）。"""
    s99 = timeline["timesteps"][99]
    bottom_proj = OUT / "task4_brush_bottom_proj.png"
    if not bottom_proj.exists():
        print("Skip task4_brush_rows: missing task4_brush_bottom_proj.png", file=sys.stderr)
        return

    ctypo = _TASK4_BRUSH_ROWS_COMPOSE
    _fs = dict(
        header="inline",
        label_font_size=ctypo["panel_label"],
        corner_font_size=ctypo["panel_corner"],
        subtitle_font_size=ctypo["panel_sub"],
    )

    row_top = _build_brush_row(
        letters=("(a)", "(b)", "(c)", "(d)"),
        hist_img=_brush_rows_hist_pil(timeline, 99, "top"),
        proj_path=OUT / "task4_brush_top1.png",
        accent=THEME["gold"],
        row_title="Top 1% 高密度尾 → 宇宙网节点",
        bullets=[
            f"ρ ≥ p99 = {s99['p99']:.2f}",
            f"体积占比 {s99['tailMassAboveP99'] * 100:.2f}%",
            f"质量占比 {s99.get('massFractionAboveP99', 0) * 100:.1f}%",
            "空间：丝状节点聚集",
        ],
        hist_sub="t=99 · 主联动见任务二图9",
        proj_sub=f"刷选高亮 · ρ ≥ {s99['p99']:.2f}",
        ctypo=ctypo,
        _fs=_fs,
    )
    row_bot = _build_brush_row(
        letters=("(e)", "(f)", "(g)", "(h)"),
        hist_img=_brush_rows_hist_pil(timeline, 99, "bottom"),
        proj_path=bottom_proj,
        accent=THEME["cyan"],
        row_title="Bottom 1% 低密度 → IGM 空洞",
        bullets=[
            f"ρ ≤ p01 = {s99['p01']:.2f}",
            f"体积占比 {s99['tailMassBelowP01'] * 100:.2f}%",
            f"质量占比 {s99.get('massFractionBelowP01', 0) * 100:.1f}%",
            "空间：弥散空洞背景",
        ],
        hist_sub="t=99 · 与 Top 1% 密度尾对照",
        proj_sub=f"刷选高亮 · ρ ≤ {s99['p01']:.2f}",
        ctypo=ctypo,
        _fs=_fs,
    )

    divider = _brush_rows_row_divider(max(row_top.width, row_bot.width))
    body = stitch_panels_png(
        [row_top, divider, row_bot],
        direction="vertical",
        gap=22,
        max_width=max(row_top.width, row_bot.width),
    )
    final = compose_sheet(
        "Top 1% / Bottom 1% 双行对比 (t=99)",
        "统计刷选 → XY 投影 + 结构 KPI → 局部放大 · Top 1% 四联见任务二图9",
        [body],
        max_width=body.width,
        title_font_size=ctypo["main_title"],
        subtitle_font_size=ctypo["sheet_sub"],
        title_pad_y=ctypo["title_pad_y"],
        title_pad_x=ctypo["title_pad_x"],
        title_subtitle_gap=ctypo["title_subtitle_gap"],
        title_align="center",
    )
    save_pil_png(final, OUT / "task4_brush_rows.png")
    print(f"Brush rows (PIL): {OUT / 'task4_brush_rows.png'} ({final.width}×{final.height}px)")


def _strip_overlay_banner(img: Image.Image, *, top_ratio: float = 0.155) -> Image.Image:
    """裁掉 matplotlib 子图顶部的 suptitle/副标题带，避免与 compose 标题重复。"""
    w, h = img.size
    cut = max(1, int(h * top_ratio))
    return img.crop((0, cut, w, h))


def _render_task3_sparkline(
    ts: list[int],
    values: list[float],
    *,
    color: str,
    title: str,
    w: int,
    h: int,
    title_fontsize: int = 11,
    tick_fontsize: int = 10,
) -> Image.Image:
    """Task3 右侧迷你趋势图：字号对齐 _TASK4_CHART_TYPO，刻度减半。"""
    fig, ax = plt.subplots(figsize=(w / 100, h / 100), facecolor=VIZ_BG)
    ax.set_facecolor(PANEL_BG)
    ax.fill_between(ts, values, alpha=0.15, color=color)
    ax.plot(ts, values, color=color, lw=LINE_WIDTH)
    ax.set_title(title, fontsize=title_fontsize, color="#e6edf3", pad=6)
    ax.set_xlim(0, 99)
    lo, hi = min(values), max(values)
    margin = max((hi - lo) * 0.18, abs(hi) * 0.02, 1e-6)
    ax.set_ylim(lo - margin, hi + margin)
    style_axes(ax, labelsize=tick_fontsize)
    set_tick_density(ax, factor=2.0, axes="xy")
    buf = io.BytesIO()
    fig.savefig(
        buf,
        format="png",
        dpi=100,
        facecolor=VIZ_BG,
        edgecolor="none",
        bbox_inches="tight",
        pad_inches=0.03,
    )
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    return img.resize((w, h), Image.Resampling.LANCZOS)


def _task3_kpi_strip(
    items: list[tuple[str, str, str]],
    *,
    total_w: int,
    label_fs: int,
    value_fs: int,
    height: int = 156,
    gap: int = 20,
    pad_x: int = 28,
) -> Image.Image:
    """底部 t=99 四 KPI 条：终态摘要，留足内边距。"""
    n = len(items)
    tile_w = max(1, (total_w - gap * (n - 1)) // n)
    canvas = Image.new("RGBA", (total_w, height), (*hex_to_rgb(VIZ_BG), 255))
    label_font = load_ui_font(label_fs)
    val_font = load_ui_font(value_fs, bold=True)
    for i, (label, val, accent) in enumerate(items):
        x0 = i * (tile_w + gap)
        bg = Image.new("RGBA", (tile_w, height), (*hex_to_rgb(PANEL_BG), 255))
        bd = ImageDraw.Draw(bg)
        bd.rounded_rectangle((0, 0, tile_w - 1, height - 1), radius=12, outline="#3a4558", width=2)
        bd.rectangle((0, 0, 5, height), fill=(*hex_to_rgb(accent), 255))
        lb = bd.textbbox((0, 0), label, font=label_font)
        vb = bd.textbbox((0, 0), val, font=val_font)
        label_h = lb[3] - lb[1]
        val_h = vb[3] - vb[1]
        block_h = label_h + 16 + val_h
        y0 = max(pad_x // 2, (height - block_h) // 2)
        bd.text(
            (pad_x, y0 - lb[1]),
            label,
            fill=(*hex_to_rgb(THEME["muted"]), 255),
            font=label_font,
        )
        bd.text(
            (pad_x, y0 + label_h + 16 - vb[1]),
            val,
            fill=(230, 237, 243, 255),
            font=val_font,
        )
        canvas.paste(bg, (x0, 0), bg)
    return canvas


def task3_story_panel(timeline: dict) -> None:
    """Section 03: overlay + sparklines + t=99 KPI — PIL 合成，覆盖 task3_story_panel.png。"""
    hist_path = OUT / "task3_hist_overlay.png"
    if not hist_path.exists():
        print("Skip task3_story_panel: missing task3_hist_overlay.png")
        return

    steps = timeline["timesteps"]
    s0, s99 = steps[0], steps[99]
    ts = [s["timestep"] for s in steps]
    std = [s["std"] for s in steps]
    span = [s["p99"] - s["p01"] for s in steps]
    tail = [s["tailMassAboveP99"] * 100 for s in steps]

    typo = _COMPOSE_TYPO
    chart = _TASK4_CHART_TYPO
    _fs = dict(
        header="inline",
        label_font_size=typo["panel_label"],
        corner_font_size=typo["panel_corner"],
        subtitle_font_size=typo["panel_sub"],
    )
    panel_content_h = 1000
    target_row_w = 3180
    spark_w = int(target_row_w * 0.34)
    spark_h = (panel_content_h - 12) // 3
    specs = [
        (std, THEME["cyan"], "σ(t)", _ratio_label(s0["std"], s99["std"])),
        (span, THEME["purple"], "p99−p01", _ratio_label(span[0], span[-1])),
        (tail, THEME["gold"], "≥p99 体积%", _ratio_label(tail[0], tail[-1])),
    ]
    sparks = [
        _render_task3_sparkline(
            ts,
            y,
            color=color,
            title=f"{title}  t=0→99  {badge}",
            w=spark_w,
            h=spark_h,
            title_fontsize=chart["annotate"],
            tick_fontsize=chart["tick"] - 2,
        )
        for y, color, title, badge in specs
    ]
    spark_col = stitch_panels_png(sparks, direction="vertical", gap=6, draw_dividers=False)

    hist_img = _strip_overlay_banner(Image.open(hist_path).convert("RGBA"))
    a_panel = wrap_panel(
        hist_img,
        corner_letter="(a)",
        label="直方图叠加 · 128 bins",
        subtitle="代表步 t=0, 25, 50, 75, 99",
        content_height=panel_content_h,
        **_fs,
    )
    b_panel = wrap_panel(
        spark_col,
        corner_letter="(b)",
        label="时序 KPI",
        subtitle=f"σ {specs[0][3]} · p99−p01 {specs[1][3]} · 尾体积 {specs[2][3]}",
        content_height=panel_content_h,
        **_fs,
    )
    card_h = max(a_panel.height, b_panel.height)
    row = stitch_panels_png(
        [fit_panel_height(a_panel, card_h), fit_panel_height(b_panel, card_h)],
        direction="horizontal",
        gap=12,
        max_width=4800,
    )
    kpi_inner = _task3_kpi_strip(
        [
            ("均值 μ", f"{s99['mean']:.3f}", THEME["purple"]),
            ("标准差 σ", f"{s99['std']:.4f}", THEME["cyan"]),
            ("p99", f"{s99['p99']:.3f}", THEME["gold"]),
            ("≥p99 体积", f"{s99['tailMassAboveP99'] * 100:.2f}%", THEME["coral"]),
        ],
        total_w=row.width - PANEL_PAD * 2,
        label_fs=typo["panel_sub"],
        value_fs=typo["panel_corner"],
        height=156,
        gap=20,
    )
    kpi_panel = wrap_panel(
        kpi_inner,
        corner_letter="(c)",
        label="t=99 关键指标",
        subtitle="终态摘要：与 (b) 时序曲线终点一致，供正文 KPI 引用",
        header="inline",
        label_font_size=typo["panel_label"],
        corner_font_size=typo["panel_corner"],
        subtitle_font_size=typo["panel_sub"],
    )
    if kpi_panel.width < row.width:
        kpi_panel = fit_panel_width(kpi_panel, row.width)
    body = stitch_panels_png([row, kpi_panel], direction="vertical", gap=20, max_width=4800)
    final = compose_sheet(
        "03 · 定量：密度两极化",
        "直方图叠加 → 时序 KPI · 右栏为演化趋势，底栏为 t=99 终态数值",
        [body],
        direction="vertical",
        max_width=min(body.width, 3840),
        title_font_size=typo["main_title"],
        subtitle_font_size=typo["sheet_sub"],
        title_pad_y=typo["title_pad_y"],
        title_pad_x=typo["title_pad_x"],
        title_subtitle_gap=typo["title_subtitle_gap"],
    )
    save_pil_png(final, OUT / "task3_story_panel.png")
    print(f"Story panel (PIL): {OUT / 'task3_story_panel.png'} ({final.width}×{final.height}px)")


def task1_hero_poster(timeline: dict) -> None:
    """Section 01: hero volume + vertical colorbar + metadata strip (PIL)."""
    vmin, vmax = global_projection_domain(timeline)
    hero_path = resolve_vol_image(99, timeline)
    s99 = timeline["timesteps"][99]

    meta = render_meta_badges(
        ["128³", "100 步", "t=0…99", "气体密度 ρ", "Nyx 模拟"],
        width=280,
        font_size=30,
        badge_h=78,
        gap=14,
    )
    hero = wrap_panel(
        hero_path,
        label="宇宙网诞生 (t=99)",
        subtitle=f"σ={s99['std']:.3f}",
        accent=THEME["cyan"],
        content_height=640,
        label_font_size=42,
        subtitle_font_size=30,
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


NARR_CANVAS_W = 3840
NARR_CANVAS_H = 5200
NARR_MARGIN = 64
NARR_INNER_GAP = 24
NARR_SECTION_GAP = 24
NARR_DIVIDER_H = 2
NARR_HEADER_H = 128
NARR_PANEL_BG = "#0c1322"
NARR_BORDER = "#243048"
NARR_ACT_HEAD_H = 156
NARR_FINDINGS_CARD_GAP = 20
NARR_FINDINGS_FOOTER_H = 36
NARR_FINDINGS_BODY_MIN = 580
NARR_FINDINGS_MIN_H = NARR_ACT_HEAD_H + NARR_FINDINGS_BODY_MIN + NARR_FINDINGS_FOOTER_H
NARR_FIG_ZOOM = 1.0
NARR_ACT1_FIG_SCALE = 0.92  # 第 1 幕体渲染条带略缩小，避免占满幕高

# 与 sceneRegistry / 03-叙事逻辑 对齐：每幕一张文档配图，禁止重复拼贴
NARR_DOC_SECTIONS: list[tuple[int, str, str, tuple[str, ...]]] = [
    (1, "看见宇宙结构", "task1-morph", ("task1_vol_strip.png",)),
    (2, "量化演化", "task3-hist", ("task3_story_panel.png", "task3_hist_overlay.png")),
    (3, "空间验证", "task4-validate", ("task4_discovery_summary.png", "task4_brush_rows.png")),
]
NARR_LABEL_H = 118
NARR_KPI_LINE_H = 44

BRUSH_STATS = ROOT / "public" / "stats" / "brush_validation.json"
VOXEL_COUNT = GRID**3


def _story_kpis(timeline: dict) -> dict:
    s0, s99 = timeline["timesteps"][0], timeline["timesteps"][99]
    span0, span99 = s0["p99"] - s0["p01"], s99["p99"] - s99["p01"]
    return {
        "s0": s0,
        "s99": s99,
        "sigma_pct": (s99["std"] - s0["std"]) / s0["std"] * 100,
        "span_pct": (span99 - span0) / span0 * 100,
        "tail_vol": s99["tailMassAboveP99"] * 100,
        "tail_mass": (s99.get("massFractionAboveP99") or 0) * 100,
        "void_vol": s99["tailMassBelowP01"] * 100,
    }


def _load_brush_validation() -> dict:
    path = BRUSH_STATS if BRUSH_STATS.exists() else OUT / "brush_validation.json"
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _narr_threshold_kpi(validation: dict, needle: str) -> tuple[str, float, float]:
    for row in validation.get("thresholds", []):
        if needle in row.get("label", ""):
            return row["label"], row["volumePct"], row["massPct"]
    return needle, 0.0, 0.0


def _narr_inner_w(width: int) -> int:
    return width - NARR_MARGIN * 2


def _narr_image_box(img: Image.Image, box_w: int, box_h: int, *, zoom: float = 1.02) -> Image.Image:
    """裁切填充到固定宽高，保证同行/同列图像尺寸一致。"""
    raw = _trim_image_margins(img.convert("RGBA"), pad=4)
    return _fit_cover(raw, box_w, box_h, zoom=zoom)


def _narr_section_divider(width: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, NARR_DIVIDER_H), (*hex_to_rgb(VIZ_BG), 255))
    draw = ImageDraw.Draw(canvas)
    draw.line(
        [(NARR_MARGIN, 1), (width - NARR_MARGIN, 1)],
        fill=hex_to_rgb(NARR_BORDER),
        width=2,
    )
    return canvas


def _narr_poster_header(width: int) -> Image.Image:
    canvas = Image.new("RGBA", (width, NARR_HEADER_H), (*hex_to_rgb(VIZ_BG), 255))
    draw = ImageDraw.Draw(canvas)
    title_font = load_ui_font(64, bold=True)
    title = "NyxViz 交互可视化系统"
    tw = draw.textlength(title, font=title_font)
    ty = max(20, (NARR_HEADER_H - 64) // 2)
    draw.text(((width - tw) / 2, ty), title, fill=(245, 249, 255), font=title_font)
    draw.line(
        [(NARR_MARGIN, NARR_HEADER_H - 8), (width - NARR_MARGIN, NARR_HEADER_H - 8)],
        fill=hex_to_rgb(NARR_BORDER),
        width=1,
    )
    return canvas


def _narr_content_mask(rgb: np.ndarray) -> np.ndarray:
    """叙事配图：面板边框、文字、曲线等非背景像素。"""
    r = rgb[:, :, 0].astype(np.int16)
    g = rgb[:, :, 1].astype(np.int16)
    b = rgb[:, :, 2].astype(np.int16)
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    sat = mx - mn
    lum = (r + g + b) // 3
    bg_like = (r < 38) & (g < 42) & (b < 65)
    return (~bg_like) | (sat > 10) | (lum > 72)


def _strip_compose_sheet_banner(img: Image.Image) -> Image.Image:
    """去掉 compose_sheet 顶栏标题（与幕标题重复，占垂直空间）。"""
    rgb = np.array(img.convert("RGB"))
    h, w = rgb.shape[:2]
    bg = np.array(hex_to_rgb(VIZ_BG), dtype=np.int16)
    diff = np.abs(rgb.astype(np.int16) - bg).max(axis=2)
    scan_limit = min(h // 2, 420)
    for y in range(24, scan_limit):
        row = diff[y]
        xs = np.where(row > 14)[0]
        if len(xs) >= int(w * 0.52):
            y0 = max(0, y - 6)
            return img.crop((0, y0, w, h))
    return img


def _trim_narr_figure_content(img: Image.Image, *, pad: int = 10) -> Image.Image:
    """裁掉 sheet 标题、外缘空白，仅保留面板主体。"""
    raw = _trim_image_margins(img.convert("RGBA"), pad=4)
    raw = _strip_compose_sheet_banner(raw)
    rgb = np.array(raw.convert("RGB"))
    mask = _narr_content_mask(rgb)
    if not mask.any():
        return raw
    ys, xs = np.where(mask)
    x0 = max(0, int(xs.min()) - pad)
    y0 = max(0, int(ys.min()) - pad)
    x1 = min(raw.width, int(xs.max()) + pad + 1)
    y1 = min(raw.height, int(ys.max()) + pad + 1)
    cropped = raw.crop((x0, y0, x1, y1))
    # 去掉内容 bbox 内上下近背景空行
    bg = np.array(hex_to_rgb(VIZ_BG), dtype=np.int16)
    diff = np.abs(np.array(cropped.convert("RGB")).astype(np.int16) - bg).max(axis=2)
    top, bottom = 0, cropped.height
    while top < bottom and (diff[top] > 12).mean() < 0.04:
        top += 1
    while bottom > top and (diff[bottom - 1] > 12).mean() < 0.04:
        bottom -= 1
    if bottom - top < 32:
        return cropped
    return cropped.crop((0, top, cropped.width, bottom))


def _fit_cover_narr(img: Image.Image, tw: int, th: int, *, zoom: float = 1.0) -> Image.Image:
    """cover 填充；纵向顶对齐保留面板主体，避免底部暗边留白。"""
    iw, ih = img.size
    scale = max(tw / iw, th / ih) * zoom
    sw, sh = max(1, int(iw * scale)), max(1, int(ih * scale))
    scaled = img.resize((sw, sh), Image.Resampling.LANCZOS)
    rgb = np.array(scaled.convert("RGB"))
    content = _narr_content_mask(rgb)
    if content.any():
        ys, _xs = np.where(content)
        y_min = int(ys.min())
        top = max(0, min(y_min - 4, sh - th))
    else:
        top = max(0, (sh - th) // 2)
    left = max(0, (sw - tw) // 2)
    return scaled.crop((left, top, left + tw, top + th))


def _narr_act_heading(act_num: int, title: str, width: int) -> Image.Image:
    """统一「第 N 幕 · 标题」+ 左侧 accent 条（无录屏副标题）。"""
    h = NARR_ACT_HEAD_H
    canvas = Image.new("RGBA", (width, h), (*hex_to_rgb(VIZ_BG), 255))
    draw = ImageDraw.Draw(canvas)
    inner_x = NARR_MARGIN
    accent = hex_to_rgb(THEME["cyan"])
    pad_top, pad_bottom = 14, 18
    draw.rounded_rectangle(
        [inner_x, pad_top + 4, inner_x + 10, h - pad_bottom - 4],
        radius=3,
        fill=accent,
    )
    num_font = load_ui_font(40, bold=True)
    title_font = load_ui_font(64, bold=True)
    tx = inner_x + 28
    num_y = pad_top
    num_bbox = draw.textbbox((tx, num_y), f"第 {act_num} 幕", font=num_font)
    title_y = num_bbox[3] + 6
    draw.text((tx, num_y), f"第 {act_num} 幕", fill=hex_to_rgb(THEME["gold"]), font=num_font)
    draw.text((tx, title_y), title, fill=(245, 249, 255), font=title_font)
    return canvas




def _resolve_narr_figure(candidates: tuple[str, ...]) -> Path:
    for name in candidates:
        path = OUT / name
        if path.is_file():
            return path
    raise FileNotFoundError(f"Missing narrative figure (tried {candidates})")


def _natural_figure_body_h(path: Path, canvas_w: int) -> int:
    """裁切 sheet 标题后，配图按内容区全宽缩放的自然高度。"""
    inner_w = _narr_inner_w(canvas_w)
    img = _trim_narr_figure_content(Image.open(path).convert("RGBA"))
    return max(1, int(img.height * inner_w / max(1, img.width)))


def _narr_compute_canvas_width(act_heights: tuple[int, int, int]) -> int:
    """按前三幕配图在分配高度下的满宽显示，反推画布宽度（消除左右留白）。"""
    head = NARR_ACT_HEAD_H
    inner_candidates: list[int] = []
    for (_, _, _, figs), act_h in zip(NARR_DOC_SECTIONS, act_heights, strict=True):
        img = _trim_narr_figure_content(Image.open(_resolve_narr_figure(figs)).convert("RGBA"))
        body_h = max(1, act_h - head)
        inner_candidates.append(max(1, int(body_h * img.width / max(1, img.height))))
    inner_w = min(inner_candidates)
    return inner_w + NARR_MARGIN * 2


def _narr_compute_act_heights(canvas_w: int) -> tuple[int, int, int, int]:
    """按配图自然宽高比分配幕高；超出预算时等比缩小，contain 不裁切。"""
    gaps = 3 * (NARR_SECTION_GAP + NARR_DIVIDER_H)
    budget = NARR_CANVAS_H - NARR_HEADER_H - gaps
    head = NARR_ACT_HEAD_H
    bodies = [
        _natural_figure_body_h(_resolve_narr_figure(figs), canvas_w)
        for *_, figs in NARR_DOC_SECTIONS
    ]
    h4 = NARR_FINDINGS_MIN_H
    fig_budget = budget - h4
    natural_acts = [head + b for b in bodies]
    natural_sum = sum(natural_acts)
    if natural_sum <= fig_budget:
        raw_figs = list(natural_acts)
        raw_figs[2] += fig_budget - natural_sum
    else:
        body_budget = fig_budget - head * 3
        bsum = sum(bodies) or 1
        raw_figs = [head + max(100, int(b * body_budget / bsum)) for b in bodies]
    return raw_figs[0], raw_figs[1], raw_figs[2], h4


def _narr_section_figure(
    path: Path, width: int, height: int, *, fig_scale: float = 1.0
) -> Image.Image:
    """配图 contain 完整显示，不 cover 裁切。fig_scale<1 时缩小并居中。"""
    inner_w = _narr_inner_w(width)
    img = _trim_narr_figure_content(Image.open(path).convert("RGBA"))
    scale = max(0.5, min(1.0, fig_scale))
    fit_w = max(1, int(inner_w * scale))
    fit_h = max(1, int(height * scale))
    filled = fit_panel_contain(img, fit_w, fit_h, valign="top", allow_upscale=False)
    canvas = Image.new("RGBA", (width, height), (*hex_to_rgb(VIZ_BG), 255))
    paste_x = NARR_MARGIN + max(0, (inner_w - filled.width) // 2)
    canvas.paste(filled, (paste_x, 0), filled)
    return canvas


def _build_doc_figure_act(
    act_num: int,
    title: str,
    scene_tag: str,
    figure_candidates: tuple[str, ...],
    width: int,
    height: int,
    *,
    fig_scale: float = 1.0,
) -> Image.Image:
    heading = _narr_act_heading(act_num, title, width)
    fig_path = _resolve_narr_figure(figure_candidates)
    body_h = max(1, height - heading.height)
    body = _narr_section_figure(fig_path, width, body_h, fig_scale=fig_scale)
    canvas = Image.new("RGBA", (width, height), (*hex_to_rgb(VIZ_BG), 255))
    canvas.paste(heading, (0, 0), heading)
    canvas.paste(body, (0, heading.height), body)
    return canvas


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
    num: str,
    title: str,
    primary: str,
    secondary: str,
) -> None:
    ref_w, ref_h = 540, 168
    scale = max(0.85, min(min(w / ref_w, h / ref_h), 2.8))

    border = hex_to_rgb(THEME["cyan"])
    gold = hex_to_rgb(THEME["gold"])
    top_rgb = hex_to_rgb("#1e3a5c")
    bot_rgb = hex_to_rgb("#0f1e34")
    for iy in range(h):
        t = iy / max(1, h - 1)
        fill = tuple(int(top_rgb[c] * (1 - t) + bot_rgb[c] * t) for c in range(3))
        draw.line([(x + 2, y + iy), (x + w - 2, y + iy)], fill=fill)
    radius = max(8, int(12 * scale))
    draw.rounded_rectangle([x, y, x + w, y + h], radius=radius, outline=border, width=2)
    inset = max(8, int(12 * scale))
    draw.rounded_rectangle(
        [x + inset, y + inset, x + w - inset, y + h - inset],
        radius=max(6, int(8 * scale)),
        outline=(*hex_to_rgb(THEME["cyan"]), 48),
        width=1,
    )

    head_h = max(32, int(40 * scale))
    num_font = load_ui_font(max(18, int(22 * scale)), bold=True)
    title_font = load_ui_font(max(16, int(20 * scale)), bold=True)
    primary_font = load_ui_font(max(24, int(36 * scale)), bold=True)
    sub_font = load_ui_font(max(14, int(18 * scale)))
    num_gap = max(36, int(52 * scale))
    draw.text((x + inset, y + inset), num, fill=gold, font=num_font)
    draw.text((x + inset + num_gap, y + inset + 2), title, fill=(245, 249, 255), font=title_font)

    content_top = y + head_h
    content_h = h - head_h - inset
    primary_h = primary_font.size + max(6, int(8 * scale))
    sub_h = sub_font.size + max(4, int(6 * scale))
    block_h = primary_h + sub_h + max(8, int(10 * scale))
    block_y = content_top + max(0, (content_h - block_h) // 2)
    pw = draw.textlength(primary, font=primary_font)
    draw.text((x + (w - pw) / 2, block_y), primary, fill=gold, font=primary_font)
    sw = draw.textlength(secondary, font=sub_font)
    draw.text(
        (x + (w - sw) / 2, block_y + primary_h + max(4, int(6 * scale))),
        secondary,
        fill=(240, 246, 255),
        font=sub_font,
    )


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
    print(f"Narrative poster: {canvas_w}×{NARR_CANVAS_H}px → task6_story_poster.png")

def _render_findings_card(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    num: str,
    title: str,
    detail: str,
) -> None:
    bg = hex_to_rgb("#121e38")
    cyan = hex_to_rgb(THEME["cyan"])
    gold = hex_to_rgb(THEME["gold"])
    draw.rounded_rectangle([x, y, x + w, y + h], radius=16, fill=bg, outline=cyan, width=2)
    num_font = load_ui_font(42, bold=True)
    title_font = load_ui_font(34, bold=True)
    body_font = load_ui_font(28)
    draw.text((x + 20, y + 20), num, fill=gold, font=num_font)
    draw.text((x + 76, y + 22), title, fill=(245, 249, 255), font=title_font)
    # wrap detail
    max_w = w - 40
    word_list = detail.replace("·", " · ").split()
    line, ly = "", y + 82
    for word in word_list:
        trial = (line + " " + word).strip()
        if draw.textlength(trial, font=body_font) > max_w and line:
            draw.text((x + 20, ly), line, fill=hex_to_rgb(THEME["muted"]), font=body_font)
            ly += 36
            line = word
        else:
            line = trial
    if line:
        draw.text((x + 20, ly), line, fill=hex_to_rgb(THEME["muted"]), font=body_font)


def _build_findings_panel(timeline: dict, width: int, height: int) -> Image.Image:
    k = _story_kpis(timeline)
    canvas = Image.new("RGBA", (width, height), (*hex_to_rgb(VIZ_BG), 255))
    draw = ImageDraw.Draw(canvas)

    header = render_text_banner(
        [
            "关键科学发现 · t=99",
            f"σ +{k['sigma_pct']:.1f}% · p99−p01 +{k['span_pct']:.1f}% · ≥p99 体积 {k['tail_vol']:.2f}%",
        ],
        width,
        bg=VIZ_BG,
        align="center",
        pad_y=24,
        title_font_size=44,
        subtitle_font_size=26,
    )
    canvas.paste(header, (0, 0), header)

    cards = [
        ("01", "引力驱动团块化", f"σ +{k['sigma_pct']:.1f}% · p99−p01 +{k['span_pct']:.1f}%"),
        ("02", "密度分布两极化", f"低密度 void ≤p01 体积 {k['void_vol']:.1f}% · 右尾增厚"),
        ("03", "少数致密承载结构", f"≥p99 体积 {k['tail_vol']:.2f}% · 质量 {k['tail_mass']:.1f}%"),
        ("04", "统计—空间可验证", "Top 1% 刷选召回 100% · 早停 ~37ms"),
    ]
    pad_x, pad_y = 48, header.height + 20
    gap = 24
    card_w = (width - pad_x * 2 - gap) // 2
    card_h = (height - pad_y - pad_x - gap) // 2
    positions = [
        (pad_x, pad_y),
        (pad_x + card_w + gap, pad_y),
        (pad_x, pad_y + card_h + gap),
        (pad_x + card_w + gap, pad_y + card_h + gap),
    ]
    for (num, title, detail), (cx, cy) in zip(cards, positions, strict=True):
        _render_findings_card(draw, cx, cy, card_w, card_h, num, title, detail)
    return canvas


def _build_closing_panel(timeline: dict, width: int, height: int) -> Image.Image:
    k = _story_kpis(timeline)
    canvas = Image.new("RGBA", (width, height), (*hex_to_rgb(VIZ_BG), 255))

    header = render_text_banner(
        ["从 Nyx 数据到宇宙结构认知", "研究闭环 · Web 三栏可视分析"],
        width,
        bg=VIZ_BG,
        align="center",
        pad_y=20,
        title_font_size=40,
        subtitle_font_size=24,
    )
    canvas.paste(header, (0, 0), header)

    steps = [
        "Nyx 数据",
        "体渲染观察",
        "时序统计",
        "密度区间刷选",
        "空间映射",
        "验证分析",
        "科学发现",
    ]
    flow_top = header.height + 16
    flow_h = min(720, height - flow_top - 280)
    flow_img = _render_horizontal_flow_strip(width - 96, flow_h, steps)
    fx = (width - flow_img.width) // 2
    canvas.paste(flow_img, (fx, flow_top), flow_img)

    quote = (
        "从微小涨落到宇宙网，可视化让隐藏在千万个数据单元中的宇宙结构显现。"
    )
    quote_font = load_ui_font(34)
    draw = ImageDraw.Draw(canvas)
    qy = flow_top + flow_h + 28
    max_qw = width - 160
    line, ly = "", qy
    for ch in quote:
        trial = line + ch
        if draw.textlength(trial, font=quote_font) > max_qw and line:
            tw = draw.textlength(line, font=quote_font)
            draw.text(((width - tw) / 2, ly), line, fill=(232, 240, 255), font=quote_font)
            ly += 44
            line = ch
        else:
            line = trial
    if line:
        tw = draw.textlength(line, font=quote_font)
        draw.text(((width - tw) / 2, ly), line, fill=(232, 240, 255), font=quote_font)

    foot = (
        f"σ +{k['sigma_pct']:.1f}%  ·  p99−p01 +{k['span_pct']:.1f}%  ·  "
        "刷选召回 100%  ·  NyxViz /video.html?record=1"
    )
    foot_font = load_ui_font(22)
    fw = draw.textlength(foot, font=foot_font)
    draw.text(
        ((width - fw) / 2, height - 52),
        foot,
        fill=hex_to_rgb(THEME["muted"]),
        font=foot_font,
    )
    return canvas


def _render_horizontal_flow_strip(strip_w: int, strip_h: int, labels: list[str]) -> Image.Image:
    n = len(labels)
    arrow_w = 44
    gap = 10
    box_w = max(220, (strip_w - (n - 1) * (arrow_w + gap)) // n)
    box_h = min(96, strip_h - 8)
    nodes: list[Image.Image] = []
    for i, label in enumerate(labels):
        node = Image.new("RGBA", (box_w, box_h), (*hex_to_rgb("#121e38"), 255))
        d = ImageDraw.Draw(node)
        d.rounded_rectangle(
            [1, 1, box_w - 2, box_h - 2],
            radius=12,
            outline=hex_to_rgb(THEME["cyan"]),
            width=2,
        )
        font = load_ui_font(22, bold=True)
        tw = d.textlength(label, font=font)
        d.text(
            ((box_w - tw) / 2, (box_h - 26) / 2),
            label,
            fill=(245, 249, 255),
            font=font,
        )
        nodes.append(node)
    return stitch_panels_flow(
        nodes,
        gap=gap,
        arrow_w=arrow_w,
        bg=VIZ_BG,
        uniform_height=box_h,
    )


def _stitch_evo_thumbs_row() -> Image.Image | None:
    """五帧 XY 投影缩略图（对齐 VideoFindingsStrip 卡 01）。"""
    target_h = 132
    gap = 10
    label_h = 22
    pieces: list[Image.Image] = []
    for t in REP_STEPS:
        path = OUT / f"task1_evo_t{t:04d}.png"
        if not path.exists():
            continue
        img = Image.open(path).convert("RGBA")
        scale = target_h / max(1, img.height)
        w = max(1, int(img.width * scale))
        pieces.append((t, img.resize((w, target_h), Image.Resampling.LANCZOS)))

    if not pieces:
        fallback = OUT / "task1_vol_strip.png"
        if fallback.exists():
            return Image.open(fallback).convert("RGBA")
        return None

    total_w = sum(im.width for _t, im in pieces) + gap * (len(pieces) - 1)
    row = Image.new("RGBA", (total_w, target_h + label_h), (*hex_to_rgb(VIZ_BG), 255))
    draw = ImageDraw.Draw(row)
    font = load_ui_font(15)
    x = 0
    for t, thumb in pieces:
        row.paste(thumb, (x, 0), thumb)
        label = f"t={t}"
        tw = draw.textlength(label, font=font)
        draw.text(
            (x + (thumb.width - tw) / 2, target_h + 2),
            label,
            fill=hex_to_rgb(THEME["muted"]),
            font=font,
        )
        x += thumb.width + gap
    return row


def _findings_strip_card(
    *,
    num: str,
    title: str,
    subtitle: str | None,
    content: Image.Image | None,
    card_w: int,
    card_h: int,
) -> Image.Image:
    """单张发现卡（录屏 vd-findings 横条风格）。"""
    card = Image.new("RGBA", (card_w, card_h), (*hex_to_rgb("#121e38"), 255))
    draw = ImageDraw.Draw(card)
    border = hex_to_rgb(THEME["cyan"])
    gold = hex_to_rgb(THEME["gold"])
    draw.rounded_rectangle([0, 0, card_w - 1, card_h - 1], radius=12, outline=border, width=2)

    pad = 14
    num_font = load_ui_font(20, bold=True)
    title_font = load_ui_font(18, bold=True)
    sub_font = load_ui_font(14)
    draw.text((pad, pad), num, fill=gold, font=num_font)
    num_w = draw.textlength(num, font=num_font) + 10
    title_y = pad + 1
    if subtitle:
        draw.text((pad + num_w, title_y), title, fill=(245, 249, 255), font=title_font)
        draw.text(
            (pad + num_w, title_y + 24),
            subtitle,
            fill=hex_to_rgb(THEME["muted"]),
            font=sub_font,
        )
        body_top = pad + 52
    else:
        draw.text((pad + num_w, title_y + 2), title, fill=(245, 249, 255), font=title_font)
        body_top = pad + 36

    body_h = max(1, card_h - body_top - pad)
    body_w = card_w - 2 * pad
    if content is not None:
        fitted = fit_panel_contain(content, body_w, body_h, bg="#121e38", allow_upscale=True)
        px = pad + (body_w - fitted.width) // 2
        py = body_top + (body_h - fitted.height) // 2
        card.paste(fitted, (px, py), fitted)
    return card


def compose_findings_strip(timeline: dict) -> None:
    """1×4 发现卡横条 — 对齐 video.html 底部 VideoFindingsStrip。"""
    k = _story_kpis(timeline)
    s99 = k["s99"]
    card_w, card_h, gap = 900, 500, 16

    evo = _stitch_evo_thumbs_row()
    metrics_path = OUT / "task3_evolution_metrics.png"
    metrics = Image.open(metrics_path).convert("RGBA") if metrics_path.exists() else None

    mass_body = Image.new("RGBA", (420, 280), (*hex_to_rgb(VIZ_BG), 255))
    pie_path = OUT / "task5_mass_pie.png"
    if pie_path.exists():
        pie = Image.open(pie_path).convert("RGBA")
        left = pie.crop((0, 0, pie.width // 2, pie.height))
        mass_body = fit_panel_contain(left, 420, 280, bg=VIZ_BG, allow_upscale=True)

    top_v = OUT / "task4_brush_top1_viz.png"
    bot_v = OUT / "task4_brush_bottom_hl.png"
    verify_parts: list[Image.Image] = []
    for path, cap in ((top_v, f"Top 1% · ρ≥{s99['p99']:.2f}"), (bot_v, f"Bottom 1% · ρ≤{s99['p01']:.2f}")):
        if not path.exists():
            continue
        img = Image.open(path).convert("RGBA")
        thumb = fit_panel_contain(img, 200, 200, bg=VIZ_BG, allow_upscale=True)
        block = Image.new("RGBA", (220, 240), (*hex_to_rgb(VIZ_BG), 255))
        d = ImageDraw.Draw(block)
        cap_font = load_ui_font(13, bold=True)
        tw = d.textlength(cap, font=cap_font)
        d.text(((220 - tw) / 2, 4), cap, fill=hex_to_rgb(THEME["gold"]), font=cap_font)
        block.paste(thumb, ((220 - thumb.width) // 2, 28), thumb)
        verify_parts.append(block)
    verify_body: Image.Image | None = None
    if verify_parts:
        verify_body = stitch_panels_png(verify_parts, direction="horizontal", gap=12, max_width=520)

    cards = [
        _findings_strip_card(
            num="01",
            title="宇宙网形成",
            subtitle=None,
            content=evo,
            card_w=card_w,
            card_h=card_h,
        ),
        _findings_strip_card(
            num="02",
            title="密度分布两极化",
            subtitle=f"σ +{k['sigma_pct']:.1f}% · p99−p01 +{k['span_pct']:.1f}% · 右尾增厚",
            content=metrics,
            card_w=card_w,
            card_h=card_h,
        ),
        _findings_strip_card(
            num="03",
            title=f"{k['tail_vol']:.2f}% 体积 · {k['tail_mass']:.2f}% 质量",
            subtitle=None,
            content=mass_body,
            card_w=card_w,
            card_h=card_h,
        ),
        _findings_strip_card(
            num="04",
            title="统计—空间验证",
            subtitle=None,
            content=verify_body,
            card_w=card_w,
            card_h=card_h,
        ),
    ]
    strip = stitch_panels_png(cards, direction="horizontal", gap=gap, max_width=4000)
    for name in ("_rep_findings_strip.png", "task2_findings_strip.png"):
        save_pil_png(strip, OUT / name)
    print(f"Findings strip: {OUT / '_rep_findings_strip.png'} ({strip.width}×{strip.height}px)")


def representative_findings_summary(timeline: dict) -> None:
    """兼容旧入口：写入发现段中间产物（四幕海报不再依赖）。"""
    compose_findings_strip(timeline)
    panel = _build_findings_panel(timeline, NARR_CANVAS_W, NARR_FINDINGS_MIN_H)
    save_pil_png(panel, OUT / "_rep_findings_summary.png")
    print(f"Findings summary: {OUT / '_rep_findings_summary.png'} ({panel.width}×{panel.height}px)")


def representative_closing_panel(timeline: dict) -> None:
    """兼容旧入口：闭环收尾段（四幕海报不再使用）。"""
    _, _, h3, _ = _narr_compute_act_heights(NARR_CANVAS_W)
    panel = _build_closing_panel(timeline, NARR_CANVAS_W, h3)
    save_pil_png(panel, OUT / "_rep_closing_panel.png")
    print(f"Closing panel: {OUT / '_rep_closing_panel.png'} ({panel.width}×{panel.height}px)")


def representative_flow_mosaic(timeline: dict) -> None:
    """兼容旧入口。"""
    representative_findings_summary(timeline)
    representative_closing_panel(timeline)


def compose_representative_poster(timeline: dict | None = None) -> None:
    """文档/录屏对齐代表图 → 3840×5200。"""
    if timeline is None:
        timeline = json.loads(STATS.read_text(encoding="utf-8"))
    task3_story_panel(timeline)
    compose_task4_discovery_summary()
    compose_narrative_poster(timeline)


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
    compose_narrative_poster(timeline)


def capture_app_html_poster() -> bool:
    """合成 3840×5200 四幕叙事代表图（无需 Playwright）。"""
    if not STATS.exists():
        print("Missing timeline.json for narrative poster", file=sys.stderr)
        return False
    timeline = json.loads(STATS.read_text(encoding="utf-8"))
    try:
        compose_narrative_poster(timeline)
        return True
    except Exception as exc:
        print(f"Narrative poster failed: {exc}", file=sys.stderr)
        return False


def representative_poster(timeline: dict) -> None:
    sub = OUT.parent / "submission"
    sub.mkdir(parents=True, exist_ok=True)
    # 赛题代表图：PIL 四幕科学叙事海报（3840×5200）
    poster_candidates = (
        OUT / "task6_story_poster.png",
        OUT / "_app_poster_capture_resized.png",
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
    task4_discovery_context_panel(vol99, timeline, 99)
    task4_discovery_brush_panel(vol99, timeline, 99)
    task4_brush_bottom_panel(vol99, timeline, 99)

    from export_band_previews import export_band_previews

    export_band_previews(timeline, 99)

    highlight_bottom = render_xy_projection(vol99, timeline, s99["min"], s99["p01"])
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(highlight_bottom, origin="lower")
    ax.axis("off")
    save_figure(fig, OUT / "task4_brush_bottom_hl.png", pad=0.02)

    highlight = render_xy_projection(vol99, timeline, s99["p99"], s99["max"])
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
    compose_findings_strip(timeline)
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
            "Warning: narrative poster compose failed — representative falls back to existing PNG",
            file=sys.stderr,
        )
    representative_poster(timeline)

    print(f"Figures written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
