---
kind: app
slug: activity
status: readable
updated: 2026-11-18
---
# Activity (steps, calories, distance)

Daily movement totals and history.

- **Status:** `readable`
- **Images:** `./activity/` (see its README for where images come from)

## Features
- Steps, calories, distance
- History by day
- (maybe) set goals

## Data it has
- Synced via `01 C5 AA 01` history dump
- Decoded to JSON by the prior-art sync

## Can we manipulate it yet?
History sync is verified. Setting goals is in the SDK but not mapped yet.

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
