"""Drawing helpers for 3840×6480 poster (Pillow + mini matplotlib)."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import LogNorm
from PIL import Image, ImageDraw, ImageFont

from layout_spec import COLORS, FONT
from viz_style import COSMIC_CMAP, apply_dark_theme

apply_dark_theme()


def _hex_to_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) for i in (0, 2, 4))


RGB = {k: _hex_to_rgb(v) for k, v in COLORS.items()}


def load_fonts() -> dict[str, ImageFont.FreeTypeFont | ImageFont.ImageFont]:
    paths = [
        ("h1", "C:/Windows/Fonts/msyhbd.ttc", FONT["h1"]),
        ("h2", "C:/Windows/Fonts/msyhbd.ttc", FONT["h2"]),
        ("section", "C:/Windows/Fonts/msyhbd.ttc", FONT["section"]),
        ("body", "C:/Windows/Fonts/msyh.ttc", FONT["body"]),
        ("caption", "C:/Windows/Fonts/msyh.ttc", FONT["caption"]),
        ("subtitle", "C:/Windows/Fonts/msyh.ttc", FONT["subtitle"]),
    ]
    fonts: dict = {}
    for key, path, size in paths:
        p = Path(path)
        if p.exists():
            fonts[key] = ImageFont.truetype(str(p), size=size)
        else:
            fonts[key] = ImageFont.load_default()
    return fonts


def paste_cover(canvas: Image.Image, asset: Path | Image.Image, box: Tuple[int, int, int, int]) -> None:
    x, y, w, h = box
    if isinstance(asset, Path):
        if not asset.exists():
            return
        img = Image.open(asset).convert("RGBA")
    else:
        img = asset.convert("RGBA")
    iw, ih = img.size
    scale = max(w / iw, h / ih)
    nw, nh = int(iw * scale), int(ih * scale)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - w) // 2
    top = (nh - h) // 2
    img = img.crop((left, top, left + w, top + h))
    base = canvas.convert("RGBA")
    base.paste(img, (x, y), img)
    canvas.paste(base.convert("RGB"))


def draw_round_card(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int, int, int],
    *,
    fill: tuple[int, int, int] = (15, 25, 45),
    outline: tuple[int, int, int] = RGB["border"],
    radius: int = 12,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=2)


def draw_section_title(
    draw: ImageDraw.ImageDraw,
    fonts: dict,
    x: int,
    y: int,
    num: str,
    title: str,
    subtitle: str | None = None,
) -> int:
    draw.text((x, y), num, fill=RGB["accent_orange"], font=fonts["h1"])
    draw.text((x + 120, y + 18), title, fill=RGB["text"], font=fonts["h2"])
    line_y = y + 90
    if subtitle:
        draw.text((x, line_y), subtitle, fill=RGB["text_muted"], font=fonts["subtitle"])
        line_y += 48
    return line_y


def draw_vertical_colorbar(
    canvas: Image.Image,
    box: Tuple[int, int, int, int],
    vmin: float,
    vmax: float,
) -> None:
    x, y, w, h = box
    grad = np.linspace(0, 1, h).reshape(h, 1)
    rgba = COSMIC_CMAP(grad, bytes=True)
    bar = Image.fromarray(np.repeat(rgba, w, axis=1), mode="RGBA")
    canvas.paste(bar, (x, y))
    draw = ImageDraw.Draw(canvas)
    for label, py, color in [
        ("高密度", y + 12, RGB["peak_density"]),
        ("中密度", y + h // 2, RGB["mid_density"]),
        ("低密度", y + h - 36, RGB["low_density"]),
    ]:
        draw.text((x + w + 12, py), label, fill=color, font=load_fonts()["caption"])
    draw.text((x - 8, y - 28), "log₁₀ ρ", fill=RGB["text_muted"], font=load_fonts()["caption"])


def mpl_to_image(fig, w: int, h: int) -> Image.Image:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=100, facecolor=COLORS["bg"], edgecolor="none", bbox_inches="tight", pad_inches=0.05)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGBA")
    return img.resize((w, h), Image.Resampling.LANCZOS)


def render_sparkline(
    ts: list[int],
    values: list[float],
    *,
    color: str,
    title: str,
    badge: str,
    w: int,
    h: int,
) -> Image.Image:
    fig, ax = plt.subplots(figsize=(w / 100, h / 100), facecolor=COLORS["bg"])
    ax.set_facecolor("#0c1222")
    ax.plot(ts, values, color=color, lw=2.5)
    ax.fill_between(ts, values, alpha=0.15, color=color)
    ax.set_title(f"{title}  {badge}", fontsize=11, color=COLORS["text"], pad=8)
    ax.set_xlim(0, 99)
    ax.tick_params(colors=COLORS["text_muted"], labelsize=8)
    for spine in ax.spines.values():
        spine.set_color(COLORS["border"])
    ax.grid(True, alpha=0.2, color=COLORS["border"])
    return mpl_to_image(fig, w, h)


def ratio_label(v0: float, v99: float) -> str:
    if abs(v0) < 1e-12:
        return "—"
    return f"+{(v99 - v0) / v0 * 100:.1f}%"
