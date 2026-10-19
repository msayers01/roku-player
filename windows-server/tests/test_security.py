from __future__ import annotations

import os
from pathlib import Path

import pytest

from app.config import MediaRoot
from app.services.paths import resolve_inside
from tests.conftest import build_client, make_config


@pytest.mark.parametrize("rel", ["../secret.mp4", "a/../../secret.mp4", "/etc/passwd", "", "C:/x.mp4"])
def test_resolve_inside_rejects_escapes(tmp_path: Path, rel: str):
    root = tmp_path / "root"
    root.mkdir()
    result = resolve_inside(root, rel)
    assert result is None or result.is_relative_to(root.resolve())


def test_resolve_inside_allows_nested(tmp_path: Path):
    root = tmp_path / "root"
    (root / "a").mkdir(parents=True)
    assert resolve_inside(root, "a/b.mp4") == (root / "a" / "b.mp4").resolve()


@pytest.mark.skipif(os.name == "nt", reason="symlinks need admin rights on Windows")
def test_symlink_escape_is_not_catalogued(tmp_path: Path):
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "Private (2020).mp4").write_bytes(b"secret")
    (outside / "dir").mkdir()
    (outside / "dir" / "Hidden (2021).mp4").write_bytes(b"secret")

    root = tmp_path / "root"
    root.mkdir()
    (root / "Visible (2022).mp4").write_bytes(b"ok")
    (root / "Linked (2020).mp4").symlink_to(outside / "Private (2020).mp4")
    (root / "linked-dir").symlink_to(outside / "dir", target_is_directory=True)

    client = build_client(make_config([MediaRoot("Movies", root)], tmp_path))
    titles = [i["title"] for i in client.get("/api/media").json()["items"]]
    assert titles == ["Visible"]


def test_traversal_style_ids_are_just_unknown(client):
    for bad in ["..%2F..%2Fetc%2Fpasswd", "%2e%2e"]:
        resp = client.get(f"/api/media/{bad}/stream")
        assert resp.status_code == 404
