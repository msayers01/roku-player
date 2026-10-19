from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import FileResponse

from app.api import deps
from app.database import MediaRecord
from app.services import artwork

router = APIRouter()

POSTER_CACHE = "public, max-age=3600"


def _duration(record: MediaRecord) -> int | None:
    return round(record.duration_seconds) if record.duration_seconds is not None else None


def summary(record: MediaRecord) -> dict:
    return {
        "id": record.id,
        "title": record.title,
        "year": record.year,
        "duration_seconds": _duration(record),
        "poster_url": f"/api/media/{record.id}/poster",
        "playable": record.playable,
    }


def detail(record: MediaRecord) -> dict:
    return {
        **summary(record),
        "video_codec": record.video_codec,
        "audio_codec": record.audio_codec,
        "stream_format": record.container,
        "width": record.width,
        "height": record.height,
        "size_bytes": record.size_bytes,
        "codecs_verified": record.probed,
        "compatibility_note": record.compat_note,
        "stream_url": f"/api/media/{record.id}/stream",
    }


@router.get("/api/media")
def list_media(request: Request) -> dict:
    return {"items": [summary(r) for r in deps.catalog(request).list()]}


@router.get("/api/media/{media_id}")
def get_media(request: Request, media_id: str) -> dict:
    return detail(deps.get_record(request, media_id))


@router.api_route("/api/media/{media_id}/poster", methods=["GET", "HEAD"])
def get_poster(request: Request, media_id: str) -> FileResponse:
    record = deps.get_record(request, media_id)
    poster = None
    if record.poster_rel_path:
        poster = deps.resolve_file(request, record, record.poster_rel_path)
    if poster is None:
        return FileResponse(artwork.PLACEHOLDER, media_type="image/png",
                            headers={"Cache-Control": POSTER_CACHE, "X-Poster-Fallback": "1"})
    return FileResponse(poster, media_type=artwork.media_type_for(poster),
                        headers={"Cache-Control": POSTER_CACHE})
