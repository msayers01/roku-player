"""Range-aware byte streaming so the Roku Video node can seek."""

from __future__ import annotations

from collections.abc import Iterator
from typing import BinaryIO

from fastapi import APIRouter, Request
from fastapi.responses import Response, StreamingResponse

from app.api import deps
from app.errors import ApiError

router = APIRouter()

CHUNK_SIZE = 256 * 1024


class RangeNotSatisfiable(Exception):
    pass


def parse_range(header: str | None, size: int) -> tuple[int, int] | None:
    """Return an inclusive (start, end) byte range, or None to send the whole file.

    Malformed or multi-range headers are ignored (full 200 response), as
    RFC 9110 allows. A well-formed but unsatisfiable range raises.
    """
    if not header:
        return None
    unit, _, spec = header.strip().partition("=")
    if unit.strip().lower() != "bytes" or "," in spec:
        return None
    first, sep, last = spec.strip().partition("-")
    if not sep:
        return None
    first, last = first.strip(), last.strip()
    if (first and not first.isdigit()) or (last and not last.isdigit()) or not (first or last):
        return None

    if not first:  # suffix range: last N bytes
        length = int(last)
        if length == 0 or size == 0:
            raise RangeNotSatisfiable
        return max(0, size - length), size - 1

    start = int(first)
    end = int(last) if last else size - 1
    if last and end < start:
        return None
    if start >= size:
        raise RangeNotSatisfiable
    return start, min(end, size - 1)


def _iter_file(handle: BinaryIO, start: int, length: int) -> Iterator[bytes]:
    try:
        handle.seek(start)
        remaining = length
        while remaining > 0:
            chunk = handle.read(min(CHUNK_SIZE, remaining))
            if not chunk:
                break
            remaining -= len(chunk)
            yield chunk
    finally:
        handle.close()


@router.api_route("/api/media/{media_id}/stream", methods=["GET", "HEAD"])
def stream(request: Request, media_id: str) -> Response:
    record = deps.get_record(request, media_id)
    path = deps.resolve_file(request, record, record.rel_path)
    if path is None:
        raise ApiError(409, "media_unavailable", "Media file was moved or deleted; refresh the catalog")

    size = path.stat().st_size
    try:
        byte_range = parse_range(request.headers.get("range"), size)
    except RangeNotSatisfiable:
        raise ApiError(416, "range_not_satisfiable", "Requested byte range is outside the file",
                       headers={"Content-Range": f"bytes */{size}"})

    headers = {"Accept-Ranges": "bytes", "Cache-Control": "no-store"}
    if byte_range is None:
        start, end, status = 0, size - 1, 200
    else:
        start, end = byte_range
        status = 206
        headers["Content-Range"] = f"bytes {start}-{end}/{size}"
    length = max(0, end - start + 1)
    headers["Content-Length"] = str(length)

    if request.method == "HEAD":
        return Response(status_code=status, headers=headers, media_type="video/mp4")

    handle = path.open("rb")
    return StreamingResponse(_iter_file(handle, start, length), status_code=status,
                             headers=headers, media_type="video/mp4")
