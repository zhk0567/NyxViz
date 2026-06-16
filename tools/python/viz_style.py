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
LABEL_BAR_H = 44
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


def _draw_corner_badge(
    canvas: Image.Image,
    letter: str,
    x: int,
    y: int,
    *,
    font_size: int = 28,
) -> None:
    """Bold panel letter badge at top-left of subplot content (e.g. (a))."""
    text = letter if letter.startswith("(") else f"({letter.lower()})"
    draw = ImageDraw.Draw(canvas)
    font = load_ui_font(font_size, bold=True)
    tw = int(draw.textlength(text, font=font))
    pad_x = max(12, int(font_size * 0.38))
    bh = int(font_size * 1.55)
    bw = tw + pad_x * 2
    _rounded_rect(
        draw,
        (x, y, x + bw - 1, y + bh - 1),
        8,
        fill=(10, 16, 32, 250),
        outline=(120, 220, 255, 255),
        width=3,
    )
    bbox = draw.textbbox((0, 0), text, font=font)
    th = bbox[3] - bbox[1]
    tx = x + (bw - tw) // 2
    ty = y + (bh - th) // 2 - bbox[1]
    draw.text((tx, ty), text, fill=(255, 255, 255, 255), font=font)


def split_panel_label(label: str) -> tuple[str | None, str]:
    """'(a) Moran's I 时序' → ('(a)', \"Moran's I 时序\")."""
    import re

    m = re.match(r"^\(([a-z])\)\s*(.*)$", label.strip(), re.I)
    if not m:
        return None, label
    letter = f"({m.group(1).lower()})"
    caption = m.group(2).strip()
    return letter, caption or label


def wrap_panel(
    img: Image.Image | Path | str,
    *,
    label: str | None = None,
    subtitle: str | None = None,
    corner_letter: str | None = None,
    accent: str = THEME["cyan"],
    content_height: int | None = None,
    max_content_width: int | None = None,
    label_font_size: int = 26,
    subtitle_font_size: int = 18,
    corner_font_size: int = 28,
    header: Literal["bottom", "inline"] = "bottom",
    header_content_gap: int = 6,
    subtitle_gap: int = 4,
    subtitle_tail_pad: int = 12,
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

    inner_w = content.width
    inner_h = content.height
    _probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))

    if header == "inline" and (corner_letter or label):
        letter_font = load_ui_font(corner_font_size, bold=True)
        title_font = load_ui_font(label_font_size, bold=True)
        sub_font = load_ui_font(subtitle_font_size) if subtitle else None
        letter_text = (
            corner_letter
            if not corner_letter or corner_letter.startswith("(")
            else f"({corner_letter.lower()})"
        )
        lb = _probe.textbbox((0, 0), letter_text, font=letter_font)
        badge_w = (lb[2] - lb[0]) + max(24, corner_font_size // 2)
        badge_h = int(corner_font_size * 1.55)
        title_h = 0
        if label:
            tb = _probe.textbbox((0, 0), label, font=title_font)
            title_h = tb[3] - tb[1]
        row_h = max(badge_h, title_h) + 14
        sub_h = 0
        if subtitle and sub_font:
            sb = _probe.textbbox((0, 0), subtitle, font=sub_font)
            sub_h = subtitle_gap + (sb[3] - sb[1]) + subtitle_tail_pad
        header_total = row_h + sub_h + header_content_gap
        card_w = inner_w + PANEL_PAD * 2
        card_h = inner_h + PANEL_PAD * 2 + header_total

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
        body.paste(content, (PANEL_PAD, PANEL_PAD + header_total), content)
        card.paste(body, (0, 0), body)

        hdr = ImageDraw.Draw(card)
        bx = PANEL_PAD + 8
        by = PANEL_PAD + 6
        if corner_letter:
            _rounded_rect(
                hdr,
                (bx, by, bx + badge_w - 1, by + badge_h - 1),
                8,
                fill=(10, 16, 32, 250),
                outline=(120, 220, 255, 255),
                width=3,
            )
            lbb = hdr.textbbox((0, 0), letter_text, font=letter_font)
            ltw = lbb[2] - lbb[0]
            lth = lbb[3] - lbb[1]
            hdr.text(
                (bx + (badge_w - ltw) // 2, by + (badge_h - lth) // 2 - lbb[1]),
                letter_text,
                fill=(255, 255, 255, 255),
                font=letter_font,
            )
        tx = bx + (badge_w + 12 if corner_letter else 0)
        if label:
            tb = hdr.textbbox((0, 0), label, font=title_font)
            ty = PANEL_PAD + (row_h - (tb[3] - tb[1])) // 2 - tb[1]
            hdr.text((tx, ty), label, fill=(230, 237, 243, 255), font=title_font)
        if subtitle and sub_font:
            sb = hdr.textbbox((0, 0), subtitle, font=sub_font)
            hdr.text(
                (PANEL_PAD + 8, PANEL_PAD + row_h + subtitle_gap - sb[1]),
                subtitle,
                fill=(*hex_to_rgb(THEME["muted"]), 255),
                font=sub_font,
            )
        return card

    label_font = load_ui_font(label_font_size, bold=True) if label else None
    sub_font = load_ui_font(subtitle_font_size) if subtitle and label else None
    label_pad_y = max(18, label_font_size // 5)
    if label and label_font:
        lb = _probe.textbbox((0, 0), label, font=label_font)
        label_h = (lb[3] - lb[1]) + label_pad_y * 2
    else:
        label_h = 0
    if subtitle and label and sub_font:
        sb = _probe.textbbox((0, 0), subtitle, font=sub_font)
        sub_h = (sb[3] - sb[1]) + 12
    else:
        sub_h = 0
    bar_h = label_h + sub_h
    badge_h = int(corner_font_size * 1.55) if corner_letter else 0
    badge_reserve = badge_h + PANEL_PAD + 28 if corner_letter else 0
    card_w = inner_w + PANEL_PAD * 2
    card_h = inner_h + PANEL_PAD * 2 + bar_h + badge_reserve

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
    body.paste(content, (PANEL_PAD, PANEL_PAD + badge_reserve), content)
    card.paste(body, (0, 0), body)

    if corner_letter:
        _draw_corner_badge(
            card,
            corner_letter,
            PANEL_PAD + 8,
            PANEL_PAD + 8,
            font_size=corner_font_size,
        )

    if bar_h:
        bar_y = card_h - bar_h
        bar = Image.new("RGBA", (card_w, bar_h), (0, 0, 0, 0))
        bar_draw = ImageDraw.Draw(bar)
        bar_draw.rectangle((0, 0, card_w, bar_h), fill=(*hex_to_rgb("#1a2240"), 230))
        bar_draw.rectangle((0, 0, 4, bar_h), fill=(*hex_to_rgb(accent), 255))
        font = label_font or load_ui_font(label_font_size, bold=True)
        sub_font = sub_font or load_ui_font(subtitle_font_size)
        text_x = max(22, label_font_size // 2)
        lb = bar_draw.textbbox((0, 0), label or "", font=font)
        lh = lb[3] - lb[1]
        label_y = label_pad_y - lb[1]
        if subtitle:
            label_y = 12 - lb[1]
        bar_draw.text((text_x, label_y), label or "", fill=(230, 237, 243, 255), font=font)
        if subtitle:
            bar_draw.text(
                (text_x, label_y + lh + 8),
                subtitle,
                fill=(*hex_to_rgb(THEME["muted"]), 255),
                font=sub_font,
            )
        card.paste(bar, (0, bar_y), bar)

    return card


def _wrap_text_lines(text: str, font, max_width: int) -> list[str]:
    """按像素宽度折行（适用于中英文混排）。"""
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines: list[str] = []
    cur = ""
    for ch in text:
        test = cur + ch
        bb = probe.textbbox((0, 0), test, font=font)
        if bb[2] - bb[0] <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = ch
    if cur:
        lines.append(cur)
    return lines or [text]


def render_kpi_card(
    title: str,
    bullets: list[str],
    accent: str,
    *,
    width: int = 420,
    height: int | None = None,
    title_font_size: int = 18,
    body_font_size: int = 15,
    line_spacing: int = 36,
    border: bool = True,
    pad_x: int = 20,
    pad_y: int = 20,
    layout: Literal["list", "grid"] = "list",
) -> Image.Image:
    """KPI bullet card for brush rows."""
    title_font = load_ui_font(title_font_size, bold=True)
    body_font = load_ui_font(body_font_size)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    text_w = width - pad_x * 2

    if layout == "grid" and len(bullets) >= 4:
        title_lines = _wrap_text_lines(title, title_font, text_w)
        title_line_h = []
        for ln in title_lines:
            tb = probe.textbbox((0, 0), ln, font=title_font)
            title_line_h.append(tb[3] - tb[1])
        title_block_h = sum(title_line_h) + max(0, len(title_lines) - 1) * 4
        col_w = max(1, (text_w - 12) // 2)
        rows = [(bullets[0], bullets[1]), (bullets[2], bullets[3])]
        row_h = []
        for left, right in rows:
            lb = probe.textbbox((0, 0), f"• {left}", font=body_font)
            rb = probe.textbbox((0, 0), f"• {right}", font=body_font)
            row_h.append(max(lb[3] - lb[1], rb[3] - rb[1]))
        grid_h = sum(row_h) + 10
        inner_h = pad_y + title_block_h + 10 + grid_h + pad_y
        card_h = height if height is not None and height > inner_h else inner_h
        card = Image.new("RGBA", (width, card_h), (*hex_to_rgb(PANEL_BG), 255))
        draw = ImageDraw.Draw(card)
        if border:
            _rounded_rect(
                draw,
                (0, 0, width - 1, card_h - 1),
                PANEL_RADIUS,
                outline=(*hex_to_rgb("#3a4558"), 255),
                width=PANEL_BORDER,
            )
            draw.rectangle((0, 0, 5, card_h), fill=(*hex_to_rgb(accent), 255))
        else:
            draw.rectangle((0, 0, 4, card_h), fill=(*hex_to_rgb(accent), 255))
        y = pad_y
        for i, ln in enumerate(title_lines):
            draw.text((pad_x, y), ln, fill=(*hex_to_rgb(accent), 255), font=title_font)
            y += title_line_h[i] + (4 if i < len(title_lines) - 1 else 0)
        y += 10
        for ri, (left, right) in enumerate(rows):
            draw.text((pad_x + 2, y), f"• {left}", fill=(230, 237, 243, 255), font=body_font)
            draw.text((pad_x + col_w + 12, y), f"• {right}", fill=(230, 237, 243, 255), font=body_font)
            y += row_h[ri] + (10 if ri < len(rows) - 1 else 0)
        return card

    title_lines = _wrap_text_lines(title, title_font, text_w)
    title_line_h = []
    for ln in title_lines:
        tb = probe.textbbox((0, 0), ln, font=title_font)
        title_line_h.append(tb[3] - tb[1])
    title_block_h = sum(title_line_h) + max(0, len(title_lines) - 1) * 4
    bullet_heights = []
    for line in bullets:
        bb = probe.textbbox((0, 0), f"• {line}", font=body_font)
        bullet_heights.append(bb[3] - bb[1])
    inner_h = (
        pad_y
        + title_block_h
        + 12
        + sum(bullet_heights)
        + line_spacing * max(0, len(bullets) - 1)
        + pad_y
    )
    card_h = height if height is not None and height > inner_h else inner_h

    card = Image.new("RGBA", (width, card_h), (*hex_to_rgb(PANEL_BG), 255))
    draw = ImageDraw.Draw(card)
    if border:
        _rounded_rect(
            draw,
            (0, 0, width - 1, card_h - 1),
            PANEL_RADIUS,
            outline=(*hex_to_rgb("#3a4558"), 255),
            width=PANEL_BORDER,
        )
        draw.rectangle((0, 0, 5, card_h), fill=(*hex_to_rgb(accent), 255))
    else:
        draw.rectangle((0, 0, 4, card_h), fill=(*hex_to_rgb(accent), 255))
    y = pad_y
    for i, ln in enumerate(title_lines):
        draw.text((pad_x, y), ln, fill=(*hex_to_rgb(accent), 255), font=title_font)
        y += title_line_h[i] + (4 if i < len(title_lines) - 1 else 0)
    y += 12
    for i, line in enumerate(bullets):
        draw.text((pad_x + 4, y), f"• {line}", fill=(230, 237, 243, 255), font=body_font)
        y += bullet_heights[i] + (line_spacing if i < len(bullets) - 1 else 0)
    return card


def center_crop_box(w: int, h: int, crop_ratio: float) -> tuple[int, int, int, int]:
    """Center square crop box (x1, y1, x2, y2) — matches render_inset_panel."""
    cx, cy = w // 2, h // 2
    half = int(min(w, h) * crop_ratio)
    return (max(0, cx - half), max(0, cy - half), min(w, cx + half), min(h, cy + half))


def estimate_inline_header_h(
    label: str | None,
    subtitle: str | None,
    *,
    corner_font_size: int,
    label_font_size: int,
    subtitle_font_size: int,
) -> int:
    """Match wrap_panel inline header height."""
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    letter_font = load_ui_font(corner_font_size, bold=True)
    title_font = load_ui_font(label_font_size, bold=True)
    sub_font = load_ui_font(subtitle_font_size) if subtitle else None
    badge_h = int(corner_font_size * 1.55)
    title_h = 0
    if label:
        tb = probe.textbbox((0, 0), label, font=title_font)
        title_h = tb[3] - tb[1]
    row_h = max(badge_h, title_h) + 14
    sub_h = 0
    if subtitle and sub_font:
        sb = probe.textbbox((0, 0), subtitle, font=sub_font)
        sub_h = (sb[3] - sb[1]) + 10
    return row_h + sub_h


def draw_zoom_crop_marker(
    img: Image.Image,
    rect: tuple[int, int, int, int],
    accent: str,
    *,
    line_w: int = 2,
) -> Image.Image:
    """Draw transparent zoom region — outline only, no fill."""
    out = img.convert("RGBA").copy()
    draw = ImageDraw.Draw(out)
    ac = hex_to_rgb(accent)
    _rounded_rect(draw, rect, 6, outline=(*ac, 235), width=line_w)
    return out


def draw_zoom_connector_lines(
    draw: ImageDraw.ImageDraw,
    src_box: tuple[int, int, int, int],
    dst_box: tuple[int, int, int, int],
    accent: str,
    *,
    line_w: int = 2,
) -> None:
    """Connect source crop box corners to inset content corners (zoom funnel)."""
    sx1, sy1, sx2, sy2 = src_box
    dx1, dy1, dx2, dy2 = dst_box
    src_pts = ((sx1, sy1), (sx2, sy1), (sx2, sy2), (sx1, sy2))
    dst_pts = ((dx1, dy1), (dx2, dy1), (dx2, dy2), (dx1, dy2))
    ac = hex_to_rgb(accent)
    shadow = (0, 0, 0, 90)
    for src, dst in zip(src_pts, dst_pts):
        draw.line([src, dst], fill=shadow, width=line_w + 2)
    for src, dst in zip(src_pts, dst_pts):
        draw.line([src, dst], fill=(*ac, 215), width=line_w)
    r = 3
    for pt in src_pts + dst_pts:
        x, y = pt
        draw.ellipse((x - r, y - r, x + r, y + r), fill=(*ac, 240), outline=(255, 255, 255, 180))


def render_inset_panel(
    img: Image.Image | Path | str,
    *,
    label: str = "局部放大",
    subtitle: str | None = None,
    accent: str = THEME["cyan"],
    crop_ratio: float = 0.2,
    content_height: int | None = None,
    header: Literal["bottom", "inline"] = "inline",
    corner_letter: str | None = None,
    label_font_size: int = 26,
    subtitle_font_size: int = 18,
    corner_font_size: int = 28,
) -> Image.Image:
    """Center crop inset wrapped as panel."""
    if isinstance(img, (Path, str)):
        source = _load_rgba(img)
    else:
        source = img.convert("RGBA")
    w, h = source.size
    crop = source.crop(center_crop_box(w, h, crop_ratio))
    return wrap_panel(
        crop,
        label=label,
        subtitle=subtitle,
        accent=accent,
        content_height=content_height,
        header=header,
        corner_letter=corner_letter,
        label_font_size=label_font_size,
        subtitle_font_size=subtitle_font_size,
        corner_font_size=corner_font_size,
    )


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
    title_font_size: int = 36,
    subtitle_font_size: int = 22,
    title_pad_y: int = 28,
    title_pad_x: int = 24,
    title_subtitle_gap: int = 20,
    title_align: Literal["left", "center"] = "left",
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
    banner = render_text_banner(
        lines,
        row.width,
        bg=bg,
        align=title_align,
        title_font_size=title_font_size,
        subtitle_font_size=subtitle_font_size,
        pad_y=title_pad_y,
        pad_x=title_pad_x,
        title_subtitle_gap=title_subtitle_gap,
    )
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


def style_axes(ax, *, labelsize: int = 11) -> None:
    ax.set_facecolor(PANEL_BG)
    ax.grid(True, alpha=GRID_ALPHA)
    ax.tick_params(colors=THEME["muted"], labelsize=labelsize)
    if hasattr(ax, "xaxis") and ax.xaxis.label:
        ax.xaxis.label.set_color(THEME["muted"])
        ax.xaxis.label.set_size(labelsize + 1)
    if hasattr(ax, "yaxis") and ax.yaxis.label:
        ax.yaxis.label.set_color(THEME["muted"])
        ax.yaxis.label.set_size(labelsize + 1)
    for spine in ax.spines.values():
        spine.set_edgecolor((78 / 255, 196 / 255, 255 / 255, 0.22))


def set_tick_density(ax, *, factor: float = 2.5, axes: str = "xy") -> None:
    """Major tick interval ÷ factor (finer scale); label size unchanged."""
    from matplotlib.ticker import LogLocator, MaxNLocator, MultipleLocator

    for name in axes:
        if name not in "xyz":
            continue
        if name == "z" and not hasattr(ax, "zaxis"):
            continue
        axis = ax.xaxis if name == "x" else (ax.yaxis if name == "y" else ax.zaxis)
        if axis.get_scale() == "log":
            axis.set_major_locator(LogLocator(base=10, numticks=max(12, int(5 * factor))))
            axis.set_minor_locator(LogLocator(base=10, subs=tuple(range(2, 10))))
            continue
        lim = getattr(ax, f"get_{name}lim")()
        span = lim[1] - lim[0]
        if span <= 0:
            continue
        ticks = axis.get_majorticklocs()
        if len(ticks) >= 2:
            step = float(abs(ticks[1] - ticks[0]))
            if step > 0:
                axis.set_major_locator(MultipleLocator(step / factor))
                continue
        axis.set_major_locator(MaxNLocator(nbins=int(5 * factor), min_n_ticks=3))


def save_figure(
    fig: Figure,
    path: Path | str,
    *,
    has_suptitle: bool = False,
    pad: float = 0.14,
    dpi: int | None = None,
    skip_tight: bool = False,
) -> None:
    """Save with bbox_inches=tight so titles and suptitles are not clipped."""
    if not skip_tight:
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


def fit_panel_contain(
    img: Image.Image,
    max_w: int,
    max_h: int,
    *,
    bg: str = VIZ_BG,
    valign: Literal["top", "center"] = "top",
    allow_upscale: bool = False,
) -> Image.Image:
    """Scale to fit cell (preserve aspect), pad to exact size — top-aligned."""
    ratio = min(max_w / img.width, max_h / img.height)
    if not allow_upscale:
        ratio = min(ratio, 1.0)
    if ratio < 1.0:
        scaled = img.resize(
            (max(1, int(img.width * ratio)), max(1, int(img.height * ratio))),
            Image.Resampling.LANCZOS,
        )
    else:
        scaled = img
    bg_rgb = hex_to_rgb(bg)
    canvas = Image.new("RGBA", (max_w, max_h), (*bg_rgb, 255))
    x = (max_w - scaled.width) // 2
    if valign == "top":
        y = 0
    else:
        y = (max_h - scaled.height) // 2
    canvas.paste(scaled.convert("RGBA"), (x, y), scaled.convert("RGBA"))
    return canvas


def pad_panel_to_height(img: Image.Image, height: int, *, bg: str = VIZ_BG) -> Image.Image:
    """Pad panel bottom with background — avoids scaling text/KPI cards."""
    if img.height >= height:
        return img
    canvas = Image.new("RGBA", (img.width, height), (*hex_to_rgb(bg), 255))
    canvas.paste(img.convert("RGBA"), (0, 0), img)
    return canvas


def fit_panel_height(img: Image.Image, height: int) -> Image.Image:
    """Scale panel to exact height (up or down), preserving aspect."""
    if img.height == height:
        return img
    ratio = height / img.height
    return img.resize((max(1, int(img.width * ratio)), height), Image.Resampling.LANCZOS)


def fit_panel_width(img: Image.Image, width: int) -> Image.Image:
    """Scale panel to exact width, preserving aspect ratio."""
    if img.width == width:
        return img
    ratio = width / img.width
    return img.resize((width, max(1, int(img.height * ratio))), Image.Resampling.LANCZOS)


def fit_panel_size(img: Image.Image, width: int, height: int) -> Image.Image:
    """Scale panel to exact width × height."""
    if img.size == (width, height):
        return img
    return img.resize((width, height), Image.Resampling.LANCZOS)


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


def stitch_panels_flow(
    panels: list[Image.Image],
    *,
    gap: int = 12,
    arrow_w: int = 44,
    bg: str = VIZ_BG,
    arrow_color: str = THEME["gold"],
    uniform_height: int | None = None,
) -> Image.Image:
    """Horizontal stitch with arrow connectors between panels."""
    if not panels:
        raise ValueError("stitch_panels_flow: no panels")
    if len(panels) == 1:
        return panels[0].convert("RGBA")

    if uniform_height:
        panels = [fit_panel_height(p.convert("RGBA"), uniform_height) for p in panels]
    else:
        panels = [p.convert("RGBA") for p in panels]
        row_h = max(p.height for p in panels)
        panels = [fit_panel_height(p, row_h) for p in panels]

    bg_rgb = hex_to_rgb(bg)
    ac = hex_to_rgb(arrow_color)
    row_h = panels[0].height
    n_arrows = len(panels) - 1
    total_w = sum(p.width for p in panels) + gap * n_arrows + arrow_w * n_arrows
    canvas = Image.new("RGBA", (total_w, row_h), (*bg_rgb, 255))
    draw = ImageDraw.Draw(canvas)
    x = 0
    for i, p in enumerate(panels):
        canvas.paste(p, (x, (row_h - p.height) // 2), p)
        x += p.width + gap
        if i < n_arrows:
            cy = row_h // 2
            x0, x1 = x + 4, x + arrow_w - 12
            draw.line([(x0, cy), (x1, cy)], fill=(*ac, 210), width=3)
            draw.polygon(
                [(x + arrow_w - 10, cy), (x + arrow_w - 26, cy - 10), (x + arrow_w - 26, cy + 10)],
                fill=(*ac, 210),
            )
            x += arrow_w
    return canvas


def flow_connector_vertical(
    width: int,
    *,
    height: int = 48,
    bg: str = VIZ_BG,
    arrow_color: str = THEME["gold"],
) -> Image.Image:
    """Downward flow arrow centered in width."""
    bg_rgb = hex_to_rgb(bg)
    ac = hex_to_rgb(arrow_color)
    canvas = Image.new("RGBA", (width, height), (*bg_rgb, 255))
    draw = ImageDraw.Draw(canvas)
    cx = width // 2
    draw.line([(cx, 6), (cx, height - 18)], fill=(*ac, 200), width=2)
    draw.polygon(
        [(cx, height - 8), (cx - 10, height - 22), (cx + 10, height - 22)],
        fill=(*ac, 200),
    )
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
    title_font_size: int = 36,
    subtitle_font_size: int = 22,
    title_subtitle_gap: int = 20,
) -> Image.Image:
    title_font = load_ui_font(title_font_size, bold=True)
    sub_font = load_ui_font(subtitle_font_size)
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    block_heights: list[int] = []
    for i, line in enumerate(lines):
        font = title_font if i == 0 else sub_font
        bb = probe.textbbox((0, 0), line, font=font)
        block_heights.append(bb[3] - bb[1])
    inner_h = block_heights[0]
    if len(lines) > 1:
        inner_h += title_subtitle_gap + sum(block_heights[1:])
    ascent_pad = max(4, title_font_size // 10)
    height = pad_y * 2 + inner_h + ascent_pad
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
        bb = probe.textbbox((0, 0), line, font=font)
        draw.text((x, y - bb[1]), line, fill=(*rgb, 255), font=font)
        if i == 0 and len(lines) > 1:
            y += block_heights[i] + title_subtitle_gap
        else:
            y += block_heights[i]
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
    font_size: int = 14,
    badge_h: int | None = None,
    gap: int = 12,
) -> Image.Image:
    """Vertical metadata badge column for hero poster."""
    badge_h = badge_h or (font_size + 36)
    height = len(lines) * badge_h + gap * (len(lines) - 1)
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = load_ui_font(font_size, bold=True)
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
        draw.text(
            ((width - tw) / 2, y + (badge_h - font_size) // 2 - 2),
            line,
            fill=(*hex_to_rgb(accent), 255),
            font=font,
        )
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
