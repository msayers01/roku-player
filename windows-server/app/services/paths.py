"""Path validation that keeps every served file inside an approved media root."""

from __future__ import annotations

from pathlib import Path, PurePosixPath


def resolve_inside(root: Path, rel_path: str) -> Path | None:
    """Resolve ``rel_path`` under ``root``; return None if it escapes the root.

    Resolution follows symlinks and junctions, so a link that points outside
    the root is rejected just like a ``..`` traversal.
    """
    rel = PurePosixPath(rel_path)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        return None
    try:
        root_real = root.resolve(strict=True)
        candidate = (root_real / Path(*rel.parts)).resolve(strict=False)
    except (OSError, RuntimeError):
        return None
    if not candidate.is_relative_to(root_real):
        return None
    return candidate
