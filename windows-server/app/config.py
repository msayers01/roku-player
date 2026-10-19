"""Server configuration loaded from config.json."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class MediaRoot:
    name: str
    path: Path


@dataclass(frozen=True)
class DirectPlayProfile:
    """Conservative allowlist of what the Roku is expected to direct-play."""

    containers: tuple[str, ...] = ("mp4",)
    video_codecs: tuple[str, ...] = ("h264",)
    audio_codecs: tuple[str, ...] = ("aac",)


@dataclass(frozen=True)
class Config:
    media_roots: tuple[MediaRoot, ...]
    bind_address: str = "0.0.0.0"
    port: int = 8080
    database_path: Path = Path("catalog.db")
    ffprobe_path: str | None = "ffprobe"
    allowed_extensions: tuple[str, ...] = (".mp4", ".m4v")
    direct_play: DirectPlayProfile = field(default_factory=DirectPlayProfile)


class ConfigError(ValueError):
    pass


def load_config(path: Path) -> Config:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ConfigError(f"Config file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Config file is not valid JSON: {exc}") from exc

    base = path.parent
    roots = []
    for entry in raw.get("media_roots", []):
        name = str(entry.get("name", "")).strip()
        root_path = str(entry.get("path", "")).strip()
        if not name or not root_path:
            raise ConfigError("Each media root needs a 'name' and a 'path'")
        roots.append(MediaRoot(name=name, path=Path(root_path)))
    if not roots:
        raise ConfigError("Config must list at least one entry in 'media_roots'")
    if len({r.name for r in roots}) != len(roots):
        raise ConfigError("Media root names must be unique")

    port = int(raw.get("port", 8080))
    if not 1 <= port <= 65535:
        raise ConfigError(f"Port out of range: {port}")

    db_path = Path(raw.get("database_path", "catalog.db"))
    if not db_path.is_absolute():
        db_path = base / db_path

    dp = raw.get("direct_play", {})
    profile = DirectPlayProfile(
        containers=tuple(c.lower() for c in dp.get("containers", DirectPlayProfile.containers)),
        video_codecs=tuple(c.lower() for c in dp.get("video_codecs", DirectPlayProfile.video_codecs)),
        audio_codecs=tuple(c.lower() for c in dp.get("audio_codecs", DirectPlayProfile.audio_codecs)),
    )

    return Config(
        media_roots=tuple(roots),
        bind_address=str(raw.get("bind_address", "0.0.0.0")),
        port=port,
        database_path=db_path,
        ffprobe_path=raw.get("ffprobe_path", "ffprobe") or None,
        allowed_extensions=tuple(e.lower() for e in raw.get("allowed_extensions", [".mp4", ".m4v"])),
        direct_play=profile,
    )
