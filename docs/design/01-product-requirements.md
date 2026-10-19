# 01 — Product Requirements (PRD)
Version 0.3 — 2026-10-19

## Objective
Build a private Roku TV app that displays posters and streams movies from approved folders on a Windows 11 desktop across the same LAN.

## Locked product decisions
| Dimension | Choice |
|---|---|
| Library | Poster grid and movie-detail view |
| Format | Direct play only; no transcoding in MVP |
| Server | User manually starts Windows server |
| Discovery | User types IP address and port; saved on Roku |
| Streaming | HTTP on trusted LAN, direct from Windows PC |
| Primary test profile | MP4 / H.264 / AAC-LC stereo |
| Roku platform | BrightScript + SceneGraph Video node |
| Windows platform | Python FastAPI + SQLite catalog |

## User journey
1. User runs `start_server.bat` on Windows.
2. Server scans configured allowlisted folders, indexes metadata, and serves posters, API and video bytes.
3. User opens Roku app and configures server IP/port the first time.
4. App checks `/api/health` and fetches `/api/media`.
5. User browses poster grid, opens film details, selects Play.
6. Roku plays a compatible stream using native Video node.
7. During playback user pauses/resumes, skips +15 seconds, rewinds -15 seconds, or exits.
8. On error app shows a helpful message and returns to details or connection settings.

## Feature requirements
| ID | Requirement | Priority / release |
|---|---|---|
| F-01 | Manual server IP and port, saved between launches | MVP |
| F-02 | Connection status with retry/edit | MVP |
| F-03 | Poster grid from server images, placeholder when absent | MVP |
| F-04 | Details: title, runtime, poster, playable status | MVP |
| F-05 | Direct play compatible local MP4 by HTTP | MVP |
| F-06 | Native play, pause, timeline seek, Back | MVP |
| F-07 | One-step skip forward **15 seconds** | MVP |
| F-08 | One-step rewind **15 seconds** | MVP |
| F-09 | Seek bounds: 0 <= target <= duration (with practical end guard) | MVP |
| F-10 | Seek toast/HUD shows `+15s` or `-15s` and timeline | MVP |
| F-11 | Explicit unsupported-format handling | MVP |
| F-12 | Audio EQ settings screen / preset names | Future / not active in MVP |
| F-13 | Actual EQ DSP applied to playback | Feasibility gate; not promised |
| F-14 | Catalog manual refresh | Soon after MVP |
| F-15 | Captions, resume positions, automatic discovery, search | Later |

## Proposed remote controls
- During playback, show a compact controls HUD on **OK** with `-15s`, Play/Pause, `+15s`, `Audio` (informational or future), and progress bar. Use d-pad to focus/select these actions.
- Optional shortcuts: dedicated Replay key can map to -15 seconds when the app receives it. Do **not** override normal FF/RW remote behavior without a usability test; Roku user guidance ordinarily expects FF/RW trick-play speeds. Dedicated `+15s` and `-15s` HUD actions are the reliable cross-remote baseline.
- If duration is known, apply `target = min(max(position + delta, 0), safeEnd)` with delta = +15 or -15. At clip end, show a non-blocking message or stop at safe seekable boundary; do not trigger a seek past EOF.
- Repeated taps: queue or debounce while a prior seek completes; never assume seek has landed until reported position/state updates.

## EQ presets — designed but not falsely promised
Proposed labels: `Off/Flat`, `Dialogue`, `Movie`, `Music`, `Bass Boost`, `Night`.
- **MVP behavior**: Do not present selectable working presets unless the platform exposes an actual functional implementation. In architecture/docs, mark as future.
- **Alternative user experience**: Provide a help note suggesting Roku TV / audio-device sound settings, clearly outside app control.
- **If revisited**: spike/prototype whether any device-specific audio control is actually allowed. True custom EQ likely requires server-side re-encoding (conflicts with direct-play decision), a different playback pipeline, or external hardware. No guarantee of Roku app-level EQ.

## Non-functional requirements
- Do not expose host PC filesystem paths in API output.
- Only configured roots can be served; reject traversal/symlink escape.
- Support range requests (`Range`, `Accept-Ranges`, `206`, `Content-Range`) for seeks.
- Restrict Windows Firewall rule to trusted local subnet; do not set router port forwarding.
- Handle PC sleep, IP changes, connectivity failure, interrupted playback.
- Keep UI remote-navigable at TV viewing distances.

## Acceptance criteria
- [ ] Manual Windows launch displays listening LAN address.
- [ ] Roku saves IP/port and reconnects after app restart.
- [ ] 10 test titles appear in poster grid with fallback art.
- [ ] Valid H.264/AAC MP4 opens and plays from local PC.
- [ ] Pausing and resuming works.
- [ ] HUD `+15s` advances playback about 15 seconds where seekable.
- [ ] HUD `-15s` rewinds playback about 15 seconds where seekable.
- [ ] Near-start/near-end seeks do not crash or exceed media range.
- [ ] Repeated seeks and server disconnections fail gracefully.
- [ ] Audio EQ is visibly marked as future/unsupported rather than pretending to change sound.
