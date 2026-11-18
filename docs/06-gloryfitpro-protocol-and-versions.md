---
date: 2026-11-18
stage: 04_develop
source: >
  Static decompile (jadx 1.5.6, --no-res) of GloryFitPro base APKs 1.8.6.2 (vc95), 1.9.0.2 (vc101),
  1.9.0.3 (vc102), 1.9.2 (vc103) from APKPure, vendor cert f90cbd89…. Output in decompiled/GloryFitPro-<ver>/.
  Manifests via apkanalyzer; string names via apkanalyzer resources. Nothing was installed, run, or sent to the watch.
---
# 06 GloryFitPro: watch protocol map (1.9.2) and version changes

## Summary

- **The SDK that talks to our watch is `com.yc.nadalsdk` ("JX" platform = Actions ATS3085).** Every public call is
  in `com/yc/nadalsdk/jx/q3.java` (implements `ble/open/UteBleConnection`, 393 methods). Each method builds a frame
  and hands it to a per-feature handler singleton (`jx/t4` faces, `jx/d5` workouts, `jx/r0` fitness and sleep,
  `jx/z0` health, `jx/k1` notifications, and so on). Replies are routed by group byte in `jx/f4.a(byte[])` (jadx
  could not decompile it in normal mode; a `-m simple` decompile of that one class gave the table in the section on transport and replies).
- **Frame grammar (evident):** `01 <group> AA <op> [len payload]` query, `01 <group> AB <op> <len> <payload>` set,
  `01 <group> AC <op> …` watch-initiated event. Sets always carry a 1-byte length. All multi-byte numbers are
  big-endian, all times are Unix seconds (u32 BE), all user text is UTF-16BE.
- **Large payloads use one shared chunker** (`jx/x2.d()`): `<grpHi grpLo> <cmdHi cmdLo> <seq u8> <data…>` per
  packet (MTU-5 bytes of data), then `<grp> <cmd> FD <xor>` where xor = XOR of every byte of every packet
  sent. Replies use the same shape, with `FD` (1-byte seq) or `FD FD` (2-byte seq) to mark the end.
- **Capabilities come from a GATT read, not a frame.** On connect the SDK **reads** characteristic 35F1 and 34F1
  (20 bytes each) and unpacks 13 capability bitmaps from them (`jx/b4.java` ~l.600-680). This explains why our
  `01 C7 AA AA` / `01 A7 AA 01` self-describe queries told us nothing.
- **Big finds, new to us:** face **delete** (`applyWatchFace` with operate=2), the full face **install** transfer
  (`01 E3 AB 03` / `01 E4 AB 01 <seq16>` / `01 E3 AB 04`), the photo-face upload format (64-byte header + LZ4
  RGB565), full **history sync** layouts (minute frames with HR/SpO2/steps/BP/HRV, sleep stages, stress), **workout
  list/summary/detail/pace and the GPS track download** (`01 E8 AA 09`), a **voice-from-watch** path over BLE (Opus
  in `01 EF AC 02`), and the music/file upload (`01 F9`).
- **No crown / dial scroll-speed setting exists** anywhere in nadalsdk or the app (searched crown/knob/rotate/
  encoder/scroll and the Chinese terms). Screen settings that do exist: brightness, auto-brightness, touch,
  cover-to-off, screen-on time, raise-to-wake.
- **Versions:** the protocol bytes for every method that exists in both 1.8.6.2 and 1.9.2 are identical. 1.9.0.2
  added about 20 SDK calls (LED/motor, PPG 50 Hz, feature data, prayer, wearing state). nadalsdk is byte-identical
  across 1.9.0.2, 1.9.0.3 and 1.9.2; those two releases change only app code.

## Transport and replies (evident)

| Item | Where | Detail |
|---|---|---|
| Command write | `jx/v1.a(byte[])` | service `56FF` / char `34F1` (channel 0). Channel 1 = `3802/4A02` (other device type), channel 2 = `56FF/34F3` (glasses/companion, frames start `11`). |
| Notifications | `jx/v1` l.540-600 | enables `35F2`, `34F2`, `AE02`, `4A02`, `FFE2`, `34F4`, `2BB1`. 35F2 and 34F2 both feed the same `f4` dispatcher. |
| Connect reads | `jx/v1.b(BluetoothGatt)` | reads `35F1` then `34F1`. |
| 35F1 read (20 B) | `jx/b4` ~l.612 | bytes 0-1 = function list 7; bytes 2-4,5-7,…,17-19 = lists 6,5,4,3,2,1 (3-byte BE each). |
| 34F1 read (20 B) | `jx/b4` ~l.643 | bytes 0-1 = **phone MTU** used for chunking; bytes 2-19 = lists 13…8 (3-byte BE each). |
| Bit names | `ble/open/DeviceModeJX.java` | ~80 named bits (e.g. `IS_NO_SUPPORT_BT_CALL`, `IS_SUPPORT_CHAT_GPT`, `IS_SUPPORT_LOCAL_MUSIC`, `IS_PLATFORM_JXATS3085L/S`). Which list each bit lives in is decided at each `isHasFunction_N()` call site. |
| Busy guard | `jx/v1.a(int,byte[])` l.717 | while a face install runs, only `01E3AB03`, `01E3AB04`, `01E4AB01`, `01E4AB02`, `01E4AA02` may be sent. |
| Chunked send | `jx/x2.d()` | `hdr(2) cmd(2) seq(1) data`; end `hdr cmd FD xor` (or `FD crc32` when the CRC flag is set). |
| Device events | `AC` frames | the watch pushes these whenever it likes; the SDK never treats them as replies. |

Dispatcher (`f4.a`) group → handler: A2,A3 `d3` (time/e-card) · A4 `z` (info/battery) · A5 `d0` (settings) · A6 `h3` ·
A7 `w0` · B0-B3 `k1` (notifications) · C0 `p` (calls/contacts) · C1-C3 `r0.g` · C4 `r0.d` · C5 `r0.e` · C6 `r0.f` ·
C7 `k` (alarms) · C8 `i2` (OTA) · C9 `d5` · CA `l1` · CB `m` · CC `n1` · CD `k2` · CE `l2` · CF `x` · D1 `f1` · D2 `e0` ·
D3 `l0` · E0 `v4` (weather) · E1 `z0` (health) · E2 `p1` (music ctl) · E3 `t4.a` / E4 `t4.b` (faces) · E5 `d5.d` · E6 `i1` ·
E7 `a1.b` · E8 `d5.e` (workouts) · E9 `u0` (GPS/ephemeris) · EA `f0` (DND) · EB `a1.a` (classic BT) · EC `d5.f` ·
ED `e5` (world clock) · EE `m1` · EF `r` (AI voice) · F0 `g` · F1/F3 `d2` · F2 `g0` · F4 `a2` (maps) · F5 `e3` · F6 `d` ·
F8 `i0` · F9/FA `n0` (files/music) · FB `c3` (temperature). Groups `01 01..01 40` with `00` as byte 3 belong to a
separate voice-recorder device (`jx/b`), not this watch.

## Feature → class → frame (1.9.2)

Legend: **WL** = already in WatchLink (`decompiled/WatchLink/.../wq1.java`, `lr2.java`); **CP** = already in
Control-Page; **NEW** = not in either. "len" is the 1-byte length that follows the op in every `AB` set.

### Device, settings, units, language, screen

| Feature | q3 method → handler | Frame | Reply / notes | Status |
|---|---|---|---|---|
| Device info | `getDeviceInfo` → `z` | `01 A4 AA AA` | chunked `01 A4 AA AA …` until `FD` | CP |
| Battery | `getBatteryInfo` → `z` | `01 A4 AA 16` | | CP |
| Set BT name / SN / MAC | `setDeviceBluetoothName/SN/Mac` | name `01 A4 AB 03`, SN `01 A4 AB 01`, MAC `01 A4 AB 02` (`<len> <ASCII>`) | factory-style; don't use | NEW (don't use) |
| Default config | `getDefaultConfiguration` → `d0` | `01 A5 AA 01` | chunked | CP |
| Generic A5 switch | `d0.a(type,val)` | `01 A5 AB <type> 01 <val>` | type 1 = raise-to-wake (`setScreenAutoLight`), 4 = find watch, 5 = disconnect alert | WL (04) |
| Language | `setLanguage` | `01 A5 AB 06 01 <lang>` (2-arg form adds `AB 07 01 <x>`) | query current `01 A5 AA 08`, list `01 A5 AA 03` | NEW |
| Length units | `setLengthUnits` | `01 A5 AB 07 01 <0 metric/1 imperial>` | query `01 A5 AA 04` | CP (query) |
| Weight units | `setWeightUnit` | `01 A5 AB 09 01 <u>` | | NEW |
| Temperature unit | `setTemperatureUnit` → `v4` | `01 E0 AB 02 01 <u>` | query `01 E0 AA 03` | NEW |
| Blood-sugar / BP unit | | `01 A5 AB 13 01 <u>` / `01 E1 AB 16 01 <u>` | | NEW |
| Screen-on time | `setScreenOnDuration` | `01 A5 AB 08 01 <sec>` | query `01 A5 AA 09`, allowed list `01 A5 AA 0B` | NEW |
| Screen info | `setScreenInfoConfig` | `01 A5 AB 0D <len>` TLV `01 01 bright` `02 01 autoBright` `04 01 touch` `05 01 coverOff` | query `01 A5 AA 0F` | NEW |
| Sound / vibration | `setSoundVibrationConfig` | `01 A5 AB 0E <len>` TLV `01 01 media` `02 01 mute` `03 <n> …` | query `01 A5 AA 10` | NEW |
| Time/date format | `setTimeDisplay` → `d3` | `01 A3 04 01 <dateFmt> 08 01 <12/24>` (or just `01 A3 08 01 <fmt>`) | | NEW |
| Set time | `setTimeClock` → `d3` | `01 A3 01 04 <epoch u32> 10 02 <tz> <min>` with tz = hours+128 for east, abs(hours) for west; min = offsetMin×100/60 | query `01 A3 AA` | CP |
| Voice assistant on/off | `setVoiceAssistantEnable` | `01 A5 AB 11 01 <0/1>` | | NEW |
| Ring phone (app ring status) | `setAppRingStatusToDevice` | `01 A5 AB 12 01 <0/1>` | | NEW |
| Camera remote | `sendCameraPermission` | `01 A5 AB 0B 01 <0/1>`; watch shutter press = `01 A5 AC 01 <instr>` | | NEW |
| Find phone enable | `sendFindPhoneSwitchStatus` | `01 A5 AB 0A 01 <0/1>` | watch event `01 A5 AC 02 <1 start/0 stop>` | WL |
| Find watch | `setFindWearCmd` | `01 A5 AB 04 01 <0/1>` | state `01 A5 AA 07` | WL/CP |
| Wearing state | `queryWearingState` | `01 E1 AA 1A` | 1.9.0.2+ | NEW |
| Factory reset / unbind | `resetFactory`, `removeBondDevice` | `01 E7 AB 03 01 <i>` etc. | **do not send** | — |

### Reminders, DND, alarms

| Feature | Method | Frame | Status |
|---|---|---|---|
| Sedentary reminder | `setActivityRemind` → `r0` | `01 C4 AB 01 08 <en> <interval u16 min> <fromH> <fromM> <toH> <toM> <x>`; query `01 C4 AA 01` | NEW |
| Drink water | `setDrinkWaterRemind` → `g0` | `01 F2 AB 01 07 <en> <fromH> <fromM> <toH> <toM> <interval u16>`; query `01 F2 AA 01` | NEW |
| Lunch-break no-remind | `setLunchBreakNoRemind` | `01 F2 AB 02 05 <en> <h> <m> <h> <m>` | NEW |
| Do not disturb | `setDoNotDisturb` → `f0` | `01 EA AB 01 08 <en> <allDay?> <fromH> <fromM> <toH> <toM> <flag> <flag>`; query `01 EA AA 01`; watch change `01 EA AC 01` | NEW |
| HR high/low alert | `setHighestRemind/LowestRemind` | `01 E1 AB 03/04 02 <en> <bpm>` | NEW |
| SpO2 low alert | `setBloodOxygenLowestRemind` | `01 C4 AB 04 02 <en> <limit>` | NEW |
| Alarms | `setAlarmList` → `k` | chunked hdr `01 C7` cmd `AB AB`; per slot TLV `AB01 02 i i` · `AB02 02 i cycle` · `AB03 02 i en` · `AB04 03 i hh mm` · `AB05 <n> i name(UTF-16)` · `AB06 02 i sound`; read `01 C7 AA AA`; slot count `01 C7 AA 0A`; watch edit `01 C7 AC …` | WL |
| Continuous HR / SpO2 | `setAutoHeartRate`, `setContinuousBloodOxygen` | `01 E1 AB 01 01 <en>`, `01 C4 AB 03 01 <en>`; intervals `01 E1 AB 0C 01 <min>` | CP (queries) |
| Stress / mood / BP auto | | `01 E1 AB 0E/10 01 <en>`, intervals `01 E1 AB 0F/11 02 <u16>` | NEW |

### Notifications, calls, contacts, weather, music control

| Feature | Method | Frame | Status |
|---|---|---|---|
| Push notification | `sendMessage` → `k1` | chunked hdr `01 B0` cmd `AB AB`, TLV `AB01 app` `AB02 contact` `AB03 body` `AB04 01 id` `AB05 phone` `AB06 package` `AB07 title` `AB08 01 type` `AB09 01 vibrate` `AB0A 04 msgId` (text UTF-16BE; length field is 2 bytes when the "432-byte push" bit is set, body cap 488 or 864 hex chars) | WL |
| Delete notification | `deleteMessage` | `01 B2 AB 05 01 <id>` | NEW |
| Call alert switch | `setCallRemindEnable` | `01 B2 AB 01 01 <0/1>` | NEW |
| Incoming / missed call | `notifyIncomingCall/MissedCall` → `p` | chunked hdr `01 C0` cmd `AB AB`, TLV `AB01 name` `AB02 number` (incoming) or `AB03`/`AB04` (missed); UTF-16BE, name ≤40, number ≤20 chars | NEW |
| Hang up / answered | `notifyHangup/AnswerCall` | `01 C0 AB 05 01 00` / `01 C0 AB 05 01 01` | NEW |
| Watch call actions | event | `01 C0 AC 01 <len> number` (reject with SMS), `01 C0 AC 02 <len> text`, `01 C0 AC 03 <op>` hang-up | NEW |
| Quick-reply SMS list | `syncSmsReplyContent` | hdr `01 C0` cmd `AB 0A` chunked; enable `01 C0 AB 09 01 <en>` | NEW |
| Contacts | `syncContactsInfoToDevice` | `01 C0 AB 06 01 00` start → `01 C0 AB 07 <idx16> <n> …` → `01 C0 AB 07 FD <xor>` → `01 C0 AB 09 01 01`; read `01 C0 AA 07`; SOS list `01 C0 AA 08` | WL |
| Weather today | `setTodayWeather` → `v4` | TLV `AB04 02 aqi` `AB05 city` `AB06 02 temp` `AB07 02 hi` `AB08 02 lo` `AB09 01 phenom` `AB0A 01 pm25` `AB0B 04 publish` `AB0C 02 level dir` `AB0F 02 hum uv` | WL |
| Weather forecast | `setFutureWeather` | `AB0B 04 ts` + `AB0D` hourly + `AB0E` daily blocks | WL |
| Watch asks for weather | event | `01 E0 AC 02` (→ `WEATHER_DATA_REQUIRED`), pressure `01 E0 AC 01` | NEW |
| Music now-playing | `setMusicAppPlayInfo` → `p1` | `01 E2 AB …` chunked; status `01 E2 AB 06 01 <play/pause>` | WL |
| Watch music buttons | event | `01 E2 AC 01 01 <ctl>` or `01 E2 AC 01 02 <ctl> <vol>`; app ack `01 E2 AB 07 01 01` | NEW |

### Health history sync (all NEW as byte layouts)

| Data | Method → handler | Request | Reply layout |
|---|---|---|---|
| Minute-frame index | `getMotionFrameIndex` → `r0` | `01 C5 AA <01, or 04 if health-expansion bit> 08 <start u32> <end u32>` | lastIndex |
| Minute frames (steps, kcal, distance, HR rest/max/min/avg/dynamic, **SpO2**, BP, mood, PAI, **HRV**, blood sugar) | `getMotionFrame(start,end,idx)` / `syncFitnessHistoryData` → `r0.b()` | `01 C6 AA 01 0A <start> <end> <idx u16>` | chunked `01 C6 AA 01 <seq> …`, end `01 C6 AA 01 FD <xor>`. Payload: `idx u16, start u32`, then records `offsetMin u16, fieldBitmap (1-4 bytes, high bit = more), fields in bit order`. Bit → field (bytes): 1 steps(1) 2 kcal(1) 3 distance(2) 4 restHR(1) 5 HRmax(1) 6 HRmin(1) 7 dynHR(1) 9 **SpO2**(1) 10 restHRv2(1) 11 height(2) 12 HRavg(1) 13 restHRv3(1) 17 BP sys,dia(2) 18 mood(2) 19-23,25 PAI(2) 26 **HRV**(2) 27 sugar/10(2); other bits 2 bytes. Bits 8/16/24 are continuation bits, not fields. |
| Status frames | `getStatusFrame` | `01 C6 AA 02 0A <start> <end> <idx16>` (count `01 C5 AA 02 08 …`) | `idx u16`, records ×7: `status u8, start u32, dur u16` |
| Activity-state frames | `getStateFrame` | `01 C6 AA 03 0A …` (index `01 C5 AA 03 09 … <type>`) | records ×7: `motionType u8, start u32, minutes u16` |
| **Sleep** | `syncSleepHistoryData` → `r0` | `01 C6 AA 04 08 <start> <end>` | chunks `01 C6 AA 04 <seq u16> …`, end `01 C6 AA 04 FD FD <x>`. Payload: 2-byte head, then records ×7: `start u32, minutes u16, stage u8` (1 deep, 2 light, 3 awake, 4 REM, 5 nap, 6 snore, 7 start, 8 end) |
| Live stress result | event | `01 C6 AC 02 <len≥5> <ts u32> <stress>` | |
| **Stress history** | `syncStressHistoryData` → `z0` | `01 E1 AA 02 08 <start> <end>` | blocks: `baseStart u32, interval u16 (min)`, then 1440/interval bytes of stress (0 = none) |
| Temperature history | `syncTemperatureHistoryData` → `c3` | `01 FB AA 02` | |
| Warning events | `getWarningEvent` → `z0` | `01 E1 AA 01 09 <start> <end> <type>` | |
| Today summary | `getMotionSummaryData` | `01 C3 AA AA` | CP |

### Workouts and GPS track (all NEW)

| Step | Method → `d5` | Request | Reply |
|---|---|---|---|
| List workouts | `getRecordList` | `01 E8 AA 01 08 <start> <end>` | chunks `01 E8 AA 01 <seq16> …` end `FD FD`. `count u16`, then 8-byte items `id u16, index u16, paceIndex, number, sectionIndex, spo2` |
| Summary | `getRecordSummary(id)` | `01 E8 AA 02 02 <id u16>` | TLV (1-byte tag, 1-byte len): 1 id, 2 status, 3 start, 4 end, 5 kcal, 6 distance, 7 steps, 8 total time, 9 speed, 10 rise, 11/12 HR min/max, 13 load, 14 effect, 15 EPOC, 16 VO2max, 17 recovery, 18 sport time, 19 **type**, 20-26 swim, 27/28 altitude, 41 max speed, 48/49 SpO2 hi/lo, 63/64 cadence, 75 avg pace, 76 step freq, 77 stride, 92-99 min/max, 100 HR avg … up to 106 |
| Per-sample detail | `getRecordDetail(id,index,newAlg)` | `01 E8 AA 03 05 <id16> <index16> <newAlg>` | `id16, index16, interval u8, start u32`, records: bitmap (1-2 B) then fields 1 speed 2 kcal 3 cadence 4 **HR** 5 elevation(s16) 6 stroke 7 swim eff 9 jump 10 fat 11 sugar 13 pace(2) … |
| Pace per km | `getWorkoutPace` | `01 E8 AA 04 03 <id16> <paceIdx>` | `id16, paceIdx`, 8-byte items |
| **GPS track** | `downloadRecordGpsFile(id)` | `01 E8 AA 09 00 02 <id u16>` | chunks `01 E8 AA 09 <seq16> …` end `FD FD`. File: `start u32, end u32, size u32`, then TLV (tag 1 B, len 1 B, BE): 1 speed 2 distance 3 altitude 4 total distance 5 start 6 end **7 lat×1e7** **8 lon×1e7** 9/10 GCJ-02 lat/lon 11 bearing 12 accuracy 13 timestamp (13 closes a point) |
| Ability list | `getWorkoutAbility` | `01 E8 AA 07` | 3-byte LE sport IDs |
| Live workout / summary push | events | `01 E8 AC 01`, `01 E8 AC 02`, `01 E5 AC AC` | `WORKOUT_*_REPORT` notifies |
| Pool / runway length | | `01 E8 AB 05 01 <m>`, `01 E8 AB 06 02 <u16>` | |
| Phone GPS to watch | `sendGpsCoordinates` → `u0` | `01 E9 AB 02 0C <ts> <lat> <lon>` | CP |

### Watch faces

| Action | Method → `t4` | Frame | Status |
|---|---|---|---|
| Face params | `getWatchFaceParams` | `01 E3 AA AA` → chunked TLV (2-byte tag, 1-byte len): `AA01` max version, `AA02` width, `AA03` height, `AA04` file types, `AA05` sort ok, `AA06` min version, `AA07` screen type(+corner), `AA08` **max file size**, `AA09` **face count**, `AA0D` AOD count | CP (sent; layout NEW) |
| Installed list | `getWatchFaceInfo` | `01 E3 AA 0B` → chunked; skip 1 byte, then 10-byte records `id u32, ver ASCII(5), type u8` (18 bytes with an 8-char path when bit list7 & 0x4000) | CP |
| Type bits | `WatchFaceTypeMode` | 1 current · 2 preset · **4 deletable** · 8 customisable · 16 Google preset · 32 photo · 64 AOD | NEW |
| Switch face | `applyWatchFace` operate=1 | `01 E3 AB 05 0A <id u32> "1.0.0" 01` | WL/CP |
| **Delete face** | `applyWatchFace` operate=2 (`MyWatchFragment.deleteDeviceWatchFace`, `WatchFaceUpperLimitDialog.deleteWatchFace`) | `01 E3 AB 05 0A <id u32> <ver ASCII 5> 02` (only for faces with type bit 4) | **NEW** |
| Apply reply | | `01 E3 AB 05 … <id> <ver> <op>`; op = 1 means "watch wants the file" | NEW |
| Reorder | `sortWatchFace` | chunked hdr `01 E3` cmd `AB 01`: `<n bytes> <id u32>…`, end `01 E3 AB 01 FD <xor>` | WL |
| **Install face** | `uploadWatchFace` | 1) `01 E3 AB 03 01 01`, 2) watch `01 E3 AC 02 xx 02` = ready, 3) data `01 E4 AB 01 <seq u16> <MTU-6 bytes>`; after each 4 KiB wait for `01 E3 AC 02 xx 07` (continue), 4) `01 E3 AB 04 01 01` = done, 5) `01 E3 AC 02 xx 01` = complete. Status byte (bArr[5]): 1 done, 2 ready, 3 cancelled, 4 CRC fail, 5 too big, **6 resend from seq (bytes 6-7)**, 7 continue, **8 face limit reached** | **NEW** |
| Face file | `WatchFaceUtil.readBinToByte` | the vendor `.bin` is sent **as-is**: no app-side header or compression | NEW |
| Photo face config | `setImageWatchFace` | chunked hdr `01 E3` cmd `AB 06`: TLV `01 01 count` `04 01 position` `05 01 style` `07 01 transferNum` `06 <n> (idx len name)…` `08 03 timeRGB` `09 03 dateRGB`; read `01 E3 AA 0C` (TLV 1 max 2 smart colour 3 imgType 4 pos 5 style 6 list 7 transferNum 8/9 colours) | WL (read only) |
| **Photo upload** | `uploadImageWatchFace(file,idx)` | `01 E3 AB 03 01 02` → data `01 E4 AB 02 <seq16> …` → `01 E3 AB 04 01 02`. File = 64-byte header + LZ4(RGB565). Header: `[0-3] FF`, `[4-7] CRC32 LE of compressed`, `[8] FF`, `[9] idx`, `[10-29] name ASCII`, `[30] name len`, `[31-47] FF`, `[48-49] W LE`, `[50-51] H LE`, `[52] 00`, `[53] 02`, `[54-55] 00`, `[56-59] compressed len LE`, `[60-63] 02 01 00 00` | **NEW** |
| Photo download | `downloadImageWatchFace` | `01 E4 AA 02 01 <idx>` | NEW |
| Watch face event | | `01 E3 AC 01` TLV id/version/reportType | NEW |

### Firmware / OTA: flow only (gated, never use; AGENTS rule 1)

`prepareUpgrade`: `01 C8 AB 03 <len> <version ASCII>` → `notifyNewVersion`: chunked hdr `01 C8` cmd `AB 04`, TLV
`01 ver`, `02 04 size`, `03 04 checkTime`, `04 01 detected` → watch `01 C8 AC 01` (confirm download) →
`setDownloadConfirmResponse` `01 C8 AB 05 02 …` → the image goes through **Actions' own OTA library**
(`com/actions/ibluz/...`, `com/yc/gloryfitpro/utils/ActsOtaUtil.java`) on the `e49a…` GATT service (`jx/b4`
watches `e49a28e1`/`e49a25e0`). Cancel `01 C8 AB 01 01 00`, status `01 C8 AA 01`. JieLi OTA (`jlota/`) and ISP
(`11 A7 AB 01`) are for other device families. **Not to be used.**

## Audio: music upload, voice, calling

| Topic | What the code does | Classes | Feasible from browser / Mac? |
|---|---|---|---|
| **Music / MP3 upload** | File service, group F9. Start `01 F9 AB 01 05 <fileCount> <totalBytes u32>`; per file `01 F9 AB 02 <len> <size u32> <crc32 u32> <UTF-8 path>` (music lives under `D:/music`, playlists `A:/playlists`); data **over BLE** `01 F9 AB 03 <n+4> <seq u32> <n bytes>` with n = MTU-9, written straight to 34F1, pausing every 4 KiB for `01 F9 AC 01 … 05` (continue; `04` = resend from seq); end `01 F9 AB 03 04 FF FF FF FD`. List `01 F9 AA 01/02/03 <len> <path>`, delete `01 F9 AB 04 <len> <path>`, stop `01 F9 AB 07 01 00`, disk usage of "D:". The file goes as-is (the app passes the picked audio file unconverted; MP3 inferred). If a classic **SPP** link is up (RFCOMM UUID `0000ff56-…`, `jx/l4`) the app uses that instead (18-byte header chunks); otherwise it falls back to BLE. | `jx/n0`, `q3.syncMusicFileContent*`, `gloryfitpro/model/main/device/MusicBaseModelImpl` (l.279-292) | **BLE path: yes in principle from Web Bluetooth** (needs `IS_SUPPORT_LOCAL_MUSIC`, and it is slow: about 4-20 KB/s at MTU 23-247, so a 4 MB MP3 takes minutes). SPP: no from a browser; a Mac could do RFCOMM with native code only. |
| **Voice from the watch mic (AI assistant)** | Watch sends `01 EF AC 01 <status>` (mic pressed), then the question audio as **Opus over BLE**: `01 EF AC 02 <seq u16> …` until `FD FD`; payload = `len u32` + Opus. Real-time variant `01 EF AC 06 <seq16> …` (streams). The app runs speech-to-text and the LLM, then sends back the question text: chunked hdr `01 EF` cmd `AB 02`, and the answer: hdr `01 EF` cmd `AB 03`, each `<len u16> <UTF-16BE>` (answer cap 128 chars, or 2000 when the bit list4 & 0x8000 is set). Status `01 EF AB 01 01 <s>`, enable `01 EF AB 0B 01 <en>`, language `01 EF AB 06 01 <l>`, query enable `01 EF AA 02`. Voice replies to messages: `01 B2 AC …` → `DEVICE_REPLY_VOICE_DATA_NOTIFY`, answer `replyDeviceVoiceContent` (hdr `01 B2` cmd `AB 07`). | `jx/r` (l.330-430), `q3.setChatGptAnswerContent/VoiceContent`, `gloryfitpro/utils/gptapi/*` | **Yes, this is the Assistant-chat route.** The audio arrives as BLE notifications on 34F2, which Web Bluetooth can read; decode the Opus in the browser (WebCodecs or opus.js) or on the server. Only works if the watch has the ChatGPT/AI bit set (bit `IS_SUPPORT_CHAT_GPT`); read 35F1/34F1 to check. |
| Voice recorder / memo files | `01 14 00`…`01 1E 00`, `01 26 00` (record list/sync/delete) | `jx/b`, `bean/recorder/*` | These go to a separate AI-recorder device type, not this watch (inferred from the frame shape and the dispatcher). |
| **BT calling** | The watch has a second, **classic BT ("BT3")** radio with its own MAC and name. Query `01 EB AA 01` → chunked reply: `[1] switch, [2] paired, [3] connected, [4-9] BT3 MAC, [10-29] BT3 name`; `openDeviceBt3` `01 EB AB 02 01 <0/1>`; `requestDevicePairBt3` `01 EB AB 01 06 02 00 00 00 00 00` (the watch starts classic pairing; the phone bonds over HFP). Call audio then goes over **classic HFP**, never BLE. BLE only carries the caller ID and hang-up/answer frames above, and the contacts. Capability bits: `IS_NO_SUPPORT_BT_CALL`, `IS_NO_SUPPORT_BT3`. | `jx/a1` (l.38-91), `jx/p`, `bean/DeviceBt3StateInfo` | Browser: can only send the BLE control frames (state query, enable BT3, caller ID). The audio needs a phone acting as the HFP gateway. **Mac: no**, because macOS cannot be an HFP gateway, so the Mac cannot place or carry calls through the watch. Voice for Assistant should use the Opus-over-BLE route, not calling. |

## New-to-us frames, ready for the web app (read-only first)

Safe **queries** (AA), to add to the Lab first:
`01 E3 AA AA` face params (now with a decoder) · `01 E3 AA 0B` face list (decoder + type bits) ·
`01 EB AA 01` classic-BT state · `01 EF AA 02` AI enable · `01 F9 AA 01 <len> "D:/music"` music list ·
`01 C5 AA 01 08 <start><end>` → `01 C6 AA 01 0A <start><end><idx16>` minute history ·
`01 C6 AA 04 08 <start><end>` sleep · `01 E1 AA 02 08 <start><end>` stress ·
`01 E8 AA 01 08 <start><end>` workout list → `01 E8 AA 02 02 <id16>` summary → `01 E8 AA 03 05 <id16><idx16>00` detail →
`01 E8 AA 09 00 02 <id16>` **GPS track** · `01 EA AA 01` DND · `01 C4 AA 01` sedentary · `01 F2 AA 01` water ·
`01 A5 AA 08` language · `01 A5 AA 09` screen-on · `01 A5 AA 0F` screen info · `01 A5 AA 10` sound · `01 E1 AA 1A` wearing.
Plus the two **GATT reads**: 35F1 and 34F1 (capabilities + MTU).

**Sets** (AB) that are low-risk once the owner approves them (rule 2):
language `01 A5 AB 06 01 <l>`, units `01 A5 AB 07/09`, `01 E0 AB 02`, screen-on `01 A5 AB 08 01 <s>`, raise-to-wake
`01 A5 AB 01 01 <0/1>`, DND `01 EA AB 01 08 …`, sedentary `01 C4 AB 01 08 …`, water `01 F2 AB 01 07 …`, caller ID
(hdr `01 C0` cmd `AB AB`), hang-up `01 C0 AB 05 01 00`, AI answer text (hdr `01 EF` cmd `AB 03`).

**Writes with consequences** (need an explicit yes): **face delete** `01 E3 AB 05 0A <id> <ver> 02`, face install
(`E3 AB 03` / `E4 AB 01` / `E3 AB 04`), photo face, music upload (`F9`).

## Per-version change log

Method: every APK entry compared by CRC; vendor classes (`com/yc/**`) compared by a normalised hash (resource IDs
removed); SDK API surface and the frame bytes of every method extracted from each version's `q3` and diffed; manifests
diffed; string-resource names diffed. "Evident" means seen in code or resources. "Inferred" means read from names only.

### 1.8.6.2 (vc95) → 1.9.0.2 (vc101): feature release

- **Protocol:** every method in both versions builds byte-identical frames (evident). 21 SDK calls were added
  (evident, frames in `q3`): `queryWearingState 01 E1 AA 1A`; `setMotorVibration 01 CC AB 01`,
  `setLedControl 01 CC AB 02`, `queryLedProperty 01 CC AA 01`; `setPpg50Hz 01 CE AB 01`, `syncPpg50HzData 01 CE AA 01`,
  `queryCollectionInfo 01 CE AA 02` (raw PPG/science data collection); `setFeatureDataCollectionEnable 01 D3 AB 01`,
  `queryFeatureDataFileInfo/ProtocolVersion 01 D3 AA 02/01`; `setPrayerData`/`queryPrayerData 01 CD AA 01`;
  `queryTripleInfo 01 EF AA 06`, `aiStartAuthentication 01 EF AB 0D`, `queryAIProviderAuthorization 01 EF AA 05`,
  `setDeviceToken`; `queryAppMessageNotify 01 B2 AA 02`; `sendCustomData` (group CF); recorder-device calls
  `getDeviceCurrentState 01 03 00`, `setUsbFlashDriveFunction 01 07 00`, `setNoteCustomData 01 F6 00`.
  New SDK handlers `jx/c5`,`d5`,`e5`,`f5` (the obfuscated names shuffled; workouts moved to `d5`).
- **New features:** Islamic prayer times, Qibla compass and Quran reader/player (`ui/activity/main/device/Prayer*`,
  `Quran*`, `QuranPlaybackActionReceiver`, `assets/quran.json`, ~100 `prayer_*`/`quran_*` strings), with prayer data
  pushed to the watch (group CD). Data export (`DataExportUtils`, `data_export*` strings). Body-temperature fever
  ranges (`low_fever`, `height_fever`). Calorie and PAI views (`PaiInfo`, `PaiListener` in utesdk). AGPS file
  handling (`AgpsUtil`, `AgpsFileRequest`). On-device voice activity detection for the AI recorder
  (`libimsl_vad.so`, `libonnxruntime.so`, `assets/rsvad/model.onnx`). Inferred: NetEase Cloud Music for the watch
  through a phone-side JS proxy (`assets/ble_analyze.js` signs `openapi.music.163.com` calls); a web map page
  (`assets/index.html` + `umi.js`, "h5map"); Starburst SDK keep-alive service.
- **Removed:** Gaode/AMap native 3D map and navigation libs (`libAMapSDK_MAP/NAVI/AGENT`), Microsoft Speech LU
  extension, `libapssdk`, `libneonui*` (evident from the split lib lists; note 1.8.6.2's split is arm64 and 1.9.x is
  armeabi-v7a, so names only were compared). `assets/model/RF/*` was renamed to `model/GDRF/*` (same CRCs).
- **Manifest:** + `FOREGROUND_SERVICE_LOCATION`; + Prayer/Quran activities, `QuranPlaybackActionReceiver`,
  Starburst `KeepAliveService`. Size of the base APK went from 85.6 to 102.3 MB (12 dex files instead of 11).

### 1.9.0.2 (vc101) → 1.9.0.3 (vc102): hotfix

Only `classes10.dex`, the manifest version and the baseline profile changed (evident). nadalsdk is identical.
Seven app classes changed:
- `services/MainService`: a "watch ended the ring" event (code 17) now stops find-my-phone ringing (bug fix, evident:
  log "在设备端点击响铃结束").
- `jlota/WatchManager`: queue-thread wait loop rewritten (JieLi OTA hang fix; inferred).
- `utils/NaviUtils`, `services/sport/AdmapLocationService`, `SearchLocationPresenter`, `RequestLocationMap`,
  `MainHomeModelRkImpl`: AMap location client destroyed later (posted delay) instead of right away (crash fix; inferred).

### 1.9.0.3 (vc102) → 1.9.2 (vc103): app-only release

- **Protocol:** nadalsdk is unchanged (0 differing classes) and the native libs are identical (evident).
- **Changes (evident in code):** quick replies and voice replies to message notifications now also work on the
  "RK" platform SDK (`rksdk/UteBleConnectionRkImpl`: new commands `SET_APP_QUICK_REPLY_ENABLE` 335,
  `SYNC_APP_QUICK_REPLY_CONTENT` 336, `SET_REPLY_DEVICE_CONTENT_STATUS` 337, `REPLY_DEVICE_VOICE_CONTENT` 338,
  `APP_REMIND_WITH_MESSAGE_ID` 339; `SearchDeviceModelImpl` re-syncs quick replies on connect). AI-recording files
  move from the cache dir to the app files dir with a one-time migration (`AIRecordingUtil.migrateLegacyFilesIfNeeded`).
  The legacy `utesdk` gains `MessageNotifyListener`, `ReplyDeviceVoiceInfo`, `OxygenIntervalInfo` and
  `SwAlgSleepSectionUtil` (sleep-section algorithm), affecting other watch families. The GreenDAO session was
  reordered (new tables, inferred).
- **Strings added:** `ble_ota_fail_tip` "Please check the Bluetooth connection.", `ota_tip_string` "…upgrade may take
  5-8 minutes. Do not disconnect!", `device_is_recording` "The device is recording…", `do_not_disturb_des_1_no_screen`
  (DND for screenless devices).
- **Manifest:** `launchMode` removed from `HomeItemManageActivity`, `MenstrualActivity`, `MenstrualSettingActivity`
  (navigation fix; inferred).

## Open questions

1. **Which capability bits does our HT36 report?** Read 35F1 and 34F1 (plain GATT reads, safe) and decode them with
   `DeviceModeJX`. That answers: BT calling, ChatGPT/AI voice, local music, SPP, and the face record size.
   Mapping each `IS_*` constant to its list number still needs a pass over the `isHasFunction_N(...)` call sites.
2. Do 35F1 reads match the 20-byte layout on AT364D, given that our earlier probe "handshake" was an `A1` write on 35F1?
   nadalsdk never writes `A1`; it only *reads* 35F1. The `A1` handshake comes from the prior-art repo or a legacy SDK.
3. Face `.bin` internals: the app sends the vendor file untouched, so the format must come from ATSDialFactory
   (`.iwf`) or a downloaded GloryFitPro face (`HttpUtil` → `ap.ute-tech.com.cn` / `apsouth.uteasy.com`).
4. The face-list record's first byte (skipped by the parser) is probably a count; confirm on the wire.
5. The time-zone byte encoding (`tz+128` for east) and whether `epoch` is local or UTC needs one capture to confirm.
6. The 4-KiB flow control on face and music uploads (`AC 02 … 07`, `AC 01 … 05`): confirm the exact status-byte
   offset on our watch before any write.
7. No crown or dial scroll-speed command exists in the SDK. If the watch has a speed option, it is set on the watch only.
