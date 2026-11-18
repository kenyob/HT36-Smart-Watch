---
kind: app
slug: calling
status: unmapped
updated: 2026-11-18
---
# Bluetooth calling

The watch's phone/dialer over Bluetooth HFP.

- **Status:** `unmapped`
- **Images:** `./calling/` (see its README for where images come from)

## Features
- Incoming-call alert
- Answer/hang up
- Dialer

## Data it has
- Not confirmed on this unit

## Can we manipulate it yet?
The owner believes the watch has calling. Call-alert frames exist in the SDK (`notifyIncomingCall`), unmapped. Voice recording depends on this — needs confirming on the watch menu.

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
