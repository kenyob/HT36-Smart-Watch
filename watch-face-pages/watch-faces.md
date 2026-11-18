---
kind: app
slug: watch-faces
status: partial
updated: 2026-11-18
---
# Watch faces

The face system: which dial is shown and (goal) custom dials.

- **Status:** `partial`
- **Images:** `./watch-faces/` (see its README for where images come from)

## Features
- Switch the active face
- List installed faces
- Slot/widget layout
- (goal) upload a custom face

## Data it has
- 9 faces installed (at the 9-face cap)
- Screen 240×296
- Each face: 3-byte id, type, version 1.0.0
- Slot config via 01 E3 AA 0C

## Can we manipulate it yet?
Read works (`01 E3 AA AA/0B/0C`). Switch is mapped. **Custom upload is blocked**: the watch is full and the known 'sort' frame reorders but does not delete. The delete/install frames are being pulled from the WatchLink APK.

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
