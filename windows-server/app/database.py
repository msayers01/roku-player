"""SQLite catalog of scanned media.

Only paths *relative to a configured media root* are stored; absolute host
paths never leave the server and are re-validated every time they are used.
"""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS media (
    id               TEXT PRIMARY KEY,
    root_name        TEXT NOT NULL,
    rel_path         TEXT NOT NULL,
    poster_rel_path  TEXT,
    title            TEXT NOT NULL,
    sort_title       TEXT NOT NULL,
    year             INTEGER,
    duration_seconds REAL,
    container        TEXT,
    video_codec      TEXT,
    audio_codec      TEXT,
    width            INTEGER,
    height           INTEGER,
    size_bytes       INTEGER NOT NULL,
    probed           INTEGER NOT NULL,
    playable         INTEGER NOT NULL,
    compat_note      TEXT
);
"""


@dataclass(frozen=True)
class MediaRecord:
    id: str
    root_name: str
    rel_path: str
    poster_rel_path: str | None
    title: str
    sort_title: str
    year: int | None
    duration_seconds: float | None
    container: str | None
    video_codec: str | None
    audio_codec: str | None
    width: int | None
    height: int | None
    size_bytes: int
    probed: bool
    playable: bool
    compat_note: str | None


_COLUMNS = [f for f in MediaRecord.__dataclass_fields__]


class Catalog:
    def __init__(self, db_path: Path | str):
        self._lock = threading.Lock()
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock, self._conn:
            self._conn.executescript(SCHEMA)

    def replace_all(self, records: list[MediaRecord]) -> None:
        placeholders = ", ".join("?" for _ in _COLUMNS)
        sql = f"INSERT INTO media ({', '.join(_COLUMNS)}) VALUES ({placeholders})"
        with self._lock, self._conn:
            self._conn.execute("DELETE FROM media")
            self._conn.executemany(
                sql, [tuple(getattr(r, c) for c in _COLUMNS) for r in records]
            )

    def list(self) -> list[MediaRecord]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM media ORDER BY sort_title, year, id"
            ).fetchall()
        return [_to_record(r) for r in rows]

    def get(self, media_id: str) -> MediaRecord | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM media WHERE id = ?", (media_id,)
            ).fetchone()
        return _to_record(row) if row else None

    def close(self) -> None:
        with self._lock:
            self._conn.close()


def _to_record(row: sqlite3.Row) -> MediaRecord:
    data = dict(row)
    data["probed"] = bool(data["probed"])
    data["playable"] = bool(data["playable"])
    return MediaRecord(**data)
