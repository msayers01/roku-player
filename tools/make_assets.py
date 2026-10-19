"""Generate the committed image assets (placeholder poster, Roku icons, splash).

Requires Pillow: ``pip install pillow``. Run from the repository root:
    python tools/make_assets.py
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

REPO = Path(__file__).resolve().parent.parent
BG = (14, 17, 22)
PANEL = (32, 38, 51)
MUTED = (154, 163, 178)
TEXT = (242, 244, 248)
ACCENT = (79, 195, 176)

FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/inter/Inter-Bold.otf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "C:/Windows/Fonts/segoeuib.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def font(size: int) -> ImageFont.FreeTypeFont:
    for candidate in FONT_CANDIDATES:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default(size)


def film_icon(draw: ImageDraw.ImageDraw, cx: int, cy: int, w: int, colour) -> None:
    h = int(w * 0.7)
    x0, y0 = cx - w // 2, cy - h // 2
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=w // 12, outline=colour, width=max(3, w // 30))
    hole = w // 10
    for i in range(5):
        x = x0 + w // 12 + i * (w - w // 6) // 4
        draw.rectangle([x, y0 + hole // 2, x + hole // 2, y0 + hole], fill=colour)
        draw.rectangle([x, y0 + h - hole, x + hole // 2, y0 + h - hole // 2], fill=colour)
    draw.polygon([(cx - w // 10, cy - w // 8), (cx - w // 10, cy + w // 8), (cx + w // 7, cy)], fill=colour)


def centered(draw, y, text, size, fill, width):
    f = font(size)
    tw = draw.textlength(text, font=f)
    draw.text(((width - tw) / 2, y), text, font=f, fill=fill)


def placeholder_poster(path: Path) -> None:
    w, h = 400, 600
    img = Image.new("RGB", (w, h), PANEL)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = y / h
        draw.line([(0, y), (w, y)], fill=tuple(int(PANEL[i] * (1 - t) + BG[i] * t) for i in range(3)))
    film_icon(draw, w // 2, h // 2 - 40, 150, MUTED)
    centered(draw, h // 2 + 60, "No poster", 34, MUTED, w)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def brand(size: tuple[int, int], path: Path, title_size: int, sub: str | None = None) -> None:
    w, h = size
    img = Image.new("RGB", size, BG)
    draw = ImageDraw.Draw(img)
    icon_w = int(h * 0.42)
    film_icon(draw, w // 2, int(h * 0.38), icon_w, ACCENT)
    centered(draw, int(h * 0.62), "LAN Media", title_size, TEXT, w)
    if sub:
        centered(draw, int(h * 0.62) + int(title_size * 1.4), sub, title_size // 2, MUTED, w)
    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, optimize=True)


def main() -> None:
    placeholder_poster(REPO / "windows-server/app/static/placeholder_poster.png")
    placeholder_poster(REPO / "roku-client/images/placeholder_poster.png")
    images = REPO / "roku-client/images"
    brand((336, 210), images / "icon_focus_hd.png", 40)
    brand((248, 140), images / "icon_focus_sd.png", 28)
    brand((1920, 1080), images / "splash_fhd.png", 96, "Movies from your PC")
    brand((1280, 720), images / "splash_hd.png", 64, "Movies from your PC")


if __name__ == "__main__":
    main()
