"""Create a demo library of short test clips with sidecar posters.

Requires FFmpeg on PATH and Pillow (``pip install pillow``):
    python tools/make_sample_library.py <output-folder> [--seconds 150]

Point a media root in windows-server/config.json at the output folder. The set
includes one title without a poster (placeholder test) and one MPEG-4 Part 2
title (unsupported-format test).
"""

from __future__ import annotations

import argparse
import subprocess
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

from make_assets import font

# (title, year, top colour, bottom colour, motif, options)
TITLES = [
    ("Aurora Drift", 2021, "#0b3d5c", "#53d1b6", "sun", {}),
    ("The Copper Lantern", 2019, "#3a1c0b", "#e08a3c", "moon", {}),
    ("Midnight Orchard", 2023, "#0d0b2a", "#6b4fbb", "moon", {}),
    ("Signal Over Saltmarsh", 2018, "#1f3a3a", "#c7d6c1", "lines", {}),
    ("Paper Satellites", 2022, "#20184a", "#f06a8a", "rings", {}),
    ("The Long Way North", 2017, "#0f2433", "#a8c8e0", "peaks", {}),
    ("Glasshouse Summer", 2024, "#2e4d1f", "#f4d35e", "sun", {"no_poster": True}),
    ("Harbor Lights", 2020, "#081a2e", "#f2b544", "lines", {}),
    ("Quiet Engines", 2016, "#1c1c1c", "#9aa3b2", "rings", {}),
    ("Velvet Static", 2015, "#3b0a2a", "#d1495b", "lines", {"codec": "mpeg4"}),
    ("Tidewater", 2022, "#06323d", "#3fb6a8", "peaks", {}),
    ("Kestrel Point", 2024, "#402218", "#f3a683", "sun", {}),
]


def hex_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def poster(path: Path, title: str, year: int, top: str, bottom: str, motif: str) -> None:
    w, h = 600, 900
    a, b = hex_rgb(top), hex_rgb(bottom)
    img = Image.new("RGB", (w, h))
    draw = ImageDraw.Draw(img)
    for y in range(h):
        t = (y / h) ** 1.3
        draw.line([(0, y), (w, y)], fill=tuple(int(a[i] * (1 - t) + b[i] * t) for i in range(3)))

    glow = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    g = ImageDraw.Draw(glow)
    light = (255, 255, 255, 70)
    if motif == "sun":
        g.ellipse([w * 0.25, h * 0.22, w * 0.75, h * 0.55], fill=(255, 240, 210, 120))
    elif motif == "moon":
        g.ellipse([w * 0.5, h * 0.12, w * 0.8, h * 0.32], fill=(255, 255, 240, 150))
    elif motif == "rings":
        for r in range(60, 300, 45):
            g.ellipse([w / 2 - r, h * 0.38 - r, w / 2 + r, h * 0.38 + r], outline=light, width=4)
    elif motif == "lines":
        for i in range(14):
            y = h * 0.18 + i * 26
            g.line([(w * 0.12, y), (w * 0.88, y)], fill=(255, 255, 255, 30 + i * 8), width=3)
    elif motif == "peaks":
        g.polygon([(0, h * 0.62), (w * 0.3, h * 0.3), (w * 0.55, h * 0.55), (w * 0.75, h * 0.36),
                   (w, h * 0.6), (w, h * 0.7), (0, h * 0.7)], fill=(255, 255, 255, 60))
    img = Image.alpha_composite(img.convert("RGBA"), glow.filter(ImageFilter.GaussianBlur(2))).convert("RGB")

    draw = ImageDraw.Draw(img)
    words, lines, line = title.upper().split(), [], ""
    title_font = font(64)
    for word in words:
        trial = f"{line} {word}".strip()
        if draw.textlength(trial, font=title_font) > w - 80 and line:
            lines.append(line)
            line = word
        else:
            line = trial
    lines.append(line)
    y = h * 0.66
    for text in lines:
        tw = draw.textlength(text, font=title_font)
        draw.text(((w - tw) / 2 + 2, y + 2), text, font=title_font, fill=(0, 0, 0))
        draw.text(((w - tw) / 2, y), text, font=title_font, fill=(255, 255, 255))
        y += 74
    year_font = font(30)
    tw = draw.textlength(str(year), font=year_font)
    draw.text(((w - tw) / 2, h - 70), str(year), font=year_font, fill=(255, 255, 255))
    img.save(path, quality=88)


def clip(path: Path, title: str, top: str, bottom: str, seconds: int, codec: str) -> None:
    safe = title.replace("'", "").replace(":", "")
    vf = (
        f"drawtext=text='{safe}':fontcolor=white:fontsize=64:x=(w-tw)/2:y=h*0.38,"
        "drawtext=text='%{pts\\:hms}':fontcolor=white@0.85:fontsize=44:x=(w-tw)/2:y=h*0.55"
    )
    video_codec = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "30", "-pix_fmt", "yuv420p",
                   "-profile:v", "high", "-level", "4.0"]
    if codec == "mpeg4":
        video_codec = ["-c:v", "mpeg4", "-q:v", "8"]
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-f", "lavfi", "-i", f"gradients=s=1280x720:r=24:c0={top}:c1={bottom}:speed=0.004:d={seconds}",
         "-f", "lavfi", "-i", f"sine=frequency=220:sample_rate=48000:duration={seconds}",
         "-vf", vf, *video_codec, "-c:a", "aac", "-b:a", "96k", "-af", "volume=0.2",
         "-movflags", "+faststart", "-shortest", str(path)],
        check=True,
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    parser.add_argument("--seconds", type=int, default=150)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for title, year, top, bottom, motif, opts in TITLES:
        stem = f"{title} ({year})"
        print(f"  {stem}")
        clip(args.output / f"{stem}.mp4", title, top, bottom, args.seconds, opts.get("codec", "h264"))
        if not opts.get("no_poster"):
            poster(args.output / f"{stem}.jpg", title, year, top, bottom, motif)


if __name__ == "__main__":
    main()
