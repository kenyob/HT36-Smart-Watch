---
date: 2026-11-16
stage: 01_discover
status: done, awaiting review
---
# 01 Discover: HT36 smart watch

## What it is
- Generic "HT36" GPS watch, sold under several brands (BRUBOSES, KPHRTEK, …). App: **GloryFitPro**
  (Youchuangyi / UTE, Android SDK `com.yc.nadalsdk`). Gadgetbridge has partial GloryFitPro support
  (notifications, weather, music, time, alarms), tested on a DM58.
- **SoC is unresolved.** One review names the Actions ATS3085L, a dual-mode BT chip that would allow BT
  calling. The reference repo infers Telink TLSR82xx (BLE only) from the `e49a…` OTA UUID base. To
  settle it, check the FCC ID on the case or box, or read the chip marking.

## Live probes from the Mac (2026-11-16, read-only)

| Probe | Result |
|---|---|
| USB (`ioreg`) | Not present. The magnetic charger is power only. (`/dev/cu.usbserial-212430` is an unrelated CH340.) |
| BLE scan (bleak, 15 s) | `HT36`, RSSI -45, advert service `5555`, mfr data `0000: 7802b7xxxxxx` (MAC prefix `78:02:B7`, the rest stays in `.env`) |
| Classic BT | No HT36 audio device paired with the Mac |
| GATT discovery | Table below. Identical to the reference repo's map. |

| Service | Char | Props | Role (per prior art) |
|---|---|---|---|
| `180a` | `2a24` `2a29` `2a50` | read | model `lark`, mfr `Manufacturer`, PnP id |
| `ffd0` | `ffd1` / `ffd2` / `ffd3` | write / notify | decoy, no acks |
| `55ff` | `35f1` / `35f2` | read,write / notify | **JieLi-style command channel** (`a1` handshake returns the model/fw string) |
| `56ff` | `34f1` / `34f2` | write / notify | **UTE frame channel** `01 <grp> <AA query, AB set, AC reply> <op> <len> <payload>` |
| `e49a3001` | `3002` / `3003` | write / notify | ⛔ **OTA, never write** |
| `e49a25f8` | `25e0` / `28e1` | write / notify | file/data channel (AGPS and face uploads) |

## Prior art: `github.com/tcsenpai/ht36` (MIT, TS/Bun, macOS)
Verified on the same watch model: push a **notification** (title + body; notifications must be enabled
first, and each one needs a type tag), **weather** (any values), **GPS** location, **battery**, **device
info**, **vibrate**, **fitness/sleep/HR/SpO2 history sync** → JSON, the watchface `.bin` format
(decode/encode), and an AGPS file push. It needs no authentication or bonding.

Blocked or unmapped there: `set-time` (ack but no change), custom face **upload** (no delete-slot
command), music/camera-remote button events (frames exist in the SDK but are unmapped), quick replies.
Firmware: no OTA image on the vendor cloud for this model. A dump needs the case opened plus a debug port.

## Constraints that shape the design
1. No custom code runs on the watch (closed firmware, signed or unknown OTA). Every "app" is a bridge feature.
2. Outputs we can drive today: notification text, weather slots, vibrate, GPS. Faces are possible later.
3. Inputs from the watch are unmapped today. Music-control and camera-shutter button events are the
   likeliest trigger channel and need an HCI capture of the vendor app (Android) to map.
4. Voice from the wrist works only if this unit has Classic BT calling, and then only through a phone or Mac, not the S3.
