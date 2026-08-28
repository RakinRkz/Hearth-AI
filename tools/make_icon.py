"""Generate assets/hearth.ico - the app, tray and installer icon.

Kept as a script rather than a hand-drawn binary so the icon can be tweaked and
regenerated: python tools/make_icon.py
"""

import math
from pathlib import Path
from PIL import Image, ImageDraw

SIZES = [16, 32, 48, 64, 128, 256]
OUT = Path(__file__).resolve().parent.parent / "assets" / "hearth.ico"
PNG = OUT.with_suffix(".png")

BG = (24, 24, 27, 255)        # zinc-900, matches the app's dark UI
OUTER = (234, 88, 12, 255)    # orange-600
MID = (249, 115, 22, 255)     # orange-500
INNER = (253, 186, 116, 255)  # orange-300


def flame_points(cx, top, height, half_width, lean, steps=120):
    """Outline of a flame: curved tapering tip, bulging belly, round base.

    Width follows 1-(1-t)^2 so it starts at a point and swells downward; the
    base is closed with a semicircle. `lean` bends the tip sideways so the
    shape reads as fire rather than as a symmetric leaf.
    """
    left, right = [], []
    for i in range(steps + 1):
        t = i / steps
        # t**1.25 keeps the tip genuinely sharp; the sine term adds the belly
        w = half_width * (t ** 1.25) * (1.0 + 0.45 * math.sin(math.pi * t))
        # tip curls to one side, belly returns to centre
        bend = lean * math.sin(math.pi * t ** 1.6) * (1.0 - t) ** 0.4
        x = cx + bend
        y = top + height * t
        left.append((x - w, y))
        right.append((x + w, y))

    # close the bottom with a semicircle between the last left/right points
    bx = (left[-1][0] + right[-1][0]) / 2.0
    by = left[-1][1]
    r = (right[-1][0] - left[-1][0]) / 2.0
    base = [
        (bx + r * math.cos(a), by + r * math.sin(a) * 0.85)
        for a in [math.pi * k / 24 for k in range(25)]
    ]
    return right + base + left[::-1]


def render(size: int) -> Image.Image:
    # 4x supersample, then downscale, so the curves stay smooth at 16px
    s = size * 4
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    d.rounded_rectangle([0, 0, s - 1, s - 1], radius=int(s * 0.22), fill=BG)

    d.polygon(flame_points(s * 0.50, s * 0.10, s * 0.74, s * 0.29, s * 0.13), fill=OUTER)
    d.polygon(flame_points(s * 0.51, s * 0.28, s * 0.56, s * 0.19, s * 0.09), fill=MID)
    d.polygon(flame_points(s * 0.51, s * 0.50, s * 0.34, s * 0.105, s * 0.05), fill=INNER)

    return img.resize((size, size), Image.LANCZOS)


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    images = [render(n) for n in SIZES]
    images[-1].save(OUT, format="ICO", sizes=[(n, n) for n in SIZES])
    images[-1].save(PNG, format="PNG")
    print(f"wrote {OUT} ({', '.join(str(n) for n in SIZES)})")


if __name__ == "__main__":
    main()
