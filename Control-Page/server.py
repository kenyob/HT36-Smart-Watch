#!/usr/bin/env python3
"""HT36 Control-Page: a small local web service for controlling the HT36 watch over Web Bluetooth.

The browser talks to the watch; this service serves the pages and keeps a SQLite store of logs, test
runs and watch info. Standard library only, Python 3.9+. Web Bluetooth needs a secure origin and
http://localhost counts, so the default bind is 127.0.0.1.

    python3 server.py                 # http://localhost:8736/
    python3 server.py --port 9000

Pages (every tab and watch app has its own URL; the page routes from the path):
    /                Apps (watch faces)     /bluetooth-log   Bluetooth log (/log also works)
    /<app-slug>      one watch app, e.g. /heart-rate, /alarms, /settings (APP_SLUGS below)
    /lab             Lab                    /resources       every tool/repo/doc we use and why

API:
    GET  /api/health                  {"ok": true, ...}
    GET  /api/resources               the resources catalog (JSON)
    POST /api/log       body=[frames] save a Bluetooth log batch to SQLite; ?note=&kind=
    GET  /api/sessions                saved log/test sessions, newest first
    GET  /api/session?id=N            the frames of one session
    POST /api/watch     body={k:v}    store a watch-info snapshot
    GET  /api/watch                   the stored watch info (verify:<control> keys hold wrist-test results)
    GET  /face-img/<6-hex id>         a real image of that face if one exists (photo or cloud preview), else 404
    POST /api/metrics   body=[rows]   store health/motion readings {ts, metric, value, unit, source, kind, trial, extra}
    GET  /api/metrics?metric=hr,spo2&source=&trial=&since=&until=&limit=   readings, newest first
    GET  /api/metrics.csv?...         the same as CSV (for the dual-wear comparison)
    GET  /api/metrics/summary         count + first/last time per source and metric
    GET  /api/tracks                  GPS tracks (browser recordings, GPX imports), newest first
    GET  /api/track?id=N              one track with its points
    POST /api/tracks    body={name, source, kind, trial, points:[{ts,lat,lon,alt,acc,hr}]}   create
    POST /api/track/append?id=N body=[points]   add points to a live recording
    POST /api/track/update?id=N body={name, trial}   ·   POST /api/track/delete?id=N
    GET  /api/voice                   voice notes, newest first
    GET  /api/voice/audio?id=N        the audio file
    POST /api/voice?mic=mac|watch&duration=s&title=&trial=   body = raw audio (Content-Type = its type)
    POST /api/voice/update?id=N body={title, transcript, status, engine}   ·   POST /api/voice/delete?id=N
    GET  /api/media?app=Music         now playing on this Mac (Music or Spotify), via osascript
    POST /api/media?cmd=next&app=..   play|pause|previous|next|volup|voldown, then now playing

page-body.html is the whole control page (HTML + CSS + JS in one file), so it can also be embedded in another
app unchanged. It routes with real paths here and with #hash URLs when embedded.
"""

import argparse
import html
import json
import subprocess
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import db
import resources

HERE = Path(__file__).resolve().parent
BODY_FILE = HERE / "page-body.html"
FACE_DIR = HERE.parent / "watch-face-pages"  # face-<id>/photo-*.jpg|png or cloud-preview.png = real face images
MAX_LOG_BYTES = 20 * 1024 * 1024
APP_SLUGS = ("voice-notes", "watch-faces", "activity", "heart-rate", "blood-oxygen", "stress", "sleep", "workouts-gps", "weather",
             "notifications", "alarms", "timer-stopwatch", "music-control", "find", "calling", "dnd", "reminders",
             "goals-profile", "settings")
TABS = {"/": "screens", "/screens": "screens", "/log": "log", "/bluetooth-log": "log", "/lab": "lab"}
TABS.update({"/" + s: "screens" for s in APP_SLUGS})
TABS["/workouts-gps/tracks"] = "screens"   # sub-page of Workouts + GPS
MAX_AUDIO_BYTES = 60 * 1024 * 1024
AUDIO_EXT = {"audio/webm": "webm", "audio/ogg": "ogg", "audio/mp4": "m4a", "application/octet-stream": "bin"}

# Mac media control for the watch's music buttons. Only these two apps and these commands; nothing else reaches osascript.
MEDIA_APPS = ("Music", "Spotify")
MEDIA_CMDS = {"play": "play", "pause": "pause", "previous": "previous track", "next": "next track"}


def osascript(script):
    r = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, timeout=6)
    if r.returncode:
        raise RuntimeError(r.stderr.strip() or "osascript failed")
    return r.stdout.strip()


def media(app, cmd=None):
    """Run one media command on Music or Spotify (macOS only) and return what is playing."""
    if sys.platform != "darwin":
        raise RuntimeError("media control needs macOS")
    if app not in MEDIA_APPS:
        raise RuntimeError("app must be Music or Spotify")
    if cmd in ("volup", "voldown"):
        osascript("set volume output volume ((output volume of (get volume settings)) %s 6)" % ("+" if cmd == "volup" else "-"))
    elif cmd:
        if cmd not in MEDIA_CMDS:
            raise RuntimeError("unknown command")
        osascript('if application "%s" is running then tell application "%s" to %s' % (app, app, MEDIA_CMDS[cmd]))
    out = osascript('if application "%s" is running then tell application "%s" to return (artist of current track) & "\n" & '
                    '(name of current track) & "\n" & (player state as string)' % (app, app))
    vol = osascript("output volume of (get volume settings)")
    parts = out.split("\n") if out else []
    if len(parts) < 3:
        return {"artist": "", "title": "%s is not playing" % app, "playing": False, "vol": round(int(vol or 0) / 100 * 16), "vmax": 16}
    return {"artist": parts[0], "title": parts[1], "playing": parts[2] == "playing", "vol": round(int(vol or 0) / 100 * 16), "vmax": 16}

SHELL = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HT36 Control</title>
<style>
:root{--bg:#121212;--pad:#262626;--row:#1b1b1b;--rail:#181818;--ink:#f2f2f2;--dim:#a0a0a0;--acc:#ff5a1f;--on-acc:#111;--ok:#3ddc84;--warn:#ffc107;color-scheme:dark}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:15px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
.cp-bar{display:flex;justify-content:space-between;gap:12px;align-items:center;padding:10px 18px;border-bottom:1px solid #2b2b2b;color:var(--dim);font-size:13px}
.cp-bar a{color:var(--dim);text-decoration:none;margin-left:14px}.cp-bar a:hover,.cp-bar a.on{color:var(--acc)}
.cp-bar b{color:var(--ink)}
__EXTRA_CSS__
</style>
__HEAD__
</head>
<body>
<div class="cp-bar"><span><b>HT36 Control-Page</b> · local service</span>
<span><a href="/" data-nav>Control</a><a href="/resources" data-nav>Resources</a></span></div>
__BODY__
</body>
</html>
"""


def control_page(tab):
    extra = "@media (max-width:1100px){.hw-grid{grid-template-columns:1fr !important}}"
    head = ('<script>window.HT36_SERVICE = true; window.HT36_TAB = %s;</script>' % json.dumps(tab))
    return SHELL.replace("__EXTRA_CSS__", extra).replace("__HEAD__", head).replace(
        "__BODY__", BODY_FILE.read_text(encoding="utf-8")).encode("utf-8")


def resources_page():
    e = html.escape
    rows = []
    for cat in resources.CATEGORIES:
        items = [r for r in resources.RESOURCES if r["cat"] == cat]
        if not items:
            continue
        rows.append('<h2 class="rc-h">%s</h2>' % e(cat))
        for r in items:
            name = e(r["name"])
            if r.get("url"):
                name = '<a href="%s" target="_blank" rel="noopener">%s ↗</a>' % (e(r["url"]), name)
            rows.append(
                '<div class="rc-card"><div class="rc-name">%s</div>'
                '<div class="rc-what">%s</div><div class="rc-why"><b>Why:</b> %s</div></div>'
                % (name, e(r["what"]), e(r["why"])))
    extra = (".rc{max-width:900px;margin:0 auto;padding:22px 18px;display:grid;gap:10px}"
             ".rc h1{margin:0 0 4px;font-size:22px}.rc .lede{margin:0 0 10px;color:var(--dim)}"
             ".rc-h{margin:18px 0 2px;font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--acc)}"
             ".rc-card{background:var(--row);border:1px solid #2b2b2b;border-radius:12px;padding:12px 14px;display:grid;gap:4px}"
             ".rc-name{font-weight:700}.rc-name a{color:var(--ink);text-decoration:none}.rc-name a:hover{color:var(--acc)}"
             ".rc-what{font-size:14px}.rc-why{font-size:13px;color:var(--dim)}")
    body = ('<div class="rc"><h1>Resources</h1>'
            '<p class="lede">Every repo, tool, doc and endpoint this project uses, and why. '
            'Edit the list in <code>Control-Page/resources.py</code>.</p>' + "".join(rows) + "</div>")
    head = ('<script>document.addEventListener("DOMContentLoaded",()=>{'
            'for(const a of document.querySelectorAll(".cp-bar a"))'
            'if(a.getAttribute("href")==="/resources")a.classList.add("on");});</script>')
    return SHELL.replace("__EXTRA_CSS__", extra).replace("__HEAD__", head).replace("__BODY__", body).encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    server_version = "HT36ControlPage/2"

    def send(self, code, body, ctype="application/json"):
        if not isinstance(body, bytes):
            body = json.dumps(body).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", ctype + "; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(body)

    def body_json(self):
        try:
            n = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            n = 0
        if n <= 0 or n > MAX_LOG_BYTES:
            return None, "body must be 1 byte to 20 MB"
        try:
            return json.loads(self.rfile.read(n)), None
        except ValueError:
            return None, "body is not JSON"

    def do_GET(self):
        u = urlparse(self.path)
        p, q = u.path, parse_qs(u.query)
        if p in TABS:
            return self.send(200, control_page(TABS[p]), "text/html")
        if p == "/resources":
            return self.send(200, resources_page(), "text/html")
        if p.startswith("/face-img/"):
            fid = p[len("/face-img/"):]
            if len(fid) == 6 and all(c in "0123456789abcdef" for c in fid):
                folder = FACE_DIR / ("face-" + fid)
                pics = sorted(folder.glob("photo-*.jpg")) + sorted(folder.glob("photo-*.png")) + sorted(folder.glob("cloud-preview.png"))
                if pics:
                    return self.send(200, pics[0].read_bytes(), "image/jpeg" if pics[0].suffix == ".jpg" else "image/png")
            return self.send(404, {"ok": False, "error": "no image for that face yet"})
        if p == "/api/health":
            return self.send(200, {"ok": True, "service": "ht36-control-page", "db": str(db.DB_PATH.name),
                                   "sessions": len(db.list_sessions(limit=100000))})
        if p == "/api/resources":
            return self.send(200, {"ok": True, "resources": resources.RESOURCES, "categories": resources.CATEGORIES})
        if p == "/api/sessions":
            return self.send(200, {"ok": True, "sessions": db.list_sessions()})
        if p == "/api/session":
            try:
                sid = int(q.get("id", ["0"])[0])
            except ValueError:
                return self.send(400, {"ok": False, "error": "id must be an integer"})
            return self.send(200, {"ok": True, "id": sid, "frames": db.session_frames(sid)})
        if p == "/api/watch":
            return self.send(200, {"ok": True, "watch": db.get_watch()})
        if p == "/api/media":
            return self.media_reply(q.get("app", ["Music"])[0], None)
        if p in ("/api/metrics", "/api/metrics.csv"):
            one = lambda k: q.get(k, [None])[0]
            try:
                rows = db.query_metrics(one("metric"), one("source"), one("trial"),
                                        one("since") and float(one("since")), one("until") and float(one("until")),
                                        int(one("limit") or 5000))
            except ValueError:
                return self.send(400, {"ok": False, "error": "since/until/limit must be numbers"})
            if p.endswith(".csv"):
                return self.send(200, db.metrics_csv(rows).encode("utf-8"), "text/csv")
            return self.send(200, {"ok": True, "metrics": rows})
        if p == "/api/tracks":
            return self.send(200, {"ok": True, "tracks": db.list_tracks()})
        if p == "/api/track":
            d = db.track_detail(self.qid(q))
            return self.send(200 if d else 404, {"ok": bool(d), "track": d} if d else {"ok": False, "error": "no such track"})
        if p == "/api/voice":
            return self.send(200, {"ok": True, "notes": db.list_notes()})
        if p == "/api/voice/audio":
            n = db.get_note(self.qid(q))
            f = n and n.get("file") and db.voice_dir() / n["file"]
            if not f or not f.is_file():
                return self.send(404, {"ok": False, "error": "no such recording"})
            return self.send(200, f.read_bytes(), n.get("mime") or "application/octet-stream")
        if p == "/api/metrics/summary":
            return self.send(200, {"ok": True, "summary": db.metrics_summary()})
        return self.send(404, {"ok": False, "error": "not found"})

    do_HEAD = do_GET

    def do_POST(self):
        u = urlparse(self.path)
        q = parse_qs(u.query)
        if u.path == "/api/log":
            data, err = self.body_json()
            if err:
                return self.send(400, {"ok": False, "error": err})
            if not isinstance(data, list):
                return self.send(400, {"ok": False, "error": "body must be a JSON list of log entries"})
            sid = db.save_session(data, kind=q.get("kind", ["log"])[0], note=(q.get("note", [None])[0]))
            return self.send(200, {"ok": True, "session": sid, "frames": len(data), "file": "sqlite:sessions/%d" % sid})
        if u.path == "/api/watch":
            data, err = self.body_json()
            if err:
                return self.send(400, {"ok": False, "error": err})
            if not isinstance(data, dict):
                return self.send(400, {"ok": False, "error": "body must be a JSON object of key/value"})
            db.set_watch(data)
            return self.send(200, {"ok": True, "keys": len(data)})
        if u.path == "/api/media":
            return self.media_reply(q.get("app", ["Music"])[0], q.get("cmd", [""])[0])
        if u.path == "/api/tracks":
            data, err = self.body_json()
            if err or not isinstance(data, dict):
                return self.send(400, {"ok": False, "error": err or "body must be a JSON object"})
            tid = db.create_track(data, data.get("points") or [])
            return self.send(200, {"ok": True, "id": tid})
        if u.path in ("/api/track/append", "/api/track/update", "/api/track/delete", "/api/voice/update", "/api/voice/delete"):
            rid = self.qid(q)
            if u.path.endswith("/delete"):
                ok = db.delete_note(rid) if u.path.startswith("/api/voice") else db.delete_row("tracks", rid)
                return self.send(200 if ok else 404, {"ok": ok})
            data, err = self.body_json()
            if err:
                return self.send(400, {"ok": False, "error": err})
            if u.path == "/api/track/append":
                n = db.append_points(rid, data if isinstance(data, list) else [])
                return self.send(200 if n is not None else 404, {"ok": n is not None, "added": n})
            allowed = ("name", "trial") if u.path.startswith("/api/track") else ("title", "transcript", "status", "engine", "trial")
            ok = isinstance(data, dict) and db.update_row("tracks" if u.path.startswith("/api/track") else "voice_notes", rid, data, allowed)
            return self.send(200 if ok else 400, {"ok": bool(ok)})
        if u.path == "/api/voice":
            mime = (self.headers.get("Content-Type") or "application/octet-stream").split(";")[0].strip()
            if mime not in AUDIO_EXT:
                return self.send(400, {"ok": False, "error": "unsupported audio type " + mime})
            try:
                n = int(self.headers.get("Content-Length") or 0)
            except ValueError:
                n = 0
            if n <= 0 or n > MAX_AUDIO_BYTES:
                return self.send(400, {"ok": False, "error": "audio must be 1 byte to 60 MB"})
            one = lambda k: q.get(k, [None])[0]
            try:
                dur = float(one("duration")) if one("duration") else None
            except ValueError:
                dur = None
            nid = db.add_note({"title": one("title"), "mic": one("mic") if one("mic") in ("mac", "watch") else "mac",
                               "mime": mime, "duration_s": dur, "trial": one("trial")}, self.rfile.read(n), AUDIO_EXT[mime])
            return self.send(200, {"ok": True, "id": nid})
        if u.path == "/api/metrics":
            data, err = self.body_json()
            if err:
                return self.send(400, {"ok": False, "error": err})
            if not isinstance(data, list):
                return self.send(400, {"ok": False, "error": "body must be a JSON list of readings"})
            try:
                return self.send(200, {"ok": True, "stored": db.add_metrics(data), "sent": len(data)})
            except (TypeError, ValueError) as e:
                return self.send(400, {"ok": False, "error": "bad reading: %s" % e})
        return self.send(404, {"ok": False, "error": "not found"})

    @staticmethod
    def qid(q):
        try:
            return int(q.get("id", ["0"])[0])
        except ValueError:
            return 0

    def media_reply(self, app, cmd):
        if cmd is not None and cmd not in MEDIA_CMDS and cmd not in ("volup", "voldown"):
            return self.send(400, {"ok": False, "error": "cmd must be one of play, pause, previous, next, volup, voldown"})
        try:
            return self.send(200, {"ok": True, "now": media(app, cmd)})
        except (RuntimeError, subprocess.TimeoutExpired, ValueError) as e:
            return self.send(200, {"ok": False, "error": str(e)})

    def log_message(self, fmt, *args):
        print("%s %s" % (self.log_date_time_string(), fmt % args))


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--host", default="127.0.0.1", help="bind address (default 127.0.0.1; Web Bluetooth needs localhost or HTTPS)")
    ap.add_argument("--port", type=int, default=8736)
    a = ap.parse_args()
    db.connect().close()
    srv = ThreadingHTTPServer((a.host, a.port), Handler)
    host = "localhost" if a.host == "127.0.0.1" else a.host
    print("HT36 Control-Page on http://%s:%d/ (open in Chrome or Edge). Resources: http://%s:%d/resources" % (host, a.port, host, a.port))
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
