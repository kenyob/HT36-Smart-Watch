---
kind: app
slug: notifications
status: push-only
updated: 2026-11-18
---
# Notifications

App and message notifications pushed to the wrist.

- **Status:** `push-only`
- **Images:** `./notifications/` (see its README for where images come from)

## Features
- Push text (paged)
- Enable notifications gate
- Supported message types

## Data it has
- `01 B2` enable gate, `01 B0` TLV push
- 2 message types reported (`01 B3 AA AA`)

## Can we manipulate it yet?
Verified: enable then push renders on the wrist. Incoming SMS reply/voice is in the SDK, unmapped.

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
