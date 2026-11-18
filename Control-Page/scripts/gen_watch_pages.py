#!/usr/bin/env python3
"""Generate one markdown page per HT36 app and per installed watch face, each with an image subfolder.

Output: HT36-Smart-Watch/watch-face-pages/
  <slug>.md                     description, features, data, and manipulation status
  <slug>/README.md              what images belong here and where they come from

Re-run any time the frame map changes: it rewrites the .md files and leaves the image folders alone
(it only creates a folder's README if missing, so your dropped-in images are never touched).

Status vocabulary:
  controllable  — we can read AND change it with a verified frame
  readable      — we can read it; changing it isn't mapped yet
  push-only     — we can send it to the watch (no read-back)
  partial       — some of it works (see notes)
  unmapped      — no frame known yet
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2] / "watch-face-pages"

# ---- Apps / features on the watch ----
APPS = [
    ("watch-faces", "Watch faces", "partial",
     "The face system: which dial is shown and (goal) custom dials.",
     ["Switch the active face", "List installed faces", "Slot/widget layout", "(goal) upload a custom face"],
     ["9 faces installed (at the 9-face cap)", "Screen 240×296", "Each face: 3-byte id, type, version 1.0.0", "Slot config via 01 E3 AA 0C"],
     "Read works (`01 E3 AA AA/0B/0C`). Switch is mapped. **Custom upload is blocked**: the watch is full and the "
     "known 'sort' frame reorders but does not delete. The delete/install frames are being pulled from the WatchLink APK."),
    ("activity", "Activity (steps, calories, distance)", "readable",
     "Daily movement totals and history.",
     ["Steps, calories, distance", "History by day", "(maybe) set goals"],
     ["Synced via `01 C5 AA 01` history dump", "Decoded to JSON by the prior-art sync"],
     "History sync is verified. Setting goals is in the SDK but not mapped yet."),
    ("heart-rate", "Heart rate", "partial",
     "Heart-rate monitoring and history.",
     ["Auto/continuous HR toggle", "Measurement interval", "High/low alerts", "History"],
     ["Auto-HR enable state (`01 E1 AA 10` → on)", "HR values come from history sync, not a live stream"],
     "Enable-state reads. Toggles (`01 E1 AB 01/02`) are mapped but untested. The watch does NOT push live bpm; "
     "HR is read from the fitness-history sync."),
    ("blood-oxygen", "Blood oxygen (SpO2)", "partial",
     "SpO2 monitoring.",
     ["Auto SpO2 toggle", "Reminders", "History"],
     ["Auto-SpO2 enable state (`01 E1 AA 11` → on)"],
     "Enable-state reads. Set frames mapped, untested."),
    ("stress", "Stress", "readable",
     "Stress measurement and history.",
     ["Auto stress toggle", "History"],
     ["Stress history via sync"],
     "History mapped in the SDK; toggle untested."),
    ("sleep", "Sleep", "readable",
     "Sleep tracking with stages.",
     ["Sleep stages", "History"],
     ["Sleep history via `01 C6 AA 04` file transfer"],
     "Download path mapped; read-only."),
    ("workouts-gps", "Workouts + GPS", "partial",
     "Workout sessions with multi-GNSS GPS tracks.",
     ["Workout history", "GPS tracks (goal: download)", "Push a location to the watch", "Pace, HR per section"],
     ["GNSS: GPS + BeiDou + Galileo (`01 E9 AA 01`)", "Workout history via `01 E8 AA 01`", "Location push via `01 E9 AB 02`"],
     "Workout history sync and location push are verified. **Downloading the recorded GPS track** "
     "(`getRecordGpsInfo` / `downloadRecordGpsFile`) is in the SDK but not mapped yet — a priority."),
    ("weather", "Weather", "push-only",
     "Current conditions and forecast shown on the watch.",
     ["Push now/high/low + icon", "City label"],
     ["Sent via subpackaged `01 E0` TLV"],
     "Push to the watch is verified. The watch does not report weather back."),
    ("notifications", "Notifications", "push-only",
     "App and message notifications pushed to the wrist.",
     ["Push text (paged)", "Enable notifications gate", "Supported message types"],
     ["`01 B2` enable gate, `01 B0` TLV push", "2 message types reported (`01 B3 AA AA`)"],
     "Verified: enable then push renders on the wrist. Incoming SMS reply/voice is in the SDK, unmapped."),
    ("alarms", "Alarms", "unmapped",
     "On-watch alarms.",
     ["Set/list alarms"],
     ["Not read yet"],
     "No frame mapped. In the SDK surface; needs a sweep or the app teardown."),
    ("timer-stopwatch", "Timer & stopwatch", "unmapped",
     "On-watch timer and stopwatch.",
     ["Likely local-only on the watch"],
     ["Not read"],
     "Probably a local watch app with no BLE control. Confirm from the app teardown."),
    ("music-control", "Music control", "unmapped",
     "Control phone music from the watch.",
     ["Play/pause/next/volume", "Now-playing info"],
     ["Not read"],
     "In the SDK (`queryAllMusicFile`, playback). Direction and frames unmapped."),
    ("find", "Find phone / find watch", "partial",
     "Make the watch (or phone) ring/vibrate.",
     ["Vibrate the watch", "(maybe) ring the phone"],
     ["Vibrate verified (`01 A5 AB 04 01 01`)", "Find-wear state (`01 A5 AA 07`)"],
     "Vibrate the watch is verified. Find-phone (watch→phone trigger) is unmapped."),
    ("calling", "Bluetooth calling", "unmapped",
     "The watch's phone/dialer over Bluetooth HFP.",
     ["Incoming-call alert", "Answer/hang up", "Dialer"],
     ["Not confirmed on this unit"],
     "the owner believes the watch has calling. Call-alert frames exist in the SDK (`notifyIncomingCall`), unmapped. "
     "Voice recording depends on this — needs confirming on the watch menu."),
    ("settings", "Settings", "partial",
     "Device settings: time, screen, units, language, reminders.",
     ["Set time", "Screen-on time / brightness / raise-to-wake", "Units, language", "Sedentary / DND reminders", "Dial scroll speed (goal)"],
     ["7 config toggles (`01 A5 AA 01`, only #5 on)", "Set-time acks but does not change the clock on this fw"],
     "Mostly unmapped. **Set-time** (`01 A3`) is acknowledged but the clock doesn't change — the frame differs on "
     "this firmware. **Dial scroll speed** has no known SDK method and may be a firmware constant."),
]

# ---- Installed faces (ids from the 2026-11-18 probe, 01 E3 AA 0B) ----
FACE_IDS = ["18af79", "18a7a9", "18ab91", "c88021", "1e7fc1", "1e83a9", "809dc9", "3abe39", "a17719"]
FACE_TYPES = {"1e83a9": "03 (special/AOD?)", "3abe39": "22 (special)", "a17719": "04 (special)"}


def md_app(slug, name, status, desc, features, data, notes):
    return f"""---
kind: app
slug: {slug}
status: {status}
updated: 2026-11-18
---
# {name}

{desc}

- **Status:** `{status}`
- **Images:** `./{slug}/` (see its README for where images come from)

## Features
{chr(10).join('- ' + f for f in features)}

## Data it has
{chr(10).join('- ' + d for d in data)}

## Can we manipulate it yet?
{notes}

> Frames and verification live in `../docs/01-discover.md` and the prior-art wiki. Update this file when the
> frame map changes (`Control-Page/scripts/gen_watch_pages.py`).
"""


def md_face(fid):
    typ = FACE_TYPES.get(fid, "02 (normal)")
    return f"""---
kind: watch-face
id: {fid}
type: {typ}
status: switch-only
updated: 2026-11-18
---
# Watch face {fid}

An installed dial on the watch. Over BLE the watch exposes only this metadata (id, type, version), never the
full bitmap — so we cannot pull the actual face image off the device. The real face file comes from the UTE
cloud by this id, or from the WatchLink/GloryFitPro app cache.

- **Face id:** `{fid}` (3-byte id; on the wire 4-byte big-endian `00{fid}`)
- **Type:** `{typ}`
- **Version:** 1.0.0
- **Status:** `switch-only` — we can select it; we cannot yet read its bitmap or delete it to free a slot.
- **Images:** `./face-{fid}/` (see its README)

## Can we manipulate it yet?
Switching is mapped. The watch is at the 9-face cap, and deleting a face to make room is **not yet mapped**
(the known 'sort' frame reorders only). Custom upload is blocked until the delete frame is found in the app.
"""


def folder_readme(title, is_face):
    src = (
        "We cannot capture the watch screen or a baked-in face bitmap over Bluetooth. Fill this folder from one of:\n\n"
        "1. **Browser replica** — a PNG of the Control-Page watch twin for this item (what we render from live state).\n"
        "2. **Your photos** — drop in photos you take of the watch showing this screen/face.\n"
        "3. **The face file** — once we fetch it from the UTE cloud (by id) or the app cache, a rendered preview.\n"
    )
    return f"# Images — {title}\n\n{src}\nName files clearly, e.g. `replica.png`, `photo-01.jpg`, `cloud-preview.png`.\n"


def main():
    ROOT.mkdir(exist_ok=True)
    (ROOT / "README.md").write_text(
        "# Watch face & app pages\n\n"
        "One markdown page per HT36 app/feature and per installed watch face, each with an image subfolder.\n"
        "Generated by `../Control-Page/scripts/gen_watch_pages.py` — edit there and re-run.\n\n"
        "Image folders can't be filled from the watch over BLE (it doesn't stream its screen); see each folder's README.\n",
        encoding="utf-8")
    n_app = n_face = 0
    for slug, name, status, desc, features, data, notes in APPS:
        (ROOT / f"{slug}.md").write_text(md_app(slug, name, status, desc, features, data, notes), encoding="utf-8")
        d = ROOT / slug; d.mkdir(exist_ok=True)
        rm = d / "README.md"
        if not rm.exists():
            rm.write_text(folder_readme(name, False), encoding="utf-8")
        n_app += 1
    for fid in FACE_IDS:
        (ROOT / f"face-{fid}.md").write_text(md_face(fid), encoding="utf-8")
        d = ROOT / f"face-{fid}"; d.mkdir(exist_ok=True)
        rm = d / "README.md"
        if not rm.exists():
            rm.write_text(folder_readme(f"face {fid}", True), encoding="utf-8")
        n_face += 1
    print(f"wrote {n_app} app pages + {n_face} face pages into {ROOT}")


if __name__ == "__main__":
    main()
