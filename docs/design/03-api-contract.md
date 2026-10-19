# 03 — API Contract (Proposed)
Version 0.3 — 2026-10-19

Base URL: `http://<WINDOWS_LAN_IP>:8080` (sample port; configurable)

## GET /api/health
200 JSON:
```json
{"status":"ok","service":"roku-lan-media","api_version":"1.0"}
```

## GET /api/media
200 JSON:
```json
{"items":[{"id":"movie_001","title":"Sample Movie","year":2024,"duration_seconds":6480,"poster_url":"/api/media/movie_001/poster","playable":true}]}
```
`playable` is based on host probe / conservative allowlist; hardware compatibility may differ.

## GET /api/media/{id}
200 JSON:
```json
{"id":"movie_001","title":"Sample Movie","duration_seconds":6480,"video_codec":"h264","audio_codec":"aac","stream_format":"mp4","playable":true,"stream_url":"/api/media/movie_001/stream"}
```

## GET /api/media/{id}/poster
200 `image/jpeg` or `image/png`; use fallback image if no poster. Optionally implement caching headers.

## GET /api/media/{id}/stream
200 for full response or **206 Partial Content** for satisfiable byte range.
Example request: `Range: bytes=1048576-2097151`
Example headers: `Accept-Ranges: bytes`, `Content-Range: bytes 1048576-2097151/<FILE_SIZE>`, appropriate `Content-Length`, `Content-Type: video/mp4`.
Unsupported byte range: 416 with `Content-Range: bytes */<FILE_SIZE>`.
Use bounded streaming/chunk reads, not whole-file memory reads; respond to HEAD if practical.

## GET /api/config (optional later)
Expose limited safe server capabilities; no filesystem paths or secrets.

## Error model
400 malformed request; 404 unknown media ID; 409 media file removed or catalog stale; 416 unsatisfiable byte range; 500 unexpected server failure. JSON API errors: `{"error":{"code":"media_not_found","message":"Media no longer available"}}`.

## Playback controls
**No new API endpoint is required for +15/-15 seeking.** Roku controls its native Video playback position; seek operations cause new HTTP range requests as necessary. **No EQ endpoint in MVP**, since EQ DSP is not implemented.

## Compatibility and safety
Use validated IDs, never accept arbitrary absolute paths; validate request ranges and set correct response headers. Host serves only approved roots. Avoid caching sensitive directory information.
