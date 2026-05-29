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
    FIG_DPI,
    THEME,
    apply_dark_theme,
    global_projection_domain,
    style_axes,
)

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
    fig.tight_layout()
    fig.savefig(out, dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)


def resolve_vol_image(t: int, timeline: dict) -> Path:
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


def task1_strip(timeline: dict) -> None:
    fig = plt.figure(figsize=(18, 4.2), facecolor="#0a0e1a")
    gs = gridspec.GridSpec(1, 5, wspace=0.04)
    for i, t in enumerate(REP_STEPS):
        ax = fig.add_subplot(gs[0, i])
        img = mpimg.imread(resolve_vol_image(t, timeline))
        ax.imshow(img, aspect="equal")
        s = timeline["timesteps"][t]
        ax.set_title(f"t={t}\nσ={s['std']:.3f}", fontsize=10, color="#e6edf3")
        for spine in ax.spines.values():
            spine.set_edgecolor("#3a4558")
            spine.set_linewidth(0.8)
        ax.set_xticks([])
        ax.set_yticks([])
    vmin, vmax = global_projection_domain(timeline)
    cax = fig.add_axes([0.25, 0.02, 0.5, 0.03])
    sm = plt.cm.ScalarMappable(
        cmap=COSMIC_CMAP,
        norm=LogNorm(vmin=max(vmin, 1e-6), vmax=max(vmax, 1e-6)),
    )
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.set_label("密度 ρ (log, 全局 p01–p99)", color="#9aa3b8")
    cb.ax.tick_params(colors="#9aa3b8")
    fig.suptitle(
        "体渲染关键帧：气体密度宇宙学演化 (128³)",
        fontsize=13,
        color="#e6edf3",
        y=1.02,
    )
    fig.savefig(OUT / "task1_vol_strip.png", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)


def task2_evolution_story(timeline: dict) -> None:
    steps = timeline["timesteps"]
    ts = [s["timestep"] for s in steps]
    span = [s["p99"] - s["p01"] for s in steps]
    tail = [s["tailMassAboveP99"] * 100 for s in steps]
    std = [s["std"] for s in steps]
    skew = [s["skewness"] for s in steps]

    fig, axes = plt.subplots(2, 2, figsize=(10, 7))
    specs = [
        (span, THEME["purple"], "分位跨度 p99−p01（团块化）"),
        (std, THEME["cyan"], "标准差 σ(t)"),
        (tail, THEME["gold"], "高密度尾体积占比 ≥p99 (%)"),
        (skew, THEME["coral"], "偏度 skew(t)"),
    ]
    for ax, (y, color, title) in zip(axes.flat, specs):
        ax.fill_between(ts, y, alpha=0.12, color=color)
        ax.plot(ts, y, color=color, lw=2)
        ax.set_title(title)
        ax.set_xlabel("时间步")
        style_axes(ax)

    fig.suptitle("任务二：100 步全域统计揭示的演化规律", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "task2_evolution_story.png", dpi=FIG_DPI)
    plt.close(fig)


def task3_figures(timeline: dict) -> None:
    edges = timeline["logBinEdges"]
    centers = [np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)]
    steps = timeline["timesteps"]
    colors = [THEME["purple"], THEME["blue"], THEME["cyan"], THEME["gold"], THEME["coral"]]

    fig, ax = plt.subplots(figsize=(8, 5))
    for t, c in zip(REP_STEPS, colors):
        hist = timeline["histograms"][t]
        ax.plot(centers, hist, label=f"t={t}", color=c, lw=1.8)
    ax.set_xscale("log")
    ax.set_xlabel("密度 ρ (log)")
    ax.set_ylabel("归一化频数")
    ax.set_title("对数等距分箱直方图叠加（代表步）")
    ax.legend()
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(OUT / "task3_hist_overlay.png", dpi=FIG_DPI)
    plt.close(fig)

    ts = [s["timestep"] for s in steps]
    fig, ax = plt.subplots(figsize=(9, 4))
    means = [s["mean"] for s in steps]
    ax.fill_between(ts, means, alpha=0.15, color=THEME["purple"])
    ax.plot(ts, means, label="均值", color=THEME["purple"], lw=2)
    ax.plot(ts, [s["p99"] for s in steps], label="p99", color=THEME["gold"], lw=1.8)
    ax.plot(ts, [s["std"] for s in steps], label="σ", color=THEME["cyan"], lw=1.8)
    ax.set_xlabel("时间步")
    ax.set_ylabel("密度统计量")
    ax.set_title("100 时间步时序指标")
    ax.legend()
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(OUT / "task3_metrics_timeline.png", dpi=FIG_DPI)
    plt.close(fig)

    fig, axes = plt.subplots(1, 3, figsize=(12, 3.8))
    axes[0].plot(ts, [s["std"] for s in steps], color=THEME["cyan"], lw=2)
    axes[0].set_title("σ(t) 持续扩大")
    axes[1].plot(ts, [s["skewness"] for s in steps], color=THEME["coral"], lw=2)
    axes[1].set_title("偏度 — 右尾增厚")
    axes[2].plot(ts, [s["p99"] - s["p01"] for s in steps], color=THEME["purple"], lw=2)
    axes[2].set_title("p99−p01 分位跨度")
    for ax in axes:
        ax.set_xlabel("t")
        style_axes(ax)
    fig.suptitle("任务三：两极分化与涨落增强", fontsize=11)
    fig.tight_layout()
    fig.savefig(OUT / "task3_evolution_metrics.png", dpi=FIG_DPI)
    plt.close(fig)

    peak_t = []
    for t in range(100):
        h = timeline["histograms"][t]
        peak_t.append(centers[int(np.argmax(h))])
    fig, ax = plt.subplots(figsize=(8, 3.5))
    ax.plot(ts, peak_t, color=THEME["gold"], lw=2)
    ax.set_xscale("log")
    ax.set_xlabel("时间步")
    ax.set_ylabel("主峰中心密度 (log)")
    ax.set_title("直方图主峰位置随时间的漂移")
    style_axes(ax)
    fig.tight_layout()
    fig.savefig(OUT / "task3_peak_drift.png", dpi=FIG_DPI)
    plt.close(fig)


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
    axes[0].set_title("XY 最大密度投影（全场）")
    axes[0].axis("off")
    axes[1].imshow(highlight, origin="lower")
    axes[1].set_title(f"刷选高亮：ρ ∈ [{lo:.2f}, {hi:.2f}]")
    axes[1].axis("off")
    fig.suptitle(title)
    fig.tight_layout()
    fig.savefig(out, dpi=FIG_DPI)
    plt.close(fig)


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
        fig.tight_layout()
        fig.savefig(OUT / fname, dpi=FIG_DPI)
        plt.close(fig)

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
    fig.tight_layout()
    fig.savefig(OUT / "task4_spatial_to_stats.png", dpi=FIG_DPI)
    plt.close(fig)
    return lo, hi


def task4_triptych(timeline: dict) -> None:
    paths = [
        OUT / "task4_hist_brush_top1.png",
        resolve_vol_image(99, timeline),
        OUT / "task4_brush_top1.png",
    ]
    fig = plt.figure(figsize=(15, 4.8))
    for i, p in enumerate(paths):
        ax = fig.add_subplot(1, 3, i + 1)
        ax.imshow(mpimg.imread(p))
        labels = ["统计刷选", "体渲染 (t=99)", "空间投影验证"]
        ax.set_title(labels[i], fontsize=11, color="#e6edf3", pad=6)
        ax.axis("off")
    fig.suptitle("相空间联动：Top 1% 高密度尾 → 宇宙网节点", fontsize=12, color="#e6edf3")
    fig.tight_layout()
    fig.savefig(OUT / "task4_brush_triptych.png", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)


def representative_poster(timeline: dict) -> None:
    fig = plt.figure(figsize=(16, 11), facecolor="#0a0e1a")
    gs = gridspec.GridSpec(2, 2, height_ratios=[1.05, 1], hspace=0.1, wspace=0.06)

    ax0 = fig.add_subplot(gs[0, :])
    ax0.imshow(mpimg.imread(OUT / "task1_vol_strip.png"))
    ax0.axis("off")
    ax0.set_title("任务一 · 体渲染五时刻", fontsize=13, color="#e6edf3", pad=12)

    ax1 = fig.add_subplot(gs[1, 0])
    ax1.imshow(mpimg.imread(OUT / "task2_evolution_story.png"))
    ax1.axis("off")
    ax1.set_title("任务二 · 演化规律", fontsize=12, color="#e6edf3", pad=8)

    ax2 = fig.add_subplot(gs[1, 1])
    ax2.imshow(mpimg.imread(OUT / "task4_brush_triptych.png"))
    ax2.axis("off")
    ax2.set_title("任务四 · 刷选联动验证", fontsize=12, color="#e6edf3", pad=8)

    s0, s99 = timeline["timesteps"][0], timeline["timesteps"][99]
    fig.suptitle(
        f"Nyx 128³ 气体密度可视化 | σ: {s0['std']:.3f}→{s99['std']:.3f} | "
        f"分位跨度: {s0['p99']-s0['p01']:.3f}→{s99['p99']-s99['p01']:.3f}",
        fontsize=14,
        color="#e6edf3",
        y=0.99,
    )
    sub = OUT.parent / "submission"
    sub.mkdir(parents=True, exist_ok=True)
    fig.savefig(sub / "submission_representative.jpg", dpi=FIG_DPI, bbox_inches="tight")
    plt.close(fig)


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

    task1_strip(timeline)
    task2_evolution_story(timeline)
    task3_figures(timeline)

    vol99 = load_volume(NYX / "0099.dat")
    s99 = timeline["timesteps"][99]
    highlight = render_xy_projection(vol99, timeline, s99["p99"], s99["max"])
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.imshow(highlight, origin="lower")
    ax.set_title(f"Top 1% 体素 XY 投影 (t=99, ρ≥{s99['p99']:.2f})")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "task4_brush_top1.png", dpi=FIG_DPI)
    plt.close(fig)

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
    representative_poster(timeline)

    print(f"Figures written to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
