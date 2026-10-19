"""Shared lookups used by the media and streaming routes."""

from __future__ import annotations

from pathlib import Path

from fastapi import Request

from app.config import Config
from app.database import Catalog, MediaRecord
from app.errors import ApiError
from app.services.paths import resolve_inside


def catalog(request: Request) -> Catalog:
    return request.app.state.catalog


def config(request: Request) -> Config:
    return request.app.state.config


def get_record(request: Request, media_id: str) -> MediaRecord:
    record = catalog(request).get(media_id)
    if record is None:
        raise ApiError(404, "media_not_found", "Media no longer available")
    return record


def root_path(request: Request, root_name: str) -> Path | None:
    for root in config(request).media_roots:
        if root.name == root_name:
            return root.path
    return None


def resolve_file(request: Request, record: MediaRecord, rel_path: str) -> Path | None:
    """Map a catalog entry back to a real file, re-checking the root allowlist."""
    root = root_path(request, record.root_name)
    if root is None:
        return None
    path = resolve_inside(root, rel_path)
    if path is None or not path.is_file():
        return None
    return path
