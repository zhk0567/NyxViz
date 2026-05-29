"""Animate 100-step log histogram evolution → GIF / MP4 for video B-roll."""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from viz_style import FIG_DPI, THEME, apply_dark_theme, style_axes

apply_dark_theme()

ROOT = Path(__file__).resolve().parents[2]
STATS = ROOT / "public" / "stats" / "timeline.json"
DEFAULT_GIF = ROOT / "docs" / "figures" / "task3_hist_evolution.gif"
DEFAULT_MP4 = ROOT / "docs" / "figures" / "task3_hist_evolution.mp4"
BROLL_DIR = ROOT / "docs" / "submission" / "broll"


def load_timeline() -> dict:
    return json.loads(STATS.read_text(encoding="utf-8"))


def bin_centers(timeline: dict) -> np.ndarray:
    edges = timeline["logBinEdges"]
    return np.array([np.sqrt(edges[i] * edges[i + 1]) for i in range(len(edges) - 1)])


def frame_indices(n_steps: int, *, every: int, max_frames: int | None) -> list[int]:
    indices = list(range(0, n_steps, every))
    if indices[-1] != n_steps - 1:
        indices.append(n_steps - 1)
    if max_frames and len(indices) > max_frames:
        pick = np.linspace(0, len(indices) - 1, max_frames, dtype=int)
        indices = [indices[i] for i in pick]
        if indices[-1] != n_steps - 1:
            indices.append(n_steps - 1)
        indices = sorted(set(indices))
    return indices


def render_animation(
    timeline: dict,
    out_path: Path,
    *,
    fmt: str,
    fps: int,
    every: int,
    max_frames: int | None,
    dpi: int,
) -> Path:
    centers = bin_centers(timeline)
    steps = timeline["timesteps"]
    n_steps = len(steps)
    frames = frame_indices(n_steps, every=every, max_frames=max_frames)

    hists = [np.array(timeline["histograms"][t], dtype=float) for t in range(n_steps)]
    y_max = max(float(h.max()) for h in hists) * 1.08

    fig, (ax_hist, ax_line) = plt.subplots(
        2,
        1,
        figsize=(8.5, 5.4),
        gridspec_kw={"height_ratios": [3.2, 1], "hspace": 0.28},
        facecolor="#0a0e1a",
    )
    ts = [s["timestep"] for s in steps]
    std_curve = [s["std"] for s in steps]
    ax_line.plot(ts, std_curve, color=THEME["cyan"], lw=1.2, alpha=0.5)
    (cursor,) = ax_line.plot([], [], "o", color=THEME["gold"], ms=8)
    ax_line.set_xlim(0, 99)
    ax_line.set_ylim(min(std_curve) * 0.95, max(std_curve) * 1.05)
    ax_line.set_ylabel("σ(t)", fontsize=9)
    ax_line.set_xlabel("时间步", fontsize=9)
    style_axes(ax_line)

    (line_hist,) = ax_hist.plot([], [], color=THEME["gold"], lw=2.2)
    fill = ax_hist.fill_between(centers, np.zeros_like(centers), alpha=0.35, color=THEME["purple"])
    ax_hist.set_xscale("log")
    ax_hist.set_xlim(centers.min(), centers.max())
    ax_hist.set_ylim(0, y_max)
    ax_hist.set_xlabel("密度 ρ (log)")
    ax_hist.set_ylabel("归一化频数")
    title = ax_hist.set_title("", fontsize=11, color="#e6edf3")
    style_axes(ax_hist)

    def update(frame_idx: int):
        nonlocal fill
        t = frames[frame_idx]
        y = hists[t]
        line_hist.set_data(centers, y)
        if fill is not None:
            fill.remove()
        fill = ax_hist.fill_between(centers, y, alpha=0.32, color=THEME["purple"])
        s = steps[t]
        title.set_text(
            f"Nyx 气体密度 log 直方图 · t={t}/99  "
            f"σ={s['std']:.3f}  skew={s['skewness']:.3f}  p99−p01={s['p99'] - s['p01']:.3f}"
        )
        cursor.set_data([t], [s["std"]])
        return line_hist, cursor

    anim = FuncAnimation(
        fig,
        update,
        frames=len(frames),
        interval=1000 / fps,
        blit=False,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    if fmt == "gif":
        writer = PillowWriter(fps=fps)
        anim.save(str(out_path), writer=writer, dpi=dpi)
    else:
        if not shutil.which("ffmpeg"):
            plt.close(fig)
            raise RuntimeError("ffmpeg not on PATH — install ffmpeg or use --format gif")
        anim.save(str(out_path), writer="ffmpeg", fps=fps, dpi=dpi)
    plt.close(fig)
    return out_path


def main() -> int:
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Generate histogram evolution GIF/MP4.")
    parser.add_argument("--format", choices=("gif", "mp4", "both"), default="gif")
    parser.add_argument("--fps", type=int, default=8, help="Frames per second (default 8)")
    parser.add_argument("--every", type=int, default=1, help="Use every Nth timestep (default 1)")
    parser.add_argument("--max-frames", type=int, default=None, help="Cap frame count")
    parser.add_argument("--dpi", type=int, default=100)
    parser.add_argument("--gif", type=Path, default=DEFAULT_GIF, dest="gif_out")
    parser.add_argument("--mp4", type=Path, default=DEFAULT_MP4, dest="mp4_out")
    parser.add_argument("--copy-broll", action="store_true", help="Also copy outputs to docs/submission/broll/")
    args = parser.parse_args()

    if not STATS.exists():
        print("Missing timeline.json — run: npm run precompute", file=sys.stderr)
        return 1

    timeline = load_timeline()
    written: list[Path] = []

    try:
        if args.format in ("gif", "both"):
            p = render_animation(
                timeline,
                args.gif_out,
                fmt="gif",
                fps=args.fps,
                every=args.every,
                max_frames=args.max_frames,
                dpi=args.dpi,
            )
            written.append(p)
        if args.format in ("mp4", "both"):
            p = render_animation(
                timeline,
                args.mp4_out,
                fmt="mp4",
                fps=args.fps,
                every=args.every,
                max_frames=args.max_frames,
                dpi=args.dpi,
            )
            written.append(p)
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if args.copy_broll:
        BROLL_DIR.mkdir(parents=True, exist_ok=True)
        for src in written:
            dest = BROLL_DIR / src.name
            shutil.copy2(src, dest)
            print(f"Copied → {dest}")

    for p in written:
        size_mb = p.stat().st_size / (1024 * 1024)
        print(f"Wrote {p} ({size_mb:.2f} MB)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
