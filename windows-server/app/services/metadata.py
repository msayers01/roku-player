"""Title parsing and optional ffprobe inspection (never transcodes)."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from app.config import DirectPlayProfile

_YEAR_RE = re.compile(r"[\(\[\s._-]((?:19|20)\d{2})(?:[\)\]\s._-]|$)")
_ARTICLES = ("the ", "a ", "an ")


@dataclass(frozen=True)
class ProbeResult:
    duration_seconds: float | None
    container: str | None
    video_codec: str | None
    audio_codec: str | None
    width: int | None
    height: int | None


def parse_title(stem: str) -> tuple[str, int | None]:
    """Turn a file stem like ``The.Big_Movie (2019) 1080p`` into ("The Big Movie", 2019)."""
    year = None
    title_part = stem
    match = _YEAR_RE.search(stem)
    if match and match.start() > 0:
        year = int(match.group(1))
        title_part = stem[: match.start()]
    title = re.sub(r"[._]+", " ", title_part)
    title = re.sub(r"\s+", " ", title).strip(" -[(")
    return (title or stem), year


def sort_key(title: str) -> str:
    lowered = title.lower()
    for article in _ARTICLES:
        if lowered.startswith(article):
            return lowered[len(article):]
    return lowered


def find_ffprobe(configured: str | None) -> str | None:
    if not configured:
        return None
    return shutil.which(configured)


def probe(path: Path, ffprobe: str) -> ProbeResult | None:
    cmd = [
        ffprobe, "-v", "error", "-print_format", "json",
        "-show_format", "-show_streams", str(path),
    ]
    try:
        out = subprocess.run(cmd, capture_output=True, timeout=30, check=True).stdout
        data = json.loads(out)
    except (OSError, subprocess.SubprocessError, json.JSONDecodeError):
        return None

    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"
                  and not s.get("disposition", {}).get("attached_pic")), None)
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    fmt = data.get("format", {})
    try:
        duration = float(fmt["duration"])
    except (KeyError, TypeError, ValueError):
        duration = None

    format_names = set(fmt.get("format_name", "").split(","))
    container = "mp4" if "mp4" in format_names else (fmt.get("format_name") or None)

    return ProbeResult(
        duration_seconds=duration,
        container=container,
        video_codec=(video or {}).get("codec_name"),
        audio_codec=(audio or {}).get("codec_name"),
        width=(video or {}).get("width"),
        height=(video or {}).get("height"),
    )


def assess_direct_play(result: ProbeResult, profile: DirectPlayProfile) -> tuple[bool, str | None]:
    """Return (playable, reason). Conservative: anything outside the allowlist is rejected."""
    problems = []
    if result.container not in profile.containers:
        problems.append(f"container {result.container or 'unknown'}")
    if result.video_codec not in profile.video_codecs:
        problems.append(f"video {result.video_codec or 'missing'}")
    if result.audio_codec is not None and result.audio_codec not in profile.audio_codecs:
        problems.append(f"audio {result.audio_codec}")
    if problems:
        return False, "Not direct-play compatible: " + ", ".join(problems)
    return True, None
