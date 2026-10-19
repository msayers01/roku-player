"""Locate sidecar poster images next to a video file."""

from __future__ import annotations

from pathlib import Path

POSTER_EXTENSIONS = (".jpg", ".jpeg", ".png")
FOLDER_POSTER_STEMS = ("poster", "folder", "cover")
PLACEHOLDER = Path(__file__).resolve().parent.parent / "static" / "placeholder_poster.png"


def find_poster(video: Path, videos_in_dir: int) -> Path | None:
    """Prefer ``<stem>.jpg`` / ``<stem>-poster.jpg``; fall back to ``poster.jpg``
    only when the folder holds a single video, so one poster is never shared
    across several titles."""
    directory, stem = video.parent, video.stem
    candidates = [f"{stem}{ext}" for ext in POSTER_EXTENSIONS]
    candidates += [f"{stem}-poster{ext}" for ext in POSTER_EXTENSIONS]
    if videos_in_dir == 1:
        candidates += [f"{s}{ext}" for s in FOLDER_POSTER_STEMS for ext in POSTER_EXTENSIONS]

    existing = {p.name.lower(): p for p in directory.iterdir() if p.is_file()}
    for name in candidates:
        match = existing.get(name.lower())
        if match is not None:
            return match
    return None


def media_type_for(path: Path) -> str:
    return "image/png" if path.suffix.lower() == ".png" else "image/jpeg"
