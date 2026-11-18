---
kind: watch-face
id: 3abe39
type: 22 (special)
status: switch-only
updated: 2026-11-18
---
# Watch face 3abe39

An installed dial on the watch. Over BLE the watch exposes only this metadata (id, type, version), never the
full bitmap — so we cannot pull the actual face image off the device. The real face file comes from the UTE
cloud by this id, or from the WatchLink/GloryFitPro app cache.

- **Face id:** `3abe39` (3-byte id; on the wire 4-byte big-endian `003abe39`)
- **Type:** `22 (special)`
- **Version:** 1.0.0
- **Status:** `switch-only` — we can select it; we cannot yet read its bitmap or delete it to free a slot.
- **Images:** `./face-3abe39/` (see its README)

## Can we manipulate it yet?
Switching is mapped. The watch is at the 9-face cap, and deleting a face to make room is **not yet mapped**
(the known 'sort' frame reorders only). Custom upload is blocked until the delete frame is found in the app.
