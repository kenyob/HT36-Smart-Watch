---
kind: app
slug: find
status: partial
updated: 2026-11-18
---
# Find phone / find watch

Make the watch (or phone) ring/vibrate.

- **Status:** `partial`
- **Images:** `./find/` (see its README for where images come from)

## Features
- Vibrate the watch
- (maybe) ring the phone

## Data it has
- Vibrate verified (`01 A5 AB 04 01 01`)
- Find-wear state (`01 A5 AA 07`)

## Can we manipulate it yet?
Vibrate the watch is verified. Find-phone (watch→phone trigger) is unmapped.

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
