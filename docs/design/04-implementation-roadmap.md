# 04 — Roadmap and Test Plan
Version 0.3 — 2026-10-19

## Milestone 1 — Playback transport proof
1. Install Python and FastAPI/Uvicorn on Windows 11.
2. Make a configurable server exposing `/api/health` and one known-good MP4 as a range-aware URL.
3. Confirm in a LAN browser/client that HTTP 200/206/416 behavior is correct.
4. Create sideloadable Roku SceneGraph app with manually entered server address.
5. Play video on Roku Video node. Confirm pause/resume and ordinary seek.
**Exit:** one local MP4 plays reliably from PC to Roku.

## Milestone 2 — 15-second controls
1. Add playback HUD with `-15s`, play/pause, `+15s` and timeline.
2. Wire HUD actions to `SeekController`, clamp target, observe position updates.
3. Test Replay key as optional shortcut without breaking Roku-expected FF/RW behavior.
4. Test repeated taps, near EOF/start, paused state and keyframe seek tolerance.
**Exit:** both buttons work on real Roku hardware without crashes.

## Milestone 3 — Poster library
1. Scan approved folders for MP4 test profile and optional adjacent `poster.jpg`.
2. Use SQLite catalog with stable IDs and conservative compatibility flag.
3. Implement `/api/media`, item details and poster endpoints.
4. Build poster grid and details scene with fallback posters.
**Exit:** at least 10 items navigable by Roku remote.

## Milestone 4 — Hardening
- Friendly errors for server stopped, incompatible media, missing files, disconnected LAN.
- Save Roku server IP/port, avoid render-thread blocking, cache poster images.
- Validate file-root security, narrow Windows firewall rule, no WAN port-forwarding.
- Document setup and packaging for restart.

## Milestone 5 — EQ technical feasibility (not MVP)
- Verify on target Roku TV model whether any supported app-controllable audio settings exist that actually change sound for Video node content.
- If unavailable: either keep EQ outside app as TV/audio device settings, or obtain explicit approval to drop direct-play-only and design a server-side DSP/processed-stream option.
- Prove with audio measurement/listening and document format/latency/CPU consequences before shipping any preset controls.

## Test matrix
| Test | Expected result |
|---|---|
| Server offline on Roku launch | Clear error + retry/edit |
| IP wrong/changed | Reconfigure successfully |
| MP4 H.264/AAC | Plays and seeks |
| Unknown codec | Unsupported notice; no fake playback |
| +15 at 00:30 | Lands approximately at 00:45 |
| -15 at 00:30 | Lands approximately at 00:15 |
| -15 at 00:05 | Clamped at 00:00 |
| +15 near clip end | Clamped to safe seekable boundary |
| Multiple rapid seek taps | Consistent result; no crash |
| Seek while paused | Behavior defined and repeatable |
| File deleted after catalog scan | Clear unavailable-media error |
| Firewall blocks incoming | Clear connection failure |
| Missing poster | Placeholder shown |
| EQ UI in MVP | Not offered as working DSP |

## Handoff
Start with transport; real Roku device behavior controls the seek implementation. Bookmark official Roku developer docs referenced in README.
