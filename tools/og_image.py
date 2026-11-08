#!/usr/bin/env python3
"""Render 1200x630 social cards for the AIDDHub notes.

Called from tools/build_site.py.  Requires Pillow; if it is missing the build
still succeeds and the pages simply omit og:image.
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1200, 630
BG = (7, 11, 20)
TEXT = (232, 238, 248)
DIM = (159, 176, 201)
FAINT = (125, 142, 169)
ACCENT = (77, 158, 247)
ACCENT2 = (52, 229, 196)
ACCENT3 = (160, 107, 255)

FONT_BOLD = {
    "en": Path(r"C:\Windows\Fonts\segoeuib.ttf"),
    "zh": Path(r"C:\Windows\Fonts\msyhbd.ttc"),
}
FONT_REG = {
    "en": Path(r"C:\Windows\Fonts\segoeui.ttf"),
    "zh": Path(r"C:\Windows\Fonts\msyh.ttc"),
}


def _font(path: Path, size: int) -> ImageFont.FreeTypeFont:
    """Load a font, or raise. Missing fonts must not silently produce ugly cards."""
    if not path.exists():
        raise FileNotFoundError(path)
    return ImageFont.truetype(str(path), size)


def _glow(base: Image.Image, center: tuple[int, int], radius: int, color: tuple[int, int, int], alpha: int) -> None:
    layer = Image.new("RGBA", (radius * 2, radius * 2), (0, 0, 0, 0))
    draw = ImageDraw.Draw(layer)
    steps = 26
    for i in range(steps, 0, -1):
        r = radius * i / steps
        a = int(alpha * (1 - i / steps) ** 1.7)
        draw.ellipse([radius - r, radius - r, radius + r, radius + r], fill=color + (a,))
    layer = layer.filter(ImageFilter.GaussianBlur(radius / 5))
    base.alpha_composite(layer, (center[0] - radius, center[1] - radius))


def _wrap(text: str, font: ImageFont.FreeTypeFont, limit: int, draw: ImageDraw.ImageDraw) -> list[str]:
    if " " not in text:
        lines, current = [], ""
        for char in text:
            probe = current + char
            if draw.textlength(probe, font=font) > limit and current:
                lines.append(current)
                current = char
            else:
                current = probe
        if current:
            lines.append(current)
        return lines

    words, lines, current = text.split(), [], ""
    for word in words:
        probe = (current + " " + word).strip()
        if draw.textlength(probe, font=font) > limit and current:
            lines.append(current)
            current = word
        else:
            current = probe
    if current:
        lines.append(current)
    return lines


def _badge(draw: ImageDraw.ImageDraw, xy: tuple[int, int], label: str, lang: str) -> int:
    font = _font(FONT_BOLD[lang], 19)
    text = label.upper() if lang == "en" else label
    width = int(draw.textlength(text, font=font)) + 6
    x, y = xy
    draw.rounded_rectangle([x, y, x + width + 34, y + 40], radius=20,
                           fill=(16, 25, 44), outline=(58, 110, 180), width=1)
    draw.text((x + 17, y + 9), text, font=font, fill=(127, 196, 255))
    return int(x + width + 34)


def _mark(draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    scale = size / 30.0
    top = (x + 15 * scale, y + 3 * scale)
    bl = (x + 5 * scale, y + 24 * scale)
    br = (x + 25 * scale, y + 24 * scale)
    r = 3.4 * scale
    for cx, cy in (top, bl, br):
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ACCENT2, width=max(2, int(2.2 * scale)))
    draw.line([top[0], top[1] + r, top[0] + 1 * scale, top[1] + 7 * scale], fill=ACCENT, width=max(2, int(2.2 * scale)))
    draw.line([top[0] - 2 * scale, top[1] + 9 * scale, bl[0] + r, bl[1] - r], fill=ACCENT, width=max(2, int(2.2 * scale)))
    draw.line([top[0] + 2 * scale, top[1] + 9 * scale, br[0] - r, br[1] - r], fill=ACCENT, width=max(2, int(2.2 * scale)))


ICON = Path(__file__).resolve().parent.parent / "assets" / "img" / "avatar-icon.png"


def _brand(image: Image.Image, draw: ImageDraw.ImageDraw, x: int, y: int, size: int) -> None:
    """Paste the site icon when it is available, otherwise draw the vector fallback."""
    if ICON.exists():
        try:
            logo = Image.open(ICON).convert("RGBA").resize((size, size), Image.LANCZOS)
            image.alpha_composite(logo, (x, y))
            return
        except Exception:
            pass
    _mark(draw, x, y, size)


def render(*, title: str, label: str, footer: str, lang: str, out: Path) -> None:
    image = Image.new("RGBA", (W, H), BG + (255,))
    _glow(image, (170, -40), 520, ACCENT, 90)
    _glow(image, (1090, 30), 460, ACCENT3, 70)
    _glow(image, (760, 690), 480, ACCENT2, 55)

    draw = ImageDraw.Draw(image)

    # faint grid, composited so the alpha is respected
    grid = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(grid)
    for x in range(0, W, 48):
        gdraw.line([(x, 0), (x, H)], fill=(120, 160, 220, 14))
    for y in range(0, H, 48):
        gdraw.line([(0, y), (W, y)], fill=(120, 160, 220, 14))
    image.alpha_composite(grid)

    _brand(image, draw, 80, 70, 34)
    brand = _font(FONT_BOLD[lang], 27)
    draw.text((128, 70), "AIDDHub", font=brand, fill=TEXT)

    date_font = _font(FONT_REG[lang], 19)
    if label:
        end = _badge(draw, (80, 168), label, lang)
        if footer:
            draw.text((end + 16, 178), footer, font=date_font, fill=FAINT)
    elif footer:
        draw.text((80, 178), footer, font=date_font, fill=FAINT)

    size = 56 if lang == "en" else 54
    title_font = _font(FONT_BOLD[lang], size)
    lines = _wrap(title, title_font, 1030, draw)
    while len(lines) > 4 and size > 38:
        size -= 4
        title_font = _font(FONT_BOLD[lang], size)
        lines = _wrap(title, title_font, 1030, draw)

    y = 250
    for line in lines[:4]:
        draw.text((80, y), line, font=title_font, fill=TEXT)
        y += int(size * 1.28)

    rule = Image.new("RGBA", (W - 160, 1), (120, 160, 220, 60))
    image.alpha_composite(rule, (80, 520))

    foot_font = _font(FONT_REG[lang], 21)
    draw.text((80, 545), "aiddhub.github.io", font=foot_font, fill=DIM)

    out.parent.mkdir(parents=True, exist_ok=True)
    payload = image.convert("RGB")
    out.write_bytes(b"")  # ensure the file can be replaced
    payload.save(out, "PNG", optimize=True)
