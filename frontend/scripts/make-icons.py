"""Generate the PWA / install icons from the brand colours.

Android and iOS do not accept an SVG for the install icon, so the manifest needs real PNGs
at 192 and 512 pixels, plus a maskable variant that survives being cropped to a circle.
Generating them here keeps the shield glyph and the brand palette in one place instead of
committing opaque binaries nobody can adjust later.

Usage (from the frontend directory):

    ../backend/.venv/Scripts/python.exe scripts/make-icons.py

Needs Pillow, which arrives with the backend requirements (as a reportlab dependency).
"""

from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).resolve().parent.parent / "public"

BRAND = (30, 58, 95)  # #1e3a5f — deep indigo, matches tailwind brand-800 / manifest theme_color
ACCENT = (45, 212, 191)  # #2dd4bf — teal accent, matches tailwind accent-400
WHITE = (255, 255, 255)

SUPERSAMPLE = 4  # draw large, then downsample: cheap anti-aliasing without a vector engine


def shield_mask(size: int, scale: float, center: bool = True) -> Image.Image:
    """A rounded-shoulder shield with a point at the bottom, as an 8-bit mask."""
    canvas = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(canvas)

    glyph = size * scale
    ox = (size - glyph) / 2 if center else 0.0
    oy = (size - glyph) / 2 if center else 0.0

    def px(rx: float, ry: float) -> tuple[float, float]:
        return (ox + glyph * rx, oy + glyph * ry)

    # Shoulders: a rounded rectangle supplies the top corners and the straight sides.
    draw.rounded_rectangle(
        [px(0.06, 0.04), px(0.94, 0.66)],
        radius=int(glyph * 0.16),
        fill=255,
    )
    # Bottom: a triangle closes the shield to a point.
    draw.polygon([px(0.06, 0.40), px(0.94, 0.40), px(0.50, 0.99)], fill=255)
    return canvas


def check_mask(size: int, scale: float) -> Image.Image:
    """The tick inside the shield."""
    canvas = Image.new("L", (size, size), 0)
    draw = ImageDraw.Draw(canvas)

    glyph = size * scale
    ox = (size - glyph) / 2
    oy = (size - glyph) / 2

    def px(rx: float, ry: float) -> tuple[float, float]:
        return (ox + glyph * rx, oy + glyph * ry)

    draw.line(
        [px(0.28, 0.50), px(0.43, 0.64), px(0.72, 0.33)],
        fill=255,
        width=max(1, int(glyph * 0.085)),
        joint="curve",
    )
    # Square off the stroke ends so the tick does not taper.
    for rx, ry in ((0.28, 0.50), (0.72, 0.33)):
        r = glyph * 0.0425
        cx, cy = px(rx, ry)
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=255)
    return canvas


def build(size: int, *, maskable: bool) -> Image.Image:
    """Render one icon. Maskable icons keep the glyph inside the safe zone."""
    big = size * SUPERSAMPLE

    if maskable:
        # Full-bleed background; Android may crop this to a circle or a squircle.
        background = Image.new("RGB", (big, big), BRAND)
        glyph = shield_mask(big, scale=0.56)
        colour = WHITE
    else:
        # Transparent corners so the icon looks intentional in a browser tab.
        background = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        plate = Image.new("RGBA", (big, big), (0, 0, 0, 0))
        ImageDraw.Draw(plate).rounded_rectangle(
            [0, 0, big - 1, big - 1], radius=int(big * 0.22), fill=BRAND + (255,)
        )
        background = plate
        glyph = shield_mask(big, scale=0.66)
        colour = WHITE

    background.paste(colour + (255,) if background.mode == "RGBA" else colour, (0, 0), glyph)

    tick = check_mask(big, scale=0.56 if maskable else 0.66)
    layer = Image.new("RGBA", (big, big), ACCENT + (255,))
    background.paste(layer, (0, 0), tick)

    return background.resize((size, size), Image.LANCZOS)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    outputs = [
        ("icon-192.png", 192, False),
        ("icon-512.png", 512, False),
        ("icon-maskable-192.png", 192, True),
        ("icon-maskable-512.png", 512, True),
        ("apple-touch-icon.png", 180, True),
    ]

    for name, size, maskable in outputs:
        image = build(size, maskable=maskable)
        # apple-touch-icon must be opaque: iOS composites it on white otherwise.
        if name == "apple-touch-icon.png":
            flat = Image.new("RGB", image.size, BRAND)
            flat.paste(image, (0, 0), image if image.mode == "RGBA" else None)
            image = flat
        image.save(OUT_DIR / name, "PNG", optimize=True)
        print(f"  wrote {name}  ({size}x{size}{', maskable' if maskable else ''})")

    print(f"\n{len(outputs)} icons written to {OUT_DIR}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
