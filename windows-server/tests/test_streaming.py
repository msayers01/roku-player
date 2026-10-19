from __future__ import annotations

import pytest

from app.api.streaming import RangeNotSatisfiable, parse_range
from app.config import MediaRoot
from tests.conftest import build_client, make_config

DATA = bytes(range(256)) * 40
SIZE = len(DATA)


@pytest.fixture
def stream_url(client) -> str:
    items = {i["title"]: i["id"] for i in client.get("/api/media").json()["items"]}
    return f"/api/media/{items['Aurora Drift']}/stream"


def test_full_response(client, stream_url):
    resp = client.get(stream_url)
    assert resp.status_code == 200
    assert resp.headers["accept-ranges"] == "bytes"
    assert resp.headers["content-length"] == str(SIZE)
    assert resp.headers["content-type"] == "video/mp4"
    assert resp.content == DATA


def test_closed_range(client, stream_url):
    resp = client.get(stream_url, headers={"Range": "bytes=100-199"})
    assert resp.status_code == 206
    assert resp.headers["content-range"] == f"bytes 100-199/{SIZE}"
    assert resp.headers["content-length"] == "100"
    assert resp.content == DATA[100:200]


def test_open_ended_range(client, stream_url):
    resp = client.get(stream_url, headers={"Range": "bytes=10000-"})
    assert resp.status_code == 206
    assert resp.headers["content-range"] == f"bytes 10000-{SIZE - 1}/{SIZE}"
    assert resp.content == DATA[10000:]


def test_suffix_range(client, stream_url):
    resp = client.get(stream_url, headers={"Range": "bytes=-16"})
    assert resp.status_code == 206
    assert resp.content == DATA[-16:]


def test_range_end_clamped_to_file_size(client, stream_url):
    resp = client.get(stream_url, headers={"Range": f"bytes=10200-{SIZE * 10}"})
    assert resp.status_code == 206
    assert resp.headers["content-range"] == f"bytes 10200-{SIZE - 1}/{SIZE}"
    assert resp.content == DATA[10200:]


def test_unsatisfiable_range(client, stream_url):
    resp = client.get(stream_url, headers={"Range": f"bytes={SIZE}-"})
    assert resp.status_code == 416
    assert resp.headers["content-range"] == f"bytes */{SIZE}"
    assert resp.json()["error"]["code"] == "range_not_satisfiable"


def test_large_reads_cross_chunk_boundary(client, library):
    big = bytes(i % 251 for i in range(700_000))
    (library / "Big File (2020).mp4").write_bytes(big)
    c = build_client(make_config([MediaRoot("Movies", library)], library.parent / "db2"))
    item = next(i for i in c.get("/api/media").json()["items"] if i["title"] == "Big File")
    resp = c.get(f"/api/media/{item['id']}/stream", headers={"Range": "bytes=100000-650000"})
    assert resp.status_code == 206
    assert resp.content == big[100000:650001]


def test_head_has_headers_and_no_body(client, stream_url):
    resp = client.head(stream_url, headers={"Range": "bytes=0-9"})
    assert resp.status_code == 206
    assert resp.headers["content-length"] == "10"
    assert resp.headers["content-range"] == f"bytes 0-9/{SIZE}"
    assert resp.content == b""


@pytest.mark.parametrize("header", [
    None, "", "items=0-5", "bytes=0-5,10-20", "bytes=abc-", "bytes=-", "bytes=9-3", "bytes=5",
])
def test_ignored_ranges_send_whole_file(header):
    assert parse_range(header, 100) is None


@pytest.mark.parametrize("header,expected", [
    ("bytes=0-0", (0, 0)),
    ("bytes=0-", (0, 99)),
    ("bytes=90-200", (90, 99)),
    ("bytes=-10", (90, 99)),
    ("bytes=-500", (0, 99)),
    (" bytes = 5 - 9 ", (5, 9)),
])
def test_parse_range(header, expected):
    assert parse_range(header, 100) == expected


@pytest.mark.parametrize("header,size", [("bytes=100-", 100), ("bytes=-0", 100), ("bytes=0-", 0), ("bytes=-5", 0)])
def test_unsatisfiable(header, size):
    with pytest.raises(RangeNotSatisfiable):
        parse_range(header, size)
