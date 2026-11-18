---
kind: app
slug: weather
status: push-only
updated: 2026-11-18
---
# Weather

Current conditions and forecast shown on the watch.

- **Status:** `push-only`
- **Images:** `./weather/` (see its README for where images come from)

## Features
- Push now/high/low + icon
- City label

## Data it has
- Sent via subpackaged `01 E0` TLV

## Can we manipulate it yet?
Push to the watch is verified. The watch does not report weather back.

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
