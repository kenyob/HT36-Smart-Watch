---
kind: app
slug: blood-oxygen
status: partial
updated: 2026-11-18
---
# Blood oxygen (SpO2)

SpO2 monitoring.

- **Status:** `partial`
- **Images:** `./blood-oxygen/` (see its README for where images come from)

## Features
- Auto SpO2 toggle
- Reminders
- History

## Data it has
- Auto-SpO2 enable state (`01 E1 AA 11` → on)

## Can we manipulate it yet?
Enable-state reads. Set frames mapped, untested.

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
