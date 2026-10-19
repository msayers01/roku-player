# Roku LAN Media Player — Design Handoff
Version: 0.3 | 2026-10-19 | Status: Planning, not implemented

## Product concept
A sideloaded Roku SceneGraph app browses a poster-based library of videos hosted by a manually launched Windows 11 HTTP server on the same LAN. Manual IP/port configuration, direct playback only. No cloud dependency for library and streaming.

## Requested new features
- **Skip forward +15 seconds** and **rewind -15 seconds** during playback: MVP requirement, subject to Roku remote key handling and stream seeking tests.
- **Audio EQ presets**: design retained, but **deferred / feasibility-gated**. Roku's documented SceneGraph Video node does not expose a general-purpose per-app multi-band audio EQ DSP interface. A UI setting alone cannot change audio output. Native TV/soundbar sound modes are external to this Roku app. Server-side DSP would require processed audio/transcoding and violate the direct-play-only MVP constraint.

## Contents
- `01-product-requirements.md` — scope, UX, acceptance criteria
- `02-system-architecture.md` — components, trust boundaries, playback and audio design
- `03-api-contract.md` — planned REST endpoints and examples
- `04-implementation-roadmap.md` — milestones and test plan
- `05-decisions-and-open-questions.md` — decisions, risks and follow-up questions
- `diagrams/architecture.mmd` — Mermaid component architecture
- `diagrams/playback-flow.mmd` — Mermaid detailed navigation/playback flow
- `diagrams/seek-controls.mmd` — Mermaid seek state flow

## Suggested resume point
Begin milestone 1: FastAPI server on Windows serving a known-good H.264/AAC MP4 with byte-range support; sideload a basic Roku app and verify playback and ±15-second seek on actual hardware. Later add poster metadata/grid, persist settings, and determine whether EQ is feasible without giving up direct play.

## Documentation references
- Roku remote behavior: https://developer.roku.com/dev/docs/remote-control-buttons
- SceneGraph key events: https://developer.roku.com/dev/docs/onkeyevent
- Roku Video node lesson: https://developer.roku.com/dev/docs/video-player
- Roku reference overview: https://developer.roku.com/dev/docs/references-overview

All names, paths, API responses and screenshots described are proposed, not existing implementations.
