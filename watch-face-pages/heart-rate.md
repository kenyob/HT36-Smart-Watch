---
kind: app
slug: heart-rate
status: partial
updated: 2026-11-18
---
# Heart rate

Heart-rate monitoring and history.

- **Status:** `partial`
- **Images:** `./heart-rate/` (see its README for where images come from)

## Features
- Auto/continuous HR toggle
- Measurement interval
- High/low alerts
- History

## Data it has
- Auto-HR enable state (`01 E1 AA 10` → on)
- HR values come from history sync, not a live stream

## Can we manipulate it yet?
Enable-state reads. Toggles (`01 E1 AB 01/02`) are mapped but untested. The watch does NOT push live bpm; HR is read from the fitness-history sync.

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
