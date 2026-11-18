---
kind: app
slug: settings
status: partial
updated: 2026-11-18
---
# Settings

Device settings: time, screen, units, language, reminders.

- **Status:** `partial`
- **Images:** `./settings/` (see its README for where images come from)

## Features
- Set time
- Screen-on time / brightness / raise-to-wake
- Units, language
- Sedentary / DND reminders
- Dial scroll speed (goal)

## Data it has
- 7 config toggles (`01 A5 AA 01`, only #5 on)
- Set-time acks but does not change the clock on this fw

## Can we manipulate it yet?
Mostly unmapped. **Set-time** (`01 A3`) is acknowledged but the clock doesn't change — the frame differs on this firmware. **Dial scroll speed** has no known SDK method and may be a firmware constant.

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
