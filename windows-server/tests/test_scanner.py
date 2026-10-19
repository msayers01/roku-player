from __future__ import annotations

from pathlib import Path

import pytest

from app.config import MediaRoot
from app.services.metadata import parse_title, sort_key
from app.services.scanner import scan
from tests.conftest import HAS_FFMPEG, make_clip, make_config


@pytest.mark.parametrize("stem,expected", [
    ("Aurora.Drift.(2021)", ("Aurora Drift", 2021)),
    ("The_Long_Way_North 2017 1080p", ("The Long Way North", 2017)),
    ("Movie [1999]", ("Movie", 1999)),
    ("2001 A Space Story", ("2001 A Space Story", None)),
    ("Plain Title", ("Plain Title", None)),
])
def test_parse_title(stem, expected):
    assert parse_title(stem) == expected


def test_sort_key_ignores_leading_article():
    assert sort_key("The Zebra") == "zebra"
    assert sort_key("An Apple") == "apple"
    assert sort_key("Theory") == "theory"


def test_folder_poster_only_used_for_single_video_folders(tmp_path: Path):
    root = tmp_path / "root"
    (root / "Solo").mkdir(parents=True)
    (root / "Solo" / "Solo (2020).mp4").write_bytes(b"x")
    (root / "Solo" / "poster.jpg").write_bytes(b"p")
    (root / "Pair").mkdir()
    (root / "Pair" / "One (2020).mp4").write_bytes(b"x")
    (root / "Pair" / "Two (2020).mp4").write_bytes(b"x")
    (root / "Pair" / "poster.jpg").write_bytes(b"p")

    records = {r.title: r for r in scan(make_config([MediaRoot("M", root)], tmp_path)).records}
    assert records["Solo"].poster_rel_path == "Solo/poster.jpg"
    assert records["One"].poster_rel_path is None
    assert records["Two"].poster_rel_path is None


def test_missing_root_is_reported(tmp_path: Path):
    report = scan(make_config([MediaRoot("Gone", tmp_path / "nope")], tmp_path))
    assert report.records == []
    assert report.missing_roots == ["Gone"]


@pytest.mark.skipif(not HAS_FFMPEG, reason="ffmpeg/ffprobe not installed")
def test_ffprobe_flags_direct_play_compatibility(tmp_path: Path):
    root = tmp_path / "root"
    make_clip(root / "Good (2020).mp4", "libx264")
    make_clip(root / "Old Codec (2010).mp4", "mpeg4")
    (root / "Broken (2000).mp4").write_bytes(b"not really an mp4")

    records = {r.title: r for r in scan(make_config([MediaRoot("M", root)], tmp_path, "ffprobe")).records}
    good = records["Good"]
    assert (good.playable, good.video_codec, good.audio_codec, good.container) == (True, "h264", "aac", "mp4")
    assert good.probed and good.duration_seconds == pytest.approx(2, abs=0.2)

    old = records["Old Codec"]
    assert old.playable is False
    assert "video mpeg4" in old.compat_note

    broken = records["Broken"]
    assert broken.playable is False
    assert "Could not read" in broken.compat_note
