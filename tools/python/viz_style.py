"""Shared matplotlib styling and PIL stitch utilities for NyxViz figures."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Literal

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.figure import Figure
from PIL import Image, ImageDraw

FIG_DPI = 300
DOC_EMBED_DPI = 300
VIZ_BG = "#0a0e1a"
PANEL_BG = "#0f1424"
GRID_ALPHA = 0.18
LINE_WIDTH = 2.5
DIVIDER_RGB = (58, 69, 88)

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


def apply_dark_theme() -> None:
    plt.rcParams.update(
        {
            "figure.facecolor": VIZ_BG,
            "axes.facecolor": PANEL_BG,
            "axes.edgecolor": "#2a3348",
            "axes.labelcolor": THEME["muted"],
            "axes.titlecolor": "#e6edf3",
            "xtick.color": THEME["muted"],
            "ytick.color": THEME["muted"],
            "text.color": "#e6edf3",
            "grid.color": "#3a4558",
            "grid.alpha": GRID_ALPHA,
            "legend.facecolor": PANEL_BG,
            "legend.edgecolor": "#2a3348",
            "font.sans-serif": ["Microsoft YaHei", "SimHei", "DejaVu Sans"],
            "axes.unicode_minus": False,
            "savefig.facecolor": VIZ_BG,
            "savefig.edgecolor": VIZ_BG,
            "lines.linewidth": LINE_WIDTH,
        }
    )


def style_axes(ax) -> None:
    ax.set_facecolor(PANEL_BG)
    ax.grid(True, alpha=GRID_ALPHA)
    for spine in ax.spines.values():
        spine.set_edgecolor((78 / 255, 196 / 255, 255 / 255, 0.22))


def save_figure(
    fig: Figure,
    path: Path | str,
    *,
    has_suptitle: bool = False,
    pad: float = 0.14,
    dpi: int | None = None,
) -> None:
    """Save with bbox_inches=tight so titles and suptitles are not clipped."""
    if has_suptitle:
        fig.tight_layout(rect=[0, 0, 1, 0.90])
    else:
        fig.tight_layout()
    fig.savefig(
        path,
        dpi=dpi or FIG_DPI,
        bbox_inches="tight",
        pad_inches=pad,
        facecolor=fig.get_facecolor(),
        edgecolor="none",
        pil_kwargs={"compress_level": 3},
    )
    plt.close(fig)


def _load_rgba(path: Path | str) -> Image.Image:
    return Image.open(path).convert("RGBA")


def _resize_down(img: Image.Image, max_w: int, max_h: int) -> Image.Image:
    w, h = img.size
    scale = min(max_w / w, max_h / h, 1.0)
    if scale >= 1.0:
        return img
    return img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.Resampling.LANCZOS)


def _fit_height(img: Image.Image, height: int) -> Image.Image:
    if img.height == height:
        return img
    if img.height > height:
        ratio = height / img.height
        return img.resize((max(1, int(img.width * ratio)), height), Image.Resampling.LANCZOS)
    return img


def stitch_panels_png(
    paths: list[Path | str],
    *,
    direction: Literal["horizontal", "vertical"] = "horizontal",
    gap: int = 12,
    bg: str = VIZ_BG,
    max_width: int | None = 3840,
    uniform_height: int | None = None,
    panel_labels: list[str] | None = None,
    draw_dividers: bool = True,
) -> Image.Image:
    """Stitch PNG panels without matplotlib imshow re-rasterization."""
    images: list[Image.Image] = []
    for p in paths:
        path = Path(p)
        if path.exists():
            images.append(_load_rgba(path))

    if not images:
        raise ValueError("stitch_panels_png: no valid images")

    bg_rgb = hex_to_rgb(bg)
    label_h = 0
    if panel_labels:
        label_h = 44

    if direction == "horizontal":
        if uniform_height:
            images = [_fit_height(im, uniform_height) for im in images]
        total_w = sum(im.width for im in images) + gap * (len(images) - 1)
        row_h = max(im.height for im in images) + label_h
        if max_width and total_w > max_width:
            scale = max_width / total_w
            images = [
                im.resize((max(1, int(im.width * scale)), max(1, int(im.height * scale))), Image.Resampling.LANCZOS)
                for im in images
            ]
            total_w = sum(im.width for im in images) + gap * (len(images) - 1)
            row_h = max(im.height for im in images) + label_h

        canvas = Image.new("RGBA", (total_w, row_h), (*bg_rgb, 255))
        draw = ImageDraw.Draw(canvas)
        x = 0
        for i, im in enumerate(images):
            y = label_h + (max(im.height for im in images) - im.height) // 2
            canvas.paste(im, (x, y), im)
            if panel_labels and i < len(panel_labels):
                draw.text((x + im.width // 2, 8), panel_labels[i], fill=(230, 237, 243, 255), anchor="ma")
            if draw_dividers and i < len(images) - 1:
                lx = x + im.width + gap // 2
                draw.line([(lx, label_h), (lx, row_h)], fill=(*DIVIDER_RGB, 255), width=1)
            x += im.width + gap
        return canvas

    # vertical
    target_w = min(max(im.width for im in images), max_width or 3840)
    scaled: list[Image.Image] = []
    for im in images:
        if im.width > target_w:
            ratio = target_w / im.width
            scaled.append(im.resize((target_w, max(1, int(im.height * ratio))), Image.Resampling.LANCZOS))
        else:
            scaled.append(im)
    images = scaled
    total_h = sum(im.height for im in images) + gap * (len(images) - 1)
    canvas = Image.new("RGBA", (target_w, total_h), (*bg_rgb, 255))
    y = 0
    draw = ImageDraw.Draw(canvas)
    for i, im in enumerate(images):
        x = (target_w - im.width) // 2
        canvas.paste(im, (x, y), im)
        if draw_dividers and i < len(images) - 1:
            ly = y + im.height + gap // 2
            draw.line([(0, ly), (target_w, ly)], fill=(*DIVIDER_RGB, 255), width=1)
        y += im.height + gap
    return canvas


def render_text_banner(
    lines: list[str],
    width: int,
    *,
    bg: str = VIZ_BG,
    title_color: str = "#e6edf3",
    subtitle_color: str = "#9aa3b8",
    pad_y: int = 28,
) -> Image.Image:
    line_h = 32
    height = pad_y * 2 + line_h * len(lines)
    img = Image.new("RGBA", (width, height), (*hex_to_rgb(bg), 255))
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        color = title_color if i == 0 else subtitle_color
        rgb = hex_to_rgb(color)
        draw.text((width // 2, pad_y + i * line_h), line, fill=(*rgb, 255), anchor="ma")
    return img


def render_horizontal_colorbar_png(
    vmin: float,
    vmax: float,
    width: int,
    *,
    height: int = 56,
    label: str = "密度 ρ (log, 全局 p01–p99)",
) -> Image.Image:
    fig_w = max(width / FIG_DPI, 6)
    fig_h = max(height / FIG_DPI, 0.45)
    fig = plt.figure(figsize=(fig_w, fig_h), facecolor=VIZ_BG)
    ax = fig.add_axes([0.08, 0.35, 0.84, 0.35])
    sm = plt.cm.ScalarMappable(cmap=COSMIC_CMAP, norm=LogNorm(vmin=max(vmin, 1e-6), vmax=max(vmax, 1e-6)))
    cb = fig.colorbar(sm, cax=ax, orientation="horizontal")
    cb.set_label(label, color=THEME["muted"], fontsize=11)
    cb.ax.tick_params(colors=THEME["muted"], labelsize=9)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=FIG_DPI, facecolor=VIZ_BG, edgecolor="none", bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    buf.seek(0)
    bar = Image.open(buf).convert("RGBA")
    if bar.width != width:
        ratio = width / bar.width
        bar = bar.resize((width, max(1, int(bar.height * ratio))), Image.Resampling.LANCZOS)
    return bar


def save_pil_png(img: Image.Image, path: Path | str, *, dpi: int = FIG_DPI) -> None:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, hex_to_rgb(VIZ_BG))
        bg.paste(img, mask=img.split()[3])
        rgb = bg
    else:
        rgb = img.convert("RGB")
    rgb.save(out, format="PNG", dpi=(dpi, dpi), compress_level=3)


def stitch_vertical_weighted(
    items: list[tuple[Path | str, float]],
    *,
    max_width: int = 3840,
    gap: int = 16,
    bg: str = VIZ_BG,
    header_lines: list[str] | None = None,
) -> Image.Image:
    """Stack panels vertically; weight controls relative display height after width normalize."""
    panels: list[tuple[Image.Image, float]] = []
    for path, weight in items:
        p = Path(path)
        if p.exists():
            panels.append((_load_rgba(p), weight))
    if not panels:
        raise ValueError("stitch_vertical_weighted: no panels")

    target_w = min(max_width, max(im.width for im, _ in panels))
    scaled: list[tuple[Image.Image, float]] = []
    for im, weight in panels:
        if im.width > target_w:
            ratio = target_w / im.width
            im = im.resize((target_w, max(1, int(im.height * ratio))), Image.Resampling.LANCZOS)
        scaled.append((im, weight))

    total_weight = sum(w for _, w in scaled) or 1.0
    base_h = int(sum(im.height for im, _ in scaled))
    canvas_h = base_h + gap * (len(scaled) - 1)
    if header_lines:
        canvas_h += 72
    canvas = Image.new("RGBA", (target_w, canvas_h), (*hex_to_rgb(bg), 255))
    y = 0
    if header_lines:
        banner = render_text_banner(header_lines, target_w, bg=bg)
        canvas.paste(banner, (0, 0))
        y = banner.height + gap // 2

    draw = ImageDraw.Draw(canvas)
    for i, (im, _) in enumerate(scaled):
        x = (target_w - im.width) // 2
        canvas.paste(im, (x, y), im)
        if i < len(scaled) - 1:
            ly = y + im.height + gap // 2
            draw.line([(0, ly), (target_w, ly)], fill=(*DIVIDER_RGB, 255), width=1)
        y += im.height + gap
    return canvas


def global_projection_domain(timeline: dict) -> tuple[float, float]:
    mins = [s["p01"] for s in timeline["timesteps"]]
    maxs = [s["p99"] for s in timeline["timesteps"]]
    return float(min(mins)), float(max(maxs))


def log_norm_unit(values: np.ndarray, vmin: float, vmax: float) -> np.ndarray:
    lo = np.log10(max(vmin, 1e-6))
    hi = np.log10(max(vmax, 1e-6))
    span = hi - lo if hi > lo else 1.0
    v = np.clip(values, vmin, vmax)
    return np.clip((np.log10(np.maximum(v, 1e-6)) - lo) / span, 0.0, 1.0)
