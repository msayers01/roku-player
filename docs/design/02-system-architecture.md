# 02 — System Architecture
Version 0.3 — 2026-10-19

See `diagrams/architecture.mmd`, `diagrams/playback-flow.mmd`, `diagrams/seek-controls.mmd`.

## Client: Roku SceneGraph
- `ConnectionScene`: manual host IP/port entry; store values in Roku registry.
- `CatalogTask`: async HTTP GET to API and image endpoints; no synchronous network work on render thread.
- `PosterGridScene`: poster-focused browsing; missing artwork fallback.
- `DetailsScene`: title, runtime, codec support warning and Play action.
- `PlaybackScene`: native `Video` node, overlay HUD with explicit ±15 buttons, play/pause, progress.
- `SeekController`: receives UI intentions, observes `Video.position`, `Video.duration`, playback state and seek completion; calculates clamped absolute target; requests seeking through supported Video-node fields after device testing.
- `AudioSettingsScene` (future placeholder only): EQ decision/feasibility pending.

## Host: Windows 11
- `start_server.bat` manually invokes configured Python environment and FastAPI/Uvicorn.
- `config.json` contains named media roots, bind address, port and artwork rules.
- Scanner finds files and records stable IDs, titles, runtime/codec results, poster association in SQLite.
- Media API returns metadata, not absolute Windows filesystem paths.
- Streaming component maps media ID to validated allowlisted path; sends range-aware byte stream.
- Artwork endpoint streams poster JPEG/PNG; missing art receives fallback.
- Optional FFprobe can inspect formats without transcoding media.

## Data flow
1. Roku `GET /api/health` => host.
2. Roku `GET /api/media` => list with item IDs/poster links.
3. Roku requests `GET /api/media/{id}/poster` per visible image.
4. Roku requests `GET /api/media/{id}` for details.
5. Roku Video node requests `GET /api/media/{id}/stream`, often with byte ranges, and can issue additional range requests during seek.
6. `SeekController` changes native Video playback position; host simply supplies requested byte ranges. No server `POST /seek` needed.

## Key seek algorithm (conceptual, not tested code)
```
seekBy(deltaSeconds):
  if video not loaded or duration not valid: show unavailable; return
  p = latest confirmed playback position
  target = clamp(p + deltaSeconds, 0, max(0, duration - endMargin))
  if abs(target - p) <= tolerance: return
  request native Video seek to target
  display HUD with delta and target
  await position update; clear transient HUD or show error
```
The playback-node field/method and exact end-margin must be confirmed on the user's actual Roku model. Seeking may land near (rather than exactly on) target due to keyframes/MP4 indexing.

## Audio processing constraint
The native Roku video playback path decodes and outputs audio internally. Public SceneGraph Video node references do not establish a general user-specified per-app multi-band EQ control. A preset UI does not imply audio can be changed. Server audio filtering with FFmpeg would generate an altered stream, so it violates the chosen direct-play-only MVP. Maintain feature as pending technical feasibility; do not implement fake presets.

## Trust boundaries
- Only trusted LAN: bind server to explicit LAN IP or interface, firewall port restricted to LAN CIDR, never forward router WAN port.
- Media root allowlist, normalize and validate file paths, prohibit path traversal and symlink escape.
- Host API unauthenticated in MVP: anyone on allowed LAN may access media. Optional pairing token for later phase.
- Avoid public remote access; disable server when not using it.
- No transcoding and no automatic server discovery in MVP.

## Suggested source tree
```
roku-lan-media/
  roku-client/
    manifest
    source/main.brs
    components/ConnectionScene.xml
    components/PosterGridScene.xml
    components/DetailsScene.xml
    components/PlaybackScene.xml
    components/SeekController.brs
    components/CatalogTask.xml
    images/placeholder_poster.png
  windows-server/
    app/main.py
    app/api/{health,media,streaming}.py
    app/services/{scanner,metadata,artwork}.py
    app/database.py
    config.json
    requirements.txt
    start_server.bat
  docs/
  tests/
```
