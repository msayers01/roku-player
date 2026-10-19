from __future__ import annotations

from pathlib import Path

from app.services.scanner import media_id


def _ids(client) -> dict[str, str]:
    return {item["title"]: item["id"] for item in client.get("/api/media").json()["items"]}


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "roku-lan-media", "api_version": "1.0"}


def test_list_media_sorted_without_articles_and_parsed_titles(client):
    items = client.get("/api/media").json()["items"]
    assert [(i["title"], i["year"]) for i in items] == [
        ("Aurora Drift", 2021),
        ("The Long Way North", 2017),
    ]
    first = items[0]
    assert set(first) == {"id", "title", "year", "duration_seconds", "poster_url", "playable"}
    assert first["poster_url"] == f"/api/media/{first['id']}/poster"


def test_ids_are_stable(client):
    assert _ids(client)["Aurora Drift"] == media_id("Movies", "Sci-Fi/Aurora.Drift.(2021).mp4")


def test_details_never_expose_host_paths(client, library: Path):
    for item_id in _ids(client).values():
        body = client.get(f"/api/media/{item_id}").text
        assert str(library) not in body
        assert "Sci-Fi" not in body
        assert ".mp4" not in body


def test_details_without_ffprobe_are_marked_unverified(client):
    detail = client.get(f"/api/media/{_ids(client)['Aurora Drift']}").json()
    assert detail["playable"] is True
    assert detail["codecs_verified"] is False
    assert "not verified" in detail["compatibility_note"]
    assert detail["stream_url"] == f"/api/media/{detail['id']}/stream"


def test_unknown_media_uses_error_model(client):
    resp = client.get("/api/media/nope")
    assert resp.status_code == 404
    assert resp.json() == {"error": {"code": "media_not_found", "message": "Media no longer available"}}


def test_unknown_route_uses_error_model(client):
    resp = client.get("/api/nothing")
    assert resp.status_code == 404
    assert resp.json()["error"]["code"] == "not_found"


def test_sidecar_poster_served(client):
    resp = client.get(f"/api/media/{_ids(client)['Aurora Drift']}/poster")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/jpeg"
    assert resp.content == b"\xff\xd8poster-bytes"
    assert "x-poster-fallback" not in resp.headers


def test_missing_poster_falls_back_to_placeholder(client):
    resp = client.get(f"/api/media/{_ids(client)['The Long Way North']}/poster")
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "image/png"
    assert resp.headers["x-poster-fallback"] == "1"
    assert resp.content.startswith(b"\x89PNG")


def test_deleted_file_returns_409(client, library: Path):
    item_id = _ids(client)["The Long Way North"]
    (library / "The Long Way North 2017.m4v").unlink()
    resp = client.get(f"/api/media/{item_id}/stream")
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "media_unavailable"
