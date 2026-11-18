# HT36 Control-Page

A local web page and service for controlling the HT36 watch from Chrome or Edge over Web Bluetooth.
The browser talks to the watch directly; the service serves the page and stores logs, health readings,
GPS tracks and voice notes in SQLite. Python 3.9+ standard library only, no installs.

## Run it

```bash
cd Control-Page
python3 server.py
# HT36 Control-Page on http://localhost:8736/ (open in Chrome or Edge)
```

Open http://localhost:8736/ in Chrome, click **Connect watch**, and pick `HT36`. Close the watch's vendor
phone app first: the watch accepts one Bluetooth connection at a time.

## Android

Web Bluetooth needs `localhost` or HTTPS, so a plain LAN address will not work on a phone:
- USB: enable USB debugging, open `chrome://inspect` on the computer, add port forwarding `8736 → localhost:8736`,
  then open `http://localhost:8736/` on the phone.
- Or put the service behind any HTTPS reverse proxy you trust.

## Files

| File | What |
|---|---|
| `server.py` | the service and its JSON API (routes listed in its docstring) |
| `page-body.html` | the whole page: HTML, CSS and JS in one file |
| `db.py` | SQLite store: Bluetooth logs, watch info, health `metrics`, `tracks`, `voice_notes` |
| `resources.py` | the Resources page: every tool, repo and doc the project uses, and why |
| `test_server.py` | `python3 -m unittest test_server` |
| `scripts/` | Python BLE probes using `bleak` (`scan.py`, `gatt.py` read-only discovery, `probe.py` handshake + battery + info) |
| `data/`, `logs/` | your database, voice notes and logs (git-ignored: personal health data) |

To run the probes (disconnect the browser page first):

```bash
cd Control-Page
python3 -m venv .venv && .venv/bin/pip install -r scripts/requirements.txt
.venv/bin/python scripts/probe.py
```

## Pages

Every watch app has its own URL: `/heart-rate`, `/alarms`, `/settings`, `/workouts-gps/tracks`, `/voice-notes`, …
plus `/bluetooth-log`, `/lab` and `/resources`.

## Safety

The page never lists the watch's firmware-update (OTA) service (`e49a3001…`) in `optionalServices`, so the
browser cannot write to it. A test checks this.
