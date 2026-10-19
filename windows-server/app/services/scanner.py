"""Walk the approved media roots and build catalog records."""

from __future__ import annotations

import hashlib
import logging
import os
from dataclasses import dataclass
from pathlib import Path

from app.config import Config, MediaRoot
from app.database import MediaRecord
from app.services import artwork, metadata
from app.services.paths import resolve_inside

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class ScanReport:
    records: list[MediaRecord]
    skipped: int
    missing_roots: list[str]
    probed: bool


def media_id(root_name: str, rel_path: str) -> str:
    """Stable ID derived from root name + relative path (survives rescans)."""
    digest = hashlib.sha1(f"{root_name}/{rel_path}".encode("utf-8")).hexdigest()
    return f"m{digest[:12]}"


def scan(config: Config) -> ScanReport:
    ffprobe = metadata.find_ffprobe(config.ffprobe_path)
    if config.ffprobe_path and not ffprobe:
        log.warning("ffprobe not found (%s); codecs will not be verified", config.ffprobe_path)

    records: list[MediaRecord] = []
    skipped = 0
    missing_roots = []
    for root in config.media_roots:
        if not root.path.is_dir():
            log.warning("Media root '%s' is not a folder: %s", root.name, root.path)
            missing_roots.append(root.name)
            continue
        found, root_skipped = _scan_root(root, config, ffprobe)
        records.extend(found)
        skipped += root_skipped

    records.sort(key=lambda r: (r.sort_title, r.year or 0, r.id))
    return ScanReport(records=records, skipped=skipped, missing_roots=missing_roots,
                      probed=ffprobe is not None)


def _scan_root(root: MediaRoot, config: Config, ffprobe: str | None) -> tuple[list[MediaRecord], int]:
    root_real = root.path.resolve()
    records = []
    skipped = 0
    # followlinks=False: never descend into linked directories that may leave the root.
    for dirpath, dirnames, filenames in os.walk(root_real, followlinks=False):
        dirnames[:] = sorted(d for d in dirnames if not d.startswith("."))
        videos = sorted(f for f in filenames
                        if Path(f).suffix.lower() in config.allowed_extensions
                        and not f.startswith("."))
        for name in videos:
            rel = Path(dirpath, name).relative_to(root_real).as_posix()
            path = resolve_inside(root_real, rel)
            if path is None or not path.is_file():
                log.warning("Skipping file outside media root: %s", rel)
                skipped += 1
                continue
            records.append(_build_record(root, root_real, rel, path, len(videos), config, ffprobe))
    return records, skipped


def _build_record(root: MediaRoot, root_real: Path, rel: str, path: Path, videos_in_dir: int,
                  config: Config, ffprobe: str | None) -> MediaRecord:
    title, year = metadata.parse_title(Path(rel).stem)

    poster_rel = None
    poster = artwork.find_poster(Path(root_real, rel), videos_in_dir)
    if poster is not None:
        candidate_rel = poster.relative_to(root_real).as_posix()
        if resolve_inside(root_real, candidate_rel) is not None:
            poster_rel = candidate_rel

    probe = metadata.probe(path, ffprobe) if ffprobe else None
    if probe is not None:
        playable, note = metadata.assess_direct_play(probe, config.direct_play)
    elif ffprobe is None:
        # Without ffprobe we can only trust the extension; say so to the user.
        probe = metadata.ProbeResult(None, "mp4", None, None, None, None)
        playable, note = True, "Codecs not verified (ffprobe unavailable)"
    else:
        probe = metadata.ProbeResult(None, None, None, None, None, None)
        playable, note = False, "Could not read media info (file may be damaged)"

    return MediaRecord(
        id=media_id(root.name, rel),
        root_name=root.name,
        rel_path=rel,
        poster_rel_path=poster_rel,
        title=title,
        sort_title=metadata.sort_key(title),
        year=year,
        duration_seconds=probe.duration_seconds,
        container=probe.container,
        video_codec=probe.video_codec,
        audio_codec=probe.audio_codec,
        width=probe.width,
        height=probe.height,
        size_bytes=path.stat().st_size,
        probed=ffprobe is not None and probe.video_codec is not None,
        playable=playable,
        compat_note=note,
    )
