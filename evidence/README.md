# Submission evidence checklist

This directory is intentionally free of fabricated evidence. Add the following only after the live BAND Desktop room has produced the service:

- `band-room-export.json` — official `harness export-room` output
- `demo-video.mp4` — screen recording of the BAND room plus service walkthrough
- `cover.png` — submission cover image
- `slides.pdf` — presentation deck
- `harness-report.json` — official stage report, if generated
- `local-rehearsal.json` — deterministic local run, not a substitute for room evidence

Never include API keys, `.env` files, private room URLs, or real user data. Follow [`../BAND_ROOM_EXPORT_RUNBOOK.md`](../BAND_ROOM_EXPORT_RUNBOOK.md) to produce the room export and video. The local `harness check` reports external items as blockers until they exist.
