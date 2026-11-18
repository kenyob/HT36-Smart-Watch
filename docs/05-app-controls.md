---
date: 2026-11-18
stage: 04_develop
source: WatchLink v1.15 APK, decompiled (decompiled/WatchLink), REAP "trace a feature" workflow
---
# 05 Controls found in the decompiled apps

The WatchLink BLE code (`decompiled/.../defpackage/fg.java` and neighbours) leaves **descriptive labels on
every command frame**, so the decompile reads almost like documentation. The frames below are decimal in the
source; shown here as hex.

## Confirmed: WatchLink's protocol matches OUR watch
`face info` in the app is `01 E3 AA AA` — byte-for-byte what our HT36 answered in the 2026-11-18 probe. So
WatchLink targets the same E-group protocol our watch speaks (it ships for AT364CD/P131, our watch is AT364D,
same family). **Its face and settings frames apply to us.**

## Command inventory (labelled frames from the app)
| Label (dev's own) | Frame (hex) | Notes |
|---|---|---|
| battery | `A2` | app uses A2; our probe used `01 A4 AA 16` — both exist |
| serial | `A1` | |
| handshake | hex blob on the JL channel | `0808442a…` |
| set time | `01 A3 01 04 <epoch s, 4B BE> 10 02 <tz h \| 0x80 east of UTC> <tz min ×100/60>` | **Correction 2026-11-18:** "seconds" means epoch seconds; this is the frame the page already used. The y/m/d/h/m/s variant was a misreading and has been removed |
| today's activity | `26 01` | steps/cal/dist for a day |
| heart-rate history | `F7 FA` + date | |
| SpO2 history | `34 FA` + date | |
| find watch | `D2 <01/00>` | buzz the watch |
| **enable find-phone** | `01 A5 AB 0A 01 01` | NEW — make the phone ring from the watch |
| notification | `12 <b> <len> <payload>` | |
| contacts start / commit | `01 C0 AB 06 01 00` / `01 C0 AB 09 01 01` | push phone contacts |
| **face info** | `01 E3 AA AA` | matches our probe |
| **photo face state** | `01 E3 AA 0C` | |

These are directly usable: each is a safe addition to the Control-Page (queries especially).

## The big one: custom faces are NOT blocked after all
The prior-art project (tcsenpai/ht36) concluded custom faces were blocked because the watch was "full at 9
faces" and it couldn't find a delete frame. WatchLink's own UI text corrects this:

> "The watch keeps **one always-on face and 4 downloaded faces**; **installing replaces the oldest** of that
> kind." · "Edited faces get a new id (9xx) so they don't clash with the original."

So you don't need a delete command — **installing a new face automatically evicts the oldest downloaded one**.
The 9 faces we saw are mostly built-in; the install path writes into the 4 downloadable slots. This is the
route to the clock-face editor goal.

WatchLink's editor does: *dim an always-on face, recolour or move its parts, hide parts, swap the clock style,
put a custom background behind it, then install.* That is the feature set to rebuild in the Control-Page face editor.

## Your two questions, answered
1. **Can we push the watch to a screen in parallel (open the same app on the wrist as on the web page)?**
   **No.** Nothing in the app sends a "navigate to app / open screen" command — the watch's app navigation is
   local (crown + buttons). What BLE *can* do is **switch the active watch face** (`applyWatchFace`). So the twin
   on the web page mirrors state; the watch can be driven to a *face*, but not made to open the HR/weather/etc.
   app screen on command. (If this matters, a custom face can be built to look like a given app.)
2. **Are there older APKs to compare with REA?** Yes — **24 WatchLink releases, v1.1 (2026-11-01, 3.2 MB) →
   v1.24 (2026-11-14, 5.0 MB)**. The big jumps (v1.4→v1.5: 3.6→4.5 MB; v1.11→v1.12) are where features landed.
   A REA version-diff (`compare_android_*`) between an early and a late build shows exactly which frames/features
   were added — a fast way to find the face-install and settings code without reading all 3,711 obfuscated lines.

## Face control extracted (install state machine = `defpackage/xs2.java`)
- **Apply / switch a face:** `01 E3 AB 05 0A <id 4B BE> "1.0.0" <operate=01>` (id = `00` + 3-byte face id).
  Now wired into the Control-Page faces grid — click a face tile to switch it (unverified on hardware).
- **Install a custom face:** the E3 subpackaged file transfer the prior-art project already built. It was only
  ever "blocked" by the full-slots misread; installing replaces the oldest downloadable face. State machine
  (slot / transferNum / progress / currentFaceId / dialect) is in `xs2.java`.
- **Alarms are mappable after all** (`defpackage/mp2.java`, `Alarms(slots=…)`) — not firmware-locked.

## Next
- ~~Add the safe new frames to the Control-Page~~ done 2026-11-18 (see the full table below).
- Trace the face **install** state machine in WatchLink (the `C0`/`E3` install path, `currentFaceId`, `dialect`)
  to build the face editor.
- Optionally download v1.1 + v1.12 + v1.24 and diff with REA to confirm the install frames.

## Full WatchLink frame map (2026-11-18, from `wq1.java` + `ks2.java`) — all wired into the Control-Page
`set1(g,op,v)` = `01 g AB op 01 v`. `sect(g,sub,p)` = `01 g AB sub <sect> p…` then `01 g AB sub FD <xor of all frames>`.
`g1(t,v)` = `AB t 01 v`. Times are `hh mm` bytes; multi-byte numbers are big-endian.

| Feature | Frame | Reply / event |
|---|---|---|
| today summary | `01 C3 AA AA` | sectioned; records `AA tag len val`: 2 = HR, 3 = time, 12 = nested `tag len val` (5 steps, 1 kcal, 2 metres) |
| read alarms | `01 C7 AA AA` | sectioned; per alarm `AA 01 01 idx`, `AA 02 01 days`, `AA 03 01 on`, `AA 04 02 h m`. Our watch: none set |
| write alarms | `sect(C7,AB, per alarm i: AB 01 02 i i · AB 02 02 i days · AB 03 02 i on · AB 04 03 i h m · AB 05 01 i)` | days bit 0 = Sunday |
| auto HR | `set1(E1,02,on)` + `sect(E1,AB, g1(2,1) g1(11,min 1–60))` | `01 E1 AC 07 … min`, `01 E1 AC 0C … on` |
| HR high / low alert | `01 E1 AB 03 02 on bpm` / `01 E1 AB 04 02 on bpm` | |
| stress monitor | `sect(E1,AB, g1(7,on) g1(13,min))` | stress push `01 C6 AC 02 len <time 4B> val` |
| mood monitor | `set1(E1,0E,on)` | |
| continuous SpO₂ / low alert | `set1(C4,03,on)` / `01 C4 AB 04 02 on pct` | |
| sedentary reminder | `01 C4 AB 01 08 on <every 2B> from_h from_m to_h to_m 7F` | |
| drink-water reminder | `01 F2 AB 01 07 on from_h from_m to_h to_m <every 2B>` | |
| do not disturb | `01 EA AB 01 08 allday scheduled from_h from_m to_h to_m novib nomsg` | |
| goals | `sect(C1,AB, g1(1,1) g1(2,1) AB 03 04 steps · AB 04 02 kcal · AB 05 04 metres · AB 06 02 seconds)` | |
| profile | `sect(C2,AB, age, AB 02 04 year month day, male, height, 0, AB 06 04 0000, run stride .548h, walk stride .405h, weight, right-wrist)` | |
| raise to wake / disconnect alert / screen timeout | `set1(A5,01,on)` / `set1(A5,05,on)` / `set1(A5,08,s)` (5/10/15/20/30) | settings group `01 A5 AA 01` → `tag 01 val` per op |
| language / length / weight unit | `set1(A5,06,idx)` / `set1(A5,07,mi)` / `set1(A5,09,lb)` | languages list `01 A5 AA 03` |
| temperature unit | `set1(E0,02,F)` | `01 E0 AC 03 … unit` |
| 12/24 h | `01 A3 04 01 03 08 01 <1=12h, 2=24h>` | |
| call / SMS alerts | `set1(B2,01,on)` / `set1(C0,09,on)` | |
| contacts | `01 C0 AB 06 01 00`, data `01 C0 AB 07 <off 2B> <n> …`, end `01 C0 AB 07 FD xor`, commit `01 C0 AB 09 01 01` | entry `[len num][len name]` UTF-16BE |
| music info | `sect(E2,AB, AB 01 artist · AB 02 title (UTF-16BE) · g1(3, 3 playing/2 paused) · g1(4,vmax) · g1(5,vol))` | buttons `01 E2 xx 01 02 cmd`: 1 play 2 pause 3 prev 4 next 5 vol+ 6 vol− |
| find watch | `01 A5 AB 04 01 on/off` | find-phone from watch `01 A5 AC 02 xx on` |
| weather request | — | watch asks `01 E0 AC 02`; the page answers with the weather frame |
| history | `01 C6 AA 01 0A <from 4B> <to 4B> <idx 2B>` | count `01 C5 AA 01/04`; parser `wq1.d()`. Not built yet (P3) |
