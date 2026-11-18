---
date: 2026-11-18
stage: 05_test
status: plan + running log
---
# 07 Testing plan and log

Three kinds of test, all recorded in the Control-Page database (`Control-Page/data/ht36.db`):

| Test | Where results live | How to read them |
|---|---|---|
| A. Wrist verification of each control | `watch` table, keys `verify:<control>` (`works`/`fails` + time) | `GET /api/watch`, or the pill next to each control |
| B. Dual-wear accuracy comparison | `metrics` table, `source` = `ht36` / `apple` / `fitbit` / `browser`, `trial` = the test label | `GET /api/metrics.csv?trial=<label>` |
| C. Audio: voice capture, calling, music upload | this file (results table below) + Bluetooth logs (`sessions`/`frames`) | `GET /api/sessions` |

## What gets logged automatically
Every reading the watch sends is stored in `metrics` as one row: time, metric, value, unit, source, kind and test label.

| Metric | Unit | From | Kind |
|---|---|---|---|
| `steps`, `kcal`, `distance_m` | today's running totals | day summary `01 C3 AA AA` | summary |
| `hr` | bpm, timestamped by the watch | day summary (latest reading) | summary |
| `stress` | score, timestamped by the watch | `01 C6 AC 02` push | push |
| `battery` | % | battery / device info | live |
| `gps` | browser fix (accuracy m; lat/lon/alt in `extra`) | browser, if "also log this browser's location" is ticked | reference |
| `gps_push` | lat/lon in `extra` | every location the page pushes to the watch | push |
| `spo2`, `sleep_*`, `mood`, `workout`, per-minute history, watch GPS track points | (reserved) | history sync, not built yet (plan P3/P5) | history |

The **Recording** box under the twin sets the test label and how often to poll the summary and battery
(default every 1 minute while connected). Each health page shows its last 25 readings and a CSV download.
Duplicates are ignored, so re-syncing is safe.

## A. Wrist verification (each control)
Open each blue-dot page, run the control, and look at the watch. Click **Works** or **Doesn't**.
Status as of 2026-11-18: everything new is `untested`. Proven before that: notifications, weather,
vibrate, GPS push, face table read.

## B. Dual-wear comparison (future test)
**Setup:** wear the HT36 and the Apple Watch (or Fitbit) on the **same wrist**, one above the other, both snug.
Swap which one sits closer to the hand halfway through, so placement doesn't bias the result.

**Steps**
1. On the Control-Page, set the test label, e.g. `dual-wear apple 2026-12-01`, and poll every 1 min.
   Tick "log this browser's location" for outdoor walks (it gives the GPS reference track).
2. Run the protocol. Note start and end times in the results table below.
   - 10 min seated rest (resting HR, SpO₂)
   - 1,000 counted steps, walking (step accuracy: count them, or use a fixed track)
   - 20 min brisk walk or run outdoors with GPS on both watches (HR under load, distance, track)
   - 5 min recovery (HR return)
   - Overnight: wear both to sleep (sleep stages, overnight SpO₂, resting HR)
3. After the test, sync the HT36 history (P3) so per-minute data lands in `metrics` with `kind=history`.
4. Export the reference watch's data:
   - **Apple Watch:** iPhone Health → profile → *Export All Health Data* → `export.zip` (`export.xml` + workout GPX routes).
   - **Fitbit:** Google Takeout → Fitbit (JSON/CSV per metric) or the Fitbit Web API.
5. Import the reference data into `metrics` with `source=apple|fitbit`, the same `trial` and `kind=import`.
   (Importer script `Control-Page/scripts/import_reference.py`: to build, maps HKQuantityTypeIdentifierHeartRate /
   StepCount / OxygenSaturation / DistanceWalkingRunning and GPX trackpoints.)
6. Compare by timestamp: per-minute HR (mean absolute error, bias, lag), step totals, distance, SpO₂ spot
   checks, GPS track distance and offset in metres, sleep totals. Output a short report and charts.

**Results**

| Date | Trial label | Reference watch | Wrist / order | Activities | HR MAE (bpm) | Steps Δ % | Distance Δ % | GPS offset (m) | Notes |
|---|---|---|---|---|---|---|---|---|---|
| | | | | | | | | | |

## D. GPS Tracks + Voice notes pages (built 2026-11-18)
| # | Test | How | Result |
|---|---|---|---|
| D1 | GPX import | /workouts-gps/tracks → Import GPX… (Apple Health workout route, Fitbit, Strava) | headless: a 26-point GPX imported, 2.94 km, HR, splits, map tiles OK |
| D2 | Browser reference track | ● Record track on a laptop outdoors, walk 10 min, ■ Stop | |
| D3 | Mac-mic voice note | /voice-notes → ● Record, ■ Stop and save, play it back | headless (fake mic): 3.1 s note saved and reloaded |
| D4 | Watch voice button | Read watch voice feature → if on, press the watch's voice button and speak | |
| D5 | Watch audio format | After D4, check whether the saved note is audio/ogg (plays) or raw (.bin) | |

## C. Audio tests (to do)
The watch has a mic, a speaker and Bluetooth calling. Calling uses **classic Bluetooth (HFP)**, not BLE, so the
browser page can't carry the audio directly. What to test:

| # | Test | How | Result |
|---|---|---|---|
| C1 | Does the watch pair to the Mac as a classic-BT headset? | Mac → System Settings → Bluetooth: look for a second "HT36…" entry (often "-Call" or similar) and pair it | |
| C2 | If yes, does the watch mic show up as a Mac input? | System Settings → Sound → Input. If it appears, the page can record it with `getUserMedia` and send voice notes to a companion backend transcript pipeline tagged `watch` (the owner's 2026-11-17 choice) | |
| C3 | Voice assistant / voice memo button on the watch | Press it while the page is connected and watch the Bluetooth log for new frames | |
| C4 | Music upload (MP3 to the watch) | Only if GloryFitPro has it (being checked in `docs/06`). WatchLink has control only | |
| C5 | Calls ring on the watch | Pair with the Android phone, call it, check the watch rings and audio works | |
