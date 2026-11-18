# HT36 Smart Watch: an open web app for a closed smartwatch

Control a low-cost **HT36 GPS smartwatch** from a web browser over Bluetooth, without the vendor's phone app.
We worked out the watch's Bluetooth protocol by probing it directly and by statically analysing the two Android
apps that support it. Then we rebuilt their features as a local web app with its own database, so the data
the watch collects (steps, heart rate, SpO₂, stress, GPS tracks, voice) stays on your own machine.

> **Status (November 2026):** early but working. The connection, logging and about 70 controls are built.
> A few are proven on the wrist; most are mapped from the vendor apps and waiting for wrist tests.
> Nothing here writes firmware.

<!-- -->

> Not affiliated with the watch maker or the app developers. No vendor code, APKs or firmware are in this
> repository. The docs describe the protocol in our own words, for interoperability.

## The watch

| | |
|---|---|
| Model | "HT36" GPS smartwatch, sold under several brands. Bluetooth name `HT36`, MAC prefix `78:02:B7` |
| Where to get it | The unit this project uses: [Amazon B0FDGPTYJN](https://www.amazon.com/dp/B0FDGPTYJN) (also sold on Alibaba as "HT36 … ATS3085L … GloryFitPro") |
| Firmware | `AT364DV003105` (Actions ATS3085-family SoC; vendor SDK "JX platform") |
| Screen | 2.01" LCD, 240 × 296 |
| GNSS | GPS + BeiDou + Galileo (as reported by the watch) |
| Sensors | heart rate, SpO₂, accelerometer; mic and speaker for Bluetooth calling |
| Radios | BLE (this project) plus a separate classic-Bluetooth radio used only for call audio |
| Vendor apps | **GloryFitPro** (`com.yc.gloryfitpro`, SDK `com.yc.nadalsdk`) and the community app **WatchLink** |

## Other watches that should work (not yet confirmed)

The web app speaks the protocol of GloryFitPro watches built on the **Actions ATS3085 ("JX") platform**. Other
watches on that platform should work too, but **none of these has been tested with this project yet**. If you own
one, please [open a "Watch report" issue](../../issues/new?template=watch-report.md): connect, click
**Log all Bluetooth info**, and attach the firmware string and the log.

**Likely.** Same firmware family, or direct protocol evidence:

| Watch | Evidence | Confidence |
|---|---|---|
| **HT36** (this one: firmware `AT364D…`, sold under several brand names) | Tested here | ✅ works (partly verified) |
| **P131** (firmware `AT364C` / `AT364CD`) | WatchLink is written for it, and its frames match ours byte for byte (`docs/05`) | likely |
| Any watch whose firmware string (Settings → About, or the page's Firmware field) starts with **`AT364`** | Same firmware line as the HT36 | likely |
| **DM58** (brandless GPS watch, GloryFitPro) | Gadgetbridge's GloryFitPro support is built against it; same app and SDK | likely |
| **DM76** (GPS watch, GloryFitPro) | Same app; seller listings say ATS3085-class | likely |
| **AT338 / AT338V** firmware | Named inside the GloryFitPro watch SDK (`jx/q3`) as JX-platform products | likely |

**Possible.** GloryFitPro watches whose chip we haven't confirmed:

| Watch | Why it might work | Caveat |
|---|---|---|
| ChiBear **MK68-015**, HELLO-WATCH | XDA's GloryFitPro watch-face tools; reported ATS3085P | different screen size, so faces won't fit |
| **AT325**, Blackview **W60**, Zeblaze **Stratos 2**, Aolon **Mars R3**, "Glory Fit Pro" **W10 Pro**, **VG53 Pro** | Listed by sellers or app aggregators as GloryFitPro watches | could be on another chip platform |

**Probably not.** These use a different protocol:
- watches on the older **GloryFit** app (not *Pro*), such as the Q18 series
- GloryFitPro watches on the **JieLi AC701** or **"RK"** platforms (for example firmware `AT396C`). The SDK
  handles those through separate code paths.

How to tell: GloryFitPro identifies the platform from two plain Bluetooth reads that change nothing on the watch
([issue #2](../../issues/2) adds them to the page). Until then, a firmware string starting `AT3…` plus a working
**Log all Bluetooth info** sweep is a good sign.

## Quick start

You need Chrome or Edge (Web Bluetooth) on macOS, Windows, Linux or Android, and Python 3.9+. Nothing else.

```bash
git clone <this repo> && cd HT36-Smart-Watch/Control-Page
python3 server.py            # → http://localhost:8736/
python3 -m unittest test_server
```

Open http://localhost:8736/, click **Connect watch** and pick `HT36`. Close the vendor phone app first: the watch
takes one Bluetooth connection at a time. Every frame sent and received appears in the **Bluetooth log** tab.

## What the web app does today

Each watch app has its own page and URL (`/heart-rate`, `/alarms`, `/settings`, …). A coloured dot shows how far
each one has got:

| Dot | Meaning | Apps |
|---|---|---|
| 🟢 proven | works on the wrist | Weather, Notifications |
| 🟡 partial | some of it proven | Watch faces (list + switch), Find (vibrate proven), Workouts + GPS (location push proven), Sleep (read-only, waits for history sync) |
| 🔵 mapped | built from the vendor apps' frames, **not yet tested on the wrist** | Activity, Heart rate, Blood oxygen, Stress, Alarms, Music control, Calling + contacts, Do not disturb, Reminders, Goals + profile, Settings |
| 🔴 none | no Bluetooth control exists | Timer & stopwatch (runs on the watch only) |
| **NEW** | features we're adding on top of the watch's own apps | **GPS tracks** (`/workouts-gps/tracks`), **Voice notes** (`/voice-notes`) |

More detail:
- **Settings:** raise to wake, disconnect alert, screen timeout, 12/24 h, units, language, set time.
- **Health:** auto heart-rate interval and alerts, continuous SpO₂ and low alert, stress and mood monitoring,
  sedentary and drink-water reminders, do not disturb, daily goals, body profile.
- **Alarms:** read the watch's alarms, edit them, write them back.
- **Music:** push now-playing info. The watch's music buttons can control Music or Spotify on a Mac.
- **Find:** buzz the watch. When the watch looks for the phone, the page rings.
- **Weather:** answered automatically when the watch asks.
- **Contacts:** pushed to the watch's dialer. Call audio itself needs a phone (classic Bluetooth).
- **Health logging:** every reading the watch sends goes into a `metrics` table with time, value, unit, source and an
  optional test label. You can poll every minute and export CSV. The source column is there so Apple Watch or Fitbit data can
  sit alongside for a **dual-wear accuracy test** ([docs/07](docs/07-testing-plan-and-log.md)).
- **GPS tracks (new):** record a reference track from the browser, or import GPX from Apple Health, Fitbit or Strava.
  Tracks are shown by day on an OpenStreetMap map with distance, time, splits and heart rate.
- **Voice notes (new):** record from the computer's mic, or from the watch's mic, which streams Opus over BLE when the
  watch has its AI-voice feature. Audio is kept for local transcription later.
- **Wrist verification:** every untested control has **Works / Doesn't** buttons; results are saved, so the
  status above can be updated from real tests.
- **Lab:** send raw frames by hand.

## How we got here

1. **Discovery.** A passive BLE scan found the watch; read-only GATT discovery mapped 5 services and 14
   characteristics. The watch is not visible over USB (the magnetic charger is power only). Notes: [docs/01](docs/01-discover.md).
2. **Prior art.** [`tcsenpai/ht36`](https://github.com/tcsenpai/ht36) (MIT) had mapped the frame envelope, notifications,
   weather and GPS push. Its logic was ported into the web app, and its copyright notice is kept.
3. **First live probe.** Read-only queries confirmed the firmware, battery, device info, settings group and face table.
   Every reply matched the reference decoder.
4. **WatchLink teardown.** WatchLink v1.15 was decompiled. Its developers labelled each command frame, which gave us
   alarms, settings, health monitors, reminders, goals, profile, music, contacts and find. It also corrected two
   earlier misreadings, and showed that installing a face replaces the oldest one (no delete needed).
   Map: [docs/05](docs/05-app-controls.md).
5. **GloryFitPro teardown.** Four versions (1.8.6.2 → 1.9.2) were analysed statically, never installed or run.
   That gave us the full command set: history sync, sleep, workouts, GPS track download, face install and delete,
   photo faces, caller ID, music upload, the Opus voice stream, and the capability bitmaps. A version diff shows
   what each release changed. The watch commands are byte-identical across all four. Map: [docs/06](docs/06-gloryfitpro-protocol-and-versions.md).
6. **The web app.** A standard-library Python service plus a single-file page (HTML, CSS and JS), with SQLite storage:
   - per-app pages with their own URLs
   - reply decoders
   - wrist-verification tracking
   - health metrics
   - GPS tracks and voice notes

   It has 15 automated tests.

## The protocol in one paragraph

Commands go to characteristic `34F1` (service `56FF`) and replies come back on `34F2`. Every frame is
`01 <group> <AA query | AB set | AC event> <op> …`. Large payloads are split into sections
(`01 <group> AB <sub> <n> …`) and end with `01 <group> AB <sub> FD <xor>`. A one-byte `A1` handshake goes on `35F1`.
Feature support comes from plain reads of `35F1` / `34F1` (13 bitmaps).
The firmware-update service (`e49a…`) is never touched: the page doesn't even list it, so the browser can't reach it.

## Roadmap

| Phase | What | State |
|---|---|---|
| P1 | Map every frame from the vendor apps | done for WatchLink and GloryFitPro |
| P2 | Every control in the web app | built; **wrist tests in progress** |
| P3 | Health history sync + charts: per-minute steps, HR, SpO₂, HRV, sleep stages, stress | frames mapped, not built |
| P4 | Watch-face install, delete and an editor (background, layout, colours, widgets, live 240 × 296 preview) | frames mapped, not built |
| P5 | Workouts + the watch's own GPS tracks, synced into the GPS Tracks page | frames mapped, not built |
| P6 | Firmware update flow | documented only; never used without an explicit decision |
| Audio | Watch-mic voice notes (BLE Opus), local Whisper transcription, MP3 upload to the watch | page built; transcription and upload not built |
| Test | Dual-wear comparison against an Apple Watch or Fitbit on the same wrist | plan written; importer not built |

## Not built yet

- **Health history sync and charts.** Per-minute data, sleep stages, stress and SpO₂ history (P3).
- **The watch's own workouts and GPS tracks.** List, summary, detail and track download; until then the GPS Tracks
  page shows browser and GPX tracks only (P5).
- **Watch faces.** Install, delete and editor (P4); photo faces.
- **Capability read.** Reading the 35F1 / 34F1 bitmaps, to know which features this watch has.
- **Transcription.** Whisper on a GPU machine for voice notes.
- **Decoding the watch's raw voice stream**, if it isn't Ogg.
- **Music upload to the watch.** File service, slow over BLE.
- **Caller ID and call-action frames**, and the classic-Bluetooth state query.
- **Importer for Apple Health and Fitbit exports**, for the dual-wear test.
- **Reaching the web app from a phone.** It works over USB port forwarding or HTTPS only.
- **Crown or dial scroll speed.** No command exists in either app; it is likely a firmware constant.

## Safety rules

- Never write to the firmware-update characteristic. One wrong byte can brick the watch.
- Queries (`AA`) are safe. Settings (`AB`) are sent only from mapped builders, and each one is marked untested
  until it's verified on the wrist.
- Vendor apps are analysed statically only: never installed or run, and never redistributed.

## Repository layout

```
Control-Page/        the web app: server.py, page-body.html, db.py, resources.py, tests, BLE probe scripts
docs/                01 discover · 04 plan · 05 WatchLink frames · 06 GloryFitPro protocol + versions · 07 testing plan + log
watch-face-pages/    one page per watch app and installed face (notes + replica images)
Skills/              REAP reverse-engineering workflows (MIT, see Skills/REAP-LICENSE)
```

## Discussion

- [r/ReverseEngineering](https://www.reddit.com/r/ReverseEngineering/comments/1xzmxpp/mapping_a_cheap_gps_smartwatchs_ble_protocol_from/): how the protocol was mapped
- [r/Gadgetbridge](https://www.reddit.com/r/Gadgetbridge/comments/1xzmzcb/gloryfitpro_ats3085_jx_protocol_notes_that_may/): GloryFitPro protocol notes for the open-source Android app
- [r/smartwatch](https://www.reddit.com/r/smartwatch/comments/1xzmynq/opensource_web_app_to_control_a_cheap_ht36_gps/): for owners of the watch

Bugs, watch reports and code go in [GitHub issues](../../issues) and pull requests.

## Credits: code and tools from other projects

This project stands on other people's work. Everything we pulled in, ported, analysed or ran is listed here.
Licence notices for anything included in the repo are in [NOTICE](NOTICE).

**Code ported into this repo**

| Project | Licence | What we used |
|---|---|---|
| [tcsenpai/ht36](https://github.com/tcsenpai/ht36) | MIT | Frame envelope, subpackaging with XOR trailer, notification, weather and GPS builders (`src/proto.ts`), ported to the web page; its GATT map was our starting point |
| [REAP reverse-engineering prompts](Skills/REAP-readme.md) (Joas Antonio dos Santos) | MIT | Workflows in `Skills/` that guided the APK analysis (feature tracing, Android, version comparison) |

**Loaded at runtime (not bundled)**

| Project | Licence | Used for |
|---|---|---|
| [Leaflet](https://leafletjs.com/) 1.9.4 (via unpkg) | BSD-2-Clause | The map on the GPS Tracks page |
| [OpenStreetMap](https://www.openstreetmap.org/copyright) tiles | ODbL data | Map tiles (© OpenStreetMap contributors) |

**Libraries our scripts depend on**

| Project | Licence | Used for |
|---|---|---|
| [bleak](https://github.com/hbldh/bleak) | MIT | The Python BLE scan, GATT discovery and probe scripts in `Control-Page/scripts/` |

**Apps we analysed statically (protocol source only; nothing from them is included)**

| App | Where from | What it gave us |
|---|---|---|
| [LydianLover/WatchLink](https://github.com/LydianLover/WatchLink) v1.15 | GitHub releases | Labelled command frames for settings, alarms, health monitors, reminders, music, contacts, find ([docs/05](docs/05-app-controls.md)) |
| GloryFitPro (`com.yc.gloryfitpro`) 1.8.6.2, 1.9.0.2, 1.9.0.3, 1.9.2 | the vendor's Google Play builds (APKPure mirror, signature checked) | The full SDK command set and a per-version diff ([docs/06](docs/06-gloryfitpro-protocol-and-versions.md)) |

**Tools we used to get here**

| Tool | Licence | Used for |
|---|---|---|
| [jadx](https://github.com/skylot/jadx) 1.5.6 | Apache-2.0 | Decompiling the Android apps to readable Java |
| REA (reverse-engineer-anything) MCP tools | — | APK signature checks, package inspection, version comparison |
| [apkeep](https://github.com/EFForg/apkeep) 1.1.0 (EFF) | MIT | Downloading specific GloryFitPro versions for analysis |
| [Android platform tools](https://developer.android.com/tools/releases/platform-tools) (adb) | Apache-2.0 | Pulling apps and Bluetooth logs from a phone (planned) |
| [Playwright](https://playwright.dev/) + headless Chrome | Apache-2.0 | Render and behaviour checks of the web app (fake mic, GPX import) |
| Chrome / Edge [Web Bluetooth](https://webbluetoothcg.github.io/web-bluetooth/) | — | The browser-to-watch connection itself |

**References we read (not used as code)**

| Project | Licence | Why |
|---|---|---|
| [Gadgetbridge](https://gadgetbridge.org/gadgets/wearables/gloryfitpro/) GloryFit support, [PR #6401](https://codeberg.org/Freeyourgadget/Gadgetbridge/pulls/6401) | AGPL-3.0 | How an open Android app talks to the same watch family |
| [jayyee/Gadgetbridge-tools](https://codeberg.org/jayyee/Gadgetbridge-tools) | — | Watch-face and protocol tooling for related watches |
| [ArnCepTech/ATSDialFactory](https://github.com/ArnCepTech/ATSDialFactory) | GPL-3.0 | Watch-face (`.iwf`) format for ATS3085L watches; reference for the face editor (P4) |
| [sonigeez/actions-adfu](https://github.com/sonigeez/actions-adfu) | MIT | USB ADFU firmware flashing for Actions ATS30xx; reference only, never run |

## Licence

MIT, see [LICENSE](LICENSE). Third-party notices are in [NOTICE](NOTICE).
