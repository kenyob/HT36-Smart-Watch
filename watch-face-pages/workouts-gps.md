---
kind: app
slug: workouts-gps
status: partial
updated: 2026-11-18
---
# Workouts + GPS

Workout sessions with multi-GNSS GPS tracks.

- **Status:** `partial`
- **Images:** `./workouts-gps/` (see its README for where images come from)

## Features
- Workout history
- GPS tracks (goal: download)
- Push a location to the watch
- Pace, HR per section

## Data it has
- GNSS: GPS + BeiDou + Galileo (`01 E9 AA 01`)
- Workout history via `01 E8 AA 01`
- Location push via `01 E9 AB 02`

## Can we manipulate it yet?
Workout history sync and location push are verified. **Downloading the recorded GPS track** (`getRecordGpsInfo` / `downloadRecordGpsFile`) is in the SDK but not mapped yet — a priority.

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
