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
LABEL_BAR_H = 32
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


def load_ui_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load Microsoft YaHei (or fallback) for PIL text rendering."""
    key = (size, bold)
    if key in _FONT_CACHE:
        return _FONT_CACHE[key]
    win = Path("C:/Windows/Fonts")
    candidates = [
        win / ("msyhbd.ttc" if bold else "msyh.ttc"),
        win / "msyh.ttc",
        win / "simhei.ttf",
        win / "arial.ttf",
    ]
    for path in candidates:
        if path.exists():
            try:
                font = ImageFont.truetype(str(path), size=size)
                _FONT_CACHE[key] = font
                return font
            except OSError:
                continue
    font = ImageFont.load_default()
    _FONT_CACHE[key] = font
    return font


def _rounded_rect(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int, int, int],
    radius: int,
    *,
    fill: tuple[int, ...] | None = None,
    outline: tuple[int, ...] | None = None,
    width: int = 1,
) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _draw_panel_shadow(canvas: Image.Image, x: int, y: int, w: int, h: int) -> None:
    shadow = Image.new("RGBA", (w + SHADOW_OFFSET, h + SHADOW_OFFSET), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    _rounded_rect(
        sd,
        (SHADOW_OFFSET, SHADOW_OFFSET, w + SHADOW_OFFSET - 1, h + SHADOW_OFFSET - 1),
        PANEL_RADIUS,
        fill=(0, 0, 0, SHADOW_ALPHA),
    )
    canvas.paste(shadow, (x - 1, y + 1), shadow)


def wrap_panel(
    img: Image.Image | Path | str,
    *,
    label: str | None = None,
    subtitle: str | None = None,
    accent: str = THEME["cyan"],
    content_height: int | None = None,
    max_content_width: int | None = None,
) -> Image.Image:
    """Wrap image in a rounded card with optional label bar."""
    if isinstance(img, (Path, str)):
        content = _load_rgba(img)
    else:
        content = img.convert("RGBA")

    if content_height and content.height != content_height:
        ratio = content_height / content.height
        content = content.resize(
            (max(1, int(content.width * ratio)), content_height),
            Image.Resampling.LANCZOS,
        )
    if max_content_width and content.width > max_content_width:
        ratio = max_content_width / content.width
        content = content.resize(
            (max_content_width, max(1, int(content.height * ratio))),
            Image.Resampling.LANCZOS,
        )

    label_h = LABEL_BAR_H if label else 0
    sub_h = 18 if subtitle and label else 0
    bar_h = label_h + sub_h
    inner_w = content.width
    inner_h = content.height
    card_w = inner_w + PANEL_PAD * 2
    card_h = inner_h + PANEL_PAD * 2 + bar_h

    card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
    _draw_panel_shadow(card, 0, 0, card_w, card_h)

    body = Image.new("RGBA", (card_w, card_h), (*hex_to_rgb(PANEL_BG), 255))
    bd = ImageDraw.Draw(body)
    _rounded_rect(
        bd,
        (0, 0, card_w - 1, card_h - 1),
        PANEL_RADIUS,
        outline=(*hex_to_rgb("#3a4558"), 255),
        width=PANEL_BORDER,
    )
    body.paste(content, (PANEL_PAD, PANEL_PAD), content)
    card.paste(body, (0, 0), body)

    if bar_h:
        bar_y = card_h - bar_h
        bar = Image.new("RGBA", (card_w, bar_h), (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar)
        bar_draw.rectangle((0, 0, 4, bar_h), fill=(*hex_to_rgb(accent), 255))
        bar_draw.rectangle((0, 0, card_w, bar_h), fill=(*hex_to_rgb("#1a2240"), 230))
        bar_draw.rectangle((0, 0, 4, bar_h), fill=(*hex_to_rgb(accent), 255))
        font = load_ui_font(16, bold=True)
        sub_font = load_ui_font(12)
        bar_draw.text((16, 6 if not sub_h else 4), label or "", fill=(230, 237, 243, 255), font=font)
        if subtitle:
            bar_draw.text((16, 20), subtitle, fill=(*hex_to_rgb(THEME["muted"]), 255), font=sub_font)
        card.paste(bar, (0, bar_y), bar)

    return card


def render_kpi_card(
    title: str,
    bullets: list[str],
    accent: str,
    *,
    width: int = 420,
    height: int = 520,
) -> Image.Image:
    """KPI bullet card for brush rows."""
    card = Image.new("RGBA", (width, height), (*hex_to_rgb(PANEL_BG), 255))
    draw = ImageDraw.Draw(card)
    _rounded_rect(
        draw,
        (0, 0, width - 1, height - 1),
        PANEL_RADIUS,
        outline=(*hex_to_rgb("#3a4558"), 255),
        width=PANEL_BORDER,
    )
    draw.rectangle((0, 0, 5, height), fill=(*hex_to_rgb(accent), 255))
    title_font = load_ui_font(18, bold=True)
    body_font = load_ui_font(15)
    draw.text((20, 24), title, fill=(*hex_to_rgb(accent), 255), font=title_font)
    y = 72
    for line in bullets:
        draw.text((24, y), f"• {line}", fill=(230, 237, 243, 255), font=body_font)
        y += 36
    return card


def render_inset_panel(
    img: Image.Image | Path | str,
    *,
    label: str = "局部放大",
    accent: str = THEME["cyan"],
    crop_ratio: float = 0.2,
) -> Image.Image:
    """Center crop inset wrapped as panel."""
    if isinstance(img, (Path, str)):
        source = _load_rgba(img)
    else:
        source = img.convert("RGBA")
    w, h = source.size
    cx, cy = w // 2, h // 2
    half = int(min(w, h) * crop_ratio)
    crop = source.crop((max(0, cx - half), max(0, cy - half), min(w, cx + half), min(h, cy + half)))
    return wrap_panel(crop, label=label, accent=accent, content_height=400)


def compose_sheet(
    title: str,
    subtitle: str | None,
    panels: list[Image.Image],
    *,
    direction: Literal["horizontal", "vertical"] = "horizontal",
    gap: int = PANEL_GAP,
    max_width: int = 4800,
    footer: Image.Image | None = None,
    bg: str = VIZ_BG,
) -> Image.Image:
    """Compose title bar + panel row/column + optional footer."""
    if not panels:
        raise ValueError("compose_sheet: no panels")

    if direction == "horizontal":
        row = stitch_panels_png(
            panels,
            direction="horizontal",
            gap=gap,
            bg=bg,
            max_width=max_width,
            draw_dividers=True,
            divider_width=2,
        )
    else:
        row = stitch_panels_png(
            panels,
            direction="vertical",
            gap=gap,
            bg=bg,
            max_width=max_width,
            draw_dividers=True,
            divider_width=2,
        )

    lines = [title]
    if subtitle:
        lines.append(subtitle)
    banner = render_text_banner(lines, row.width, bg=bg, align="left")
    footer_h = footer.height + 12 if footer else 0
    total_h = banner.height + 8 + row.height + footer_h
    canvas = Image.new("RGBA", (row.width, total_h), (*hex_to_rgb(bg), 255))
    y = 0
    canvas.paste(banner, (0, y))
    y += banner.height + 8
    canvas.paste(row, (0, y))
    y += row.height
    if footer:
        y += 8
        canvas.paste(footer, (0, y))
    return canvas


def compose_sectioned_poster(
    sections: list[tuple[str, str | None, list[Image.Image | Path | str]]],
    *,
    header_title: str,
    header_subtitle: str | None = None,
    max_width: int = 3840,
    bg: str = VIZ_BG,
    wrap_content: bool = False,
) -> Image.Image:
    """Vertical poster with labeled sections."""
    bg_rgb = hex_to_rgb(bg)
    section_images: list[Image.Image] = []
    for sec_title, sec_sub, paths in sections:
        loaded: list[Image.Image] = []
        for p in paths:
            if isinstance(p, Image.Image):
                im = p.convert("RGBA")
            else:
                im = _load_rgba(p)
            loaded.append(wrap_panel(im, label=None) if wrap_content else im)
        if len(loaded) == 1:
            row = loaded[0]
        else:
            row = stitch_panels_png(
                loaded,
                direction="horizontal",
                gap=PANEL_GAP,
                bg=bg,
                max_width=max_width,
                draw_dividers=True,
                divider_width=2,
            )
        if row.width > max_width:
            ratio = max_width / row.width
            row = row.resize((max_width, max(1, int(row.height * ratio))), Image.Resampling.LANCZOS)

        lines = [sec_title]
        if sec_sub:
            lines.append(sec_sub)
        sec_banner = render_text_banner(lines, row.width, bg=bg, align="left", pad_y=20)
        sec_h = sec_banner.height + 12 + row.height
        sec_canvas = Image.new("RGBA", (row.width, sec_h), (*bg_rgb, 255))
        sec_canvas.paste(sec_banner, (0, 0))
        sec_canvas.paste(row, (0, sec_banner.height + 8))
        section_images.append(sec_canvas)

    target_w = min(max_width, max(im.width for im in section_images))
    scaled: list[Image.Image] = []
    for im in section_images:
        if im.width > target_w:
            ratio = target_w / im.width
            im = im.resize((target_w, max(1, int(im.height * ratio))), Image.Resampling.LANCZOS)
        scaled.append(im)

    header_lines = [header_title]
    if header_subtitle:
        header_lines.append(header_subtitle)
    header = render_text_banner(header_lines, target_w, bg=bg, align="left", pad_y=32)

    total_h = header.height + SECTION_GAP + sum(im.height for im in scaled) + SECTION_GAP * (len(scaled) - 1)
    canvas = Image.new("RGBA", (target_w, total_h), (*bg_rgb, 255))
    y = 0
    canvas.paste(header, (0, y))
    y += header.height + SECTION_GAP
    draw = ImageDraw.Draw(canvas)
    for i, im in enumerate(scaled):
        canvas.paste(im, (0, y), im)
        y += im.height
        if i < len(scaled) - 1:
            ly = y + SECTION_GAP // 2
            draw.line([(24, ly), (target_w - 24, ly)], fill=(*DIVIDER_RGB, 255), width=2)
            y += SECTION_GAP
    return canvas


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
    paths: list[Path | str | Image.Image],
    *,
    direction: Literal["horizontal", "vertical"] = "horizontal",
    gap: int = PANEL_GAP,
    bg: str = VIZ_BG,
    max_width: int | None = 3840,
    uniform_height: int | None = None,
    panel_labels: list[str] | None = None,
    draw_dividers: bool = True,
    divider_width: int = 2,
    wrap_panels: bool = False,
    panel_accent: str = THEME["cyan"],
) -> Image.Image:
    """Stitch PNG panels without matplotlib imshow re-rasterization."""
    images: list[Image.Image] = []
    for i, p in enumerate(paths):
        if isinstance(p, Image.Image):
            images.append(p.convert("RGBA"))
        else:
            path = Path(p)
            if path.exists():
                im = _load_rgba(path)
                if wrap_panels:
                    label = panel_labels[i] if panel_labels and i < len(panel_labels) else None
                    im = wrap_panel(im, label=label, accent=panel_accent)
                images.append(im)

    if not images:
        raise ValueError("stitch_panels_png: no valid images")

    bg_rgb = hex_to_rgb(bg)
    label_h = 0
    if panel_labels and not wrap_panels:
        label_h = LABEL_BAR_H + 8

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
        title_font = load_ui_font(17, bold=True)
        x = 0
        max_im_h = max(im.height for im in images)
        for i, im in enumerate(images):
            y = label_h + (max_im_h - im.height) // 2
            canvas.paste(im, (x, y), im)
            if panel_labels and not wrap_panels and i < len(panel_labels):
                tw = draw.textlength(panel_labels[i], font=title_font)
                draw.text(
                    (x + (im.width - tw) / 2, 6),
                    panel_labels[i],
                    fill=(230, 237, 243, 255),
                    font=title_font,
                )
            if draw_dividers and i < len(images) - 1:
                lx = x + im.width + gap // 2
                draw.line([(lx, label_h), (lx, row_h)], fill=(*DIVIDER_RGB, 255), width=divider_width)
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
            draw.line([(24, ly), (target_w - 24, ly)], fill=(*DIVIDER_RGB, 255), width=divider_width)
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
    align: Literal["left", "center"] = "left",
    pad_x: int = 24,
) -> Image.Image:
    title_font = load_ui_font(22, bold=True)
    sub_font = load_ui_font(14)
    line_heights = [32, 26]
    height = pad_y * 2 + sum(line_heights[: len(lines)])
    img = Image.new("RGBA", (width, height), (*hex_to_rgb(bg), 255))
    draw = ImageDraw.Draw(img)
    y = pad_y
    for i, line in enumerate(lines):
        color = title_color if i == 0 else subtitle_color
        rgb = hex_to_rgb(color)
        font = title_font if i == 0 else sub_font
        tw = draw.textlength(line, font=font)
        if align == "center":
            x = (width - tw) / 2
        else:
            x = pad_x
        draw.text((x, y), line, fill=(*rgb, 255), font=font)
        y += line_heights[i] if i < len(line_heights) else 26
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


def render_vertical_colorbar_png(
    vmin: float,
    vmax: float,
    *,
    width: int = 56,
    height: int = 480,
    label: str = "log10 ρ (p01–p99)",
) -> Image.Image:
    fig_w = max(width / FIG_DPI, 0.5)
    fig_h = max(height / FIG_DPI, 4)
    fig = plt.figure(figsize=(fig_w, fig_h), facecolor=VIZ_BG)
    ax = fig.add_axes([0.15, 0.08, 0.35, 0.84])
    sm = plt.cm.ScalarMappable(cmap=COSMIC_CMAP, norm=LogNorm(vmin=max(vmin, 1e-6), vmax=max(vmax, 1e-6)))
    cb = fig.colorbar(sm, cax=ax, orientation="vertical")
    cb.set_label(label, color=THEME["muted"], fontsize=10)
    cb.ax.tick_params(colors=THEME["muted"], labelsize=8)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=FIG_DPI, facecolor=VIZ_BG, edgecolor="none", bbox_inches="tight", pad_inches=0.06)
    plt.close(fig)
    buf.seek(0)
    bar = Image.open(buf).convert("RGBA")
    if bar.height != height:
        ratio = height / bar.height
        bar = bar.resize((max(1, int(bar.width * ratio)), height), Image.Resampling.LANCZOS)
    return bar


def render_meta_badges(
    lines: list[str],
    *,
    width: int = 180,
    accent: str = THEME["cyan"],
) -> Image.Image:
    """Vertical metadata badge column for hero poster."""
    badge_h = 52
    gap = 12
    height = len(lines) * badge_h + gap * (len(lines) - 1)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_ui_font(14, bold=True)
    for i, line in enumerate(lines):
        y = i * (badge_h + gap)
        _rounded_rect(
            draw,
            (0, y, width - 1, y + badge_h - 1),
            8,
            fill=(*hex_to_rgb("#1a2240"), 255),
            outline=(*hex_to_rgb("#3a4558"), 255),
            width=1,
        )
        tw = draw.textlength(line, font=font)
        draw.text(((width - tw) / 2, y + 16), line, fill=(*hex_to_rgb(accent), 255), font=font)
    return img


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
