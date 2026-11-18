---
date: 2026-11-18
updated: 2026-11-18
stage: 04_develop
status: active plan (the owner's scope answers 2026-11-18)
---
# 04 Plan: rebuild WatchLink + GloryFitPro in the web app

## Goal
Every watch function the phone apps (WatchLink, GloryFitPro) offer, driven from the Control-Page web app
(`Control-Page/`, `http://localhost:8736/`), with each control verified on the wrist.

## The owner's answers (2026-11-18)
| Question | Answer |
|---|---|
| GloryFitPro APK | Downloaded latest + 3 previous from APKPure via `apkeep` (1.9.2, 1.9.0.3, 1.9.0.2, 1.8.6.2) into `apk/`. Same vendor signing cert on all, Google Play source stamp present. Phone: for an HCI snoop capture later. |
| Scope | **All of it:** watch settings + controls, health history sync + charts, watch-face editor + install, workouts + GPS tracks |
| OTA / firmware | **Map it, gate it later.** Document the flow; any firmware write needs the owner's explicit yes at the time (AGENTS rule 1 still stands) |
| Verification | **The owner tests, page tracks status.** Each control shows "mapped · untested" with a Works / Doesn't button; results are saved to the DB as `verify:<control>` keys |
| Emulator | Possible for running GloryFitPro's UI (arm64 AVD), but it has no Bluetooth passthrough, so it can't capture watch traffic. Ground truth needs the real phone. |

## Status by phase

**P1. Map the frames: WatchLink done, GloryFitPro in progress**
- WatchLink v1.15: done. Builders are in `decompiled/.../defpackage/wq1.java` (commands + reply parser) and `ks2.java` (settings).
  Full list in `05-app-controls.md`.
- GloryFitPro 1.8.6.2 → 1.9.2: a background REA/jadx pass is mapping the `com.yc.nadalsdk` command builders
  and diffing each version (new features / fixes / protocol changes). Output: `06-gloryfitpro-protocol-and-versions.md`.
- Still to do: history sync frames (sleep, HR/SpO2/stress series), workout + GPS track download, face install
  file format, OTA flow (documentation only).

**P2. Every control in the web app: built 2026-11-18, waiting for wrist tests**
- 18 app pages, each with its own URL (`/heart-rate`, `/alarms`, `/settings`, …, plus `/bluetooth-log`, `/lab`).
- Built and mapped from WatchLink: alarms (read + write), today summary (steps/kcal/distance/HR), auto-HR interval,
  HR high/low alerts, continuous SpO₂ + low alert, stress + mood monitoring, DND, sedentary + drink-water reminders,
  goals, body profile, raise-to-wake, disconnect alert, screen timeout, time format, units, language,
  call/SMS alert toggles, contacts push, music info push + watch music buttons → Mac Music/Spotify
  (`/api/media`), find-phone (the page rings), auto-reply to the watch's weather request, WatchLink set-time.
- Already proven before today: notifications, weather, vibrate, GPS push, face table read.
- No BLE control exists for the timer/stopwatch (it runs on the watch only) or dial scroll speed
  (no command in WatchLink).
- **Next:** the owner connects in Chrome, opens each app page, runs it, and clicks Works / Doesn't.

**P3. Health history sync + charts (next build)**
History frames `01 C6 AA 01 0A <from> <to> <idx>` with the record parser in `wq1.d()`
(steps/kcal/distance per minute, HR avg/min/max, BP, mood, HRV, SpO₂, blood sugar). Store in SQLite and chart per day.
Sleep and GloryFitPro-only records come from the 06 doc.

**P4. Watch-face editor + install**
Install replaces the oldest of the 4 downloadable slots (no delete needed). Switch frame `01 E3 AB 05 0A <id> "1.0.0" 01`
is wired (unverified). Still needed: the face file format and transfer (WatchLink `xs2.java` state machine, the
`ATSDialFactory` `.iwf` reference, GloryFitPro). Then the editor: background, time/date layout, colours, widgets, 240×296 preview.

**P5. Workouts + GPS tracks**
Download recorded workouts and tracks, match them to recordings by time. Frames come from GloryFitPro (06 doc).

**P6. Firmware / OTA (documentation only, gated)**
Map the OTA flow from the APKs. No writes to `e49a3002` without the owner's explicit yes for that specific action.
Dial scroll speed is likely a firmware constant, so only this route can change it.

## Phone (when charged)
1. USB debugging on, data cable, "File transfer" mode, then confirm `adb devices -l` shows `device`.
2. Enable "Bluetooth HCI snoop log" in Developer options, use GloryFitPro with the watch, then pull the
   bugreport. That capture is the ground truth for history sync, face install and workouts.
