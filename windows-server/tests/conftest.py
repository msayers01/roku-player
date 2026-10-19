from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.config import Config, MediaRoot
from app.database import Catalog
from app.main import create_app
from app.services.scanner import scan

HAS_FFMPEG = shutil.which("ffmpeg") is not None and shutil.which("ffprobe") is not None


def make_config(roots: list[MediaRoot], tmp_path: Path, ffprobe: str | None = None) -> Config:
    return Config(media_roots=tuple(roots), database_path=tmp_path / "catalog.db", ffprobe_path=ffprobe)


def build_client(config: Config) -> TestClient:
    catalog = Catalog(config.database_path)
    catalog.replace_all(scan(config).records)
    return TestClient(create_app(config, catalog))


@pytest.fixture
def library(tmp_path: Path) -> Path:
    """A media root with fake (unprobed) MP4 bytes and a sidecar poster."""
    root = tmp_path / "movies"
    (root / "Sci-Fi").mkdir(parents=True)
    (root / "Sci-Fi" / "Aurora.Drift.(2021).mp4").write_bytes(bytes(range(256)) * 40)  # 10240 bytes
    (root / "Sci-Fi" / "Aurora.Drift.(2021).jpg").write_bytes(b"\xff\xd8poster-bytes")
    (root / "The Long Way North 2017.m4v").write_bytes(b"x" * 100)
    (root / "notes.txt").write_text("not media")
    return root


@pytest.fixture
def client(library: Path, tmp_path: Path) -> TestClient:
    return build_client(make_config([MediaRoot("Movies", library)], tmp_path))


def make_clip(path: Path, vcodec: str = "libx264", seconds: int = 2) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y",
         "-f", "lavfi", "-i", f"testsrc2=size=160x90:rate=10:duration={seconds}",
         "-f", "lavfi", "-i", f"sine=duration={seconds}",
         "-c:v", vcodec, "-c:a", "aac", "-shortest", str(path)],
        check=True,
    )
