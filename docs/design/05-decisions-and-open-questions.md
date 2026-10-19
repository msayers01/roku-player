# 05 — Decision Log and Open Questions
Version 0.3 — 2026-10-19

## Agreed
- Roku client is a poster-grid media player.
- Windows 11 host serves selected local video files over LAN.
- Host starts manually; Roku connects using manually configured IP and port.
- Direct play only, no on-the-fly conversion.
- ±15-second playback jumps are desired.
- Audio EQ presets are desired, but cannot be represented as functional without verified DSP capabilities.

## Architectural decisions
| Decision | Why | Revisit when |
|---|---|---|
| FastAPI Windows host | Fast prototype, mature HTTP stack | Packaging/performance requires changes |
| SQLite catalog | Simple local cache for artwork and metadata | Scale warrants a different store |
| SceneGraph Video node | Native Roku playback | Device constraints force redesign |
| HUD ±15 actions | Consistent with variable Roku remote keys | Remote usability testing |
| No `POST /seek` endpoint | Playback is client-managed | Server switches to session-based streaming |
| EQ deferred | Native per-app EQ unavailable/unverified | Platform capability proof or transcoding approved |

## Outstanding questions for next session
1. Exact Roku TV model, OS version, and which remote buttons it has (especially Replay).
2. Typical source codecs, subtitles and containers; how many files?
3. Poster source: sidecar `poster.jpg`, auto-generated image, or later online metadata?
4. Preferred server packaging: Python batch starter vs standalone Windows `.exe`.
5. Does EQ mean app-specific custom DSP or is opening TV/soundbar sound-mode settings acceptable?
6. Should -15/+15 controls appear only in the playback HUD or also use physical remote shortcuts?

## Important EQ trade-off
If **actual EQ controls inside the Roku app** are mandatory, the locked **direct play only** requirement probably needs to change. A server-side DSP pipeline can alter audio but requires generating a processed stream; otherwise the Roku's native playback path and the TV/audio-device sound controls govern audio output.

## Current status
Design only. No deployed media server, Roku application, working seek controls, or working EQ have been built.
