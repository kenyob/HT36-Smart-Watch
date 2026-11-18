"""SQLite store for the HT36 Control-Page: Bluetooth logs, test runs, and watch info/content.

One file, Python 3.9 stdlib only. The DB lives at Control-Page/data/ht36.db (git-ignored).

Tables:
  frames    — every Bluetooth frame the page saves (one row per frame), tagged with a session id.
  sessions  — one row per saved log batch / test run: when, how many frames, a note.
  watch     — key/value snapshot of the watch (firmware, battery, MAC, face table, probe results).
  metrics   — every health/motion reading we can track (steps, HR, SpO2, stress, kcal, distance, battery, GPS
              points, history records), one row per reading. `source` is 'ht36' for this watch, and 'apple' /
              'fitbit' / 'browser' for reference data, so a dual-wear comparison lines up by timestamp
              (docs/07-testing-plan-and-log.md). `trial` tags a test run.
  tracks / track_points — GPS tracks (browser reference recordings, GPX imports, later the watch's own tracks).
  voice_notes — recorded voice notes; audio files in data/voice/, transcript filled in later by a local engine.
"""

import math

import csv
import io

import json
import sqlite3
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "data" / "ht36.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS sessions (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  kind      TEXT NOT NULL DEFAULT 'log',   -- 'log' | 'test' | 'probe'
  created   REAL NOT NULL,
  note      TEXT,
  frames    INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS frames (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  session   INTEGER NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
  ts        REAL,          -- seconds since the page connected, from the log entry
  dir       TEXT,          -- tx | rx | sys | err
  ch        TEXT,          -- channel, e.g. 34F1
  hex       TEXT,          -- space-separated bytes
  meaning   TEXT
);
CREATE INDEX IF NOT EXISTS ix_frames_session ON frames(session);
CREATE TABLE IF NOT EXISTS metrics (
  id        INTEGER PRIMARY KEY AUTOINCREMENT,
  ts        REAL NOT NULL,           -- epoch seconds (UTC) the reading refers to
  recorded  REAL NOT NULL,           -- epoch seconds it was stored
  source    TEXT NOT NULL DEFAULT 'ht36',
  metric    TEXT NOT NULL,           -- steps | kcal | distance_m | hr | spo2 | stress | battery | gps | ...
  value     REAL,
  unit      TEXT,
  kind      TEXT,                    -- live | summary | history | push | import
  trial     TEXT,                    -- optional test-run label
  extra     TEXT,                    -- JSON: lat/lon/alt for gps, raw fields, etc.
  UNIQUE(source, metric, ts, trial)
);
CREATE INDEX IF NOT EXISTS ix_metrics_metric_ts ON metrics(metric, ts);
CREATE TABLE IF NOT EXISTS tracks (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  name       TEXT,
  source     TEXT NOT NULL DEFAULT 'browser',  -- browser | ht36 | apple | fitbit | strava | gpx
  kind       TEXT NOT NULL DEFAULT 'record',   -- record (live in the browser) | import | watch
  trial      TEXT,
  started    REAL,
  ended      REAL,
  points     INTEGER NOT NULL DEFAULT 0,
  distance_m REAL NOT NULL DEFAULT 0,
  created    REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS track_points (
  track  INTEGER NOT NULL REFERENCES tracks(id) ON DELETE CASCADE,
  ts     REAL, lat REAL NOT NULL, lon REAL NOT NULL, alt REAL, acc REAL, hr REAL
);
CREATE INDEX IF NOT EXISTS ix_track_points ON track_points(track, ts);
CREATE TABLE IF NOT EXISTS voice_notes (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  created    REAL NOT NULL,
  title      TEXT,
  mic        TEXT,              -- mac | watch
  mime       TEXT,              -- audio/webm, audio/ogg, application/octet-stream (raw watch stream)
  file       TEXT,              -- file name under data/voice/
  bytes      INTEGER,
  duration_s REAL,
  status     TEXT NOT NULL DEFAULT 'pending',   -- pending | transcribed | failed
  transcript TEXT,
  engine     TEXT,
  trial      TEXT
);
CREATE TABLE IF NOT EXISTS watch (
  key       TEXT PRIMARY KEY,
  value     TEXT,
  updated   REAL NOT NULL
);
"""


def connect():
    DB_PATH.parent.mkdir(exist_ok=True)
    cx = sqlite3.connect(DB_PATH)
    cx.row_factory = sqlite3.Row
    cx.execute("PRAGMA foreign_keys = ON")
    cx.executescript(SCHEMA)
    return cx


def save_session(entries, kind="log", note=None):
    """entries: list of log dicts from the page {t|ts, dir, ch, hex, m|meaning}. Returns the session id."""
    cx = connect()
    try:
        cur = cx.execute("INSERT INTO sessions(kind, created, note, frames) VALUES (?,?,?,?)",
                         (kind, time.time(), note, len(entries)))
        sid = cur.lastrowid
        rows = [(sid, e.get("t", e.get("ts")), e.get("dir"), e.get("ch"),
                 e.get("hex"), e.get("m", e.get("meaning"))) for e in entries]
        cx.executemany("INSERT INTO frames(session, ts, dir, ch, hex, meaning) VALUES (?,?,?,?,?,?)", rows)
        cx.commit()
        return sid
    finally:
        cx.close()


def list_sessions(limit=100):
    cx = connect()
    try:
        return [dict(r) for r in cx.execute(
            "SELECT id, kind, created, note, frames FROM sessions ORDER BY id DESC LIMIT ?", (limit,))]
    finally:
        cx.close()


def session_frames(sid):
    cx = connect()
    try:
        return [dict(r) for r in cx.execute(
            "SELECT ts, dir, ch, hex, meaning FROM frames WHERE session=? ORDER BY id", (sid,))]
    finally:
        cx.close()


def set_watch(info):
    """info: dict of key -> value (value is JSON-encoded if not a string)."""
    cx = connect()
    try:
        now = time.time()
        for k, v in info.items():
            cx.execute("INSERT INTO watch(key, value, updated) VALUES (?,?,?) "
                       "ON CONFLICT(key) DO UPDATE SET value=excluded.value, updated=excluded.updated",
                       (k, v if isinstance(v, str) else json.dumps(v), now))
        cx.commit()
    finally:
        cx.close()


def get_watch():
    cx = connect()
    try:
        return {r["key"]: {"value": r["value"], "updated": r["updated"]}
                for r in cx.execute("SELECT key, value, updated FROM watch ORDER BY key")}
    finally:
        cx.close()


METRIC_COLS = ("ts", "recorded", "source", "metric", "value", "unit", "kind", "trial", "extra")


def add_metrics(rows):
    """rows: list of {ts, metric, value?, unit?, source?, kind?, trial?, extra?}. Duplicates (same source,
    metric, ts, trial) are ignored, so re-syncing history is safe. Returns how many rows were new."""
    cx = connect()
    try:
        now, n = time.time(), 0
        for r in rows:
            if not isinstance(r, dict) or not r.get("metric") or r.get("ts") is None:
                continue
            extra = r.get("extra")
            cur = cx.execute(
                "INSERT OR IGNORE INTO metrics(ts, recorded, source, metric, value, unit, kind, trial, extra) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                (float(r["ts"]), now, str(r.get("source") or "ht36"), str(r["metric"]),
                 None if r.get("value") is None else float(r["value"]), r.get("unit"), r.get("kind"),
                 r.get("trial") or "", None if extra is None else (extra if isinstance(extra, str) else json.dumps(extra))))
            n += cur.rowcount
        cx.commit()
        return n
    finally:
        cx.close()


def query_metrics(metric=None, source=None, trial=None, since=None, until=None, limit=5000):
    where, args = [], []
    for col, v in (("metric", metric), ("source", source), ("trial", trial)):
        if v:
            vals = v.split(",")
            where.append("%s IN (%s)" % (col, ",".join("?" * len(vals))))
            args += vals
    if since is not None:
        where.append("ts >= ?"); args.append(float(since))
    if until is not None:
        where.append("ts <= ?"); args.append(float(until))
    sql = "SELECT %s FROM metrics%s ORDER BY ts DESC LIMIT ?" % (
        ", ".join(METRIC_COLS), " WHERE " + " AND ".join(where) if where else "")
    cx = connect()
    try:
        return [dict(r) for r in cx.execute(sql, args + [int(limit)])]
    finally:
        cx.close()


def metrics_summary():
    cx = connect()
    try:
        return [dict(r) for r in cx.execute(
            "SELECT source, metric, COUNT(*) AS n, MIN(ts) AS first, MAX(ts) AS last FROM metrics "
            "GROUP BY source, metric ORDER BY source, metric")]
    finally:
        cx.close()


def metrics_csv(rows):
    out = io.StringIO()
    w = csv.writer(out)
    w.writerow(("time_utc",) + METRIC_COLS)
    for r in sorted(rows, key=lambda r: r["ts"]):
        w.writerow((time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(r["ts"])),) + tuple(r[c] for c in METRIC_COLS))
    return out.getvalue()


# ---------- GPS tracks ----------


def voice_dir():
    return DB_PATH.parent / "voice"   # follows DB_PATH, so tests stay isolated


def _hav(a, b):
    r = 6371000.0
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(h)))


def _clean_points(points):
    out = []
    for q in points or []:
        try:
            lat, lon = float(q["lat"]), float(q["lon"])
        except (KeyError, TypeError, ValueError):
            continue
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            g = lambda k: None if q.get(k) is None else float(q[k])
            out.append((g("ts"), lat, lon, g("alt"), g("acc"), g("hr")))
    return out


def _add_points(cx, tid, pts):
    last = cx.execute("SELECT lat, lon FROM track_points WHERE track=? ORDER BY rowid DESC LIMIT 1", (tid,)).fetchone()
    dist, prev = 0.0, (last["lat"], last["lon"]) if last else None
    for p in pts:
        if prev:
            dist += _hav(prev, (p[1], p[2]))
        prev = (p[1], p[2])
    cx.executemany("INSERT INTO track_points(track, ts, lat, lon, alt, acc, hr) VALUES (?,?,?,?,?,?,?)", [(tid,) + p for p in pts])
    times = [p[0] for p in pts if p[0] is not None]
    cx.execute("UPDATE tracks SET points=points+?, distance_m=distance_m+?, started=COALESCE(started, ?), "
               "ended=CASE WHEN ? IS NULL THEN ended ELSE MAX(COALESCE(ended, 0), ?) END WHERE id=?",
               (len(pts), dist, min(times) if times else None, max(times) if times else None, max(times) if times else None, tid))


def create_track(meta, points=()):
    cx = connect()
    try:
        tid = cx.execute("INSERT INTO tracks(name, source, kind, trial, created) VALUES (?,?,?,?,?)",
                         (meta.get("name") or "Track", meta.get("source") or "browser", meta.get("kind") or "record",
                          meta.get("trial") or "", time.time())).lastrowid
        _add_points(cx, tid, _clean_points(points))
        cx.commit()
        return tid
    finally:
        cx.close()


def append_points(tid, points):
    cx = connect()
    try:
        if not cx.execute("SELECT 1 FROM tracks WHERE id=?", (tid,)).fetchone():
            return None
        pts = _clean_points(points)
        _add_points(cx, tid, pts)
        cx.commit()
        return len(pts)
    finally:
        cx.close()


def update_row(table, rid, fields, allowed):
    sets = {k: v for k, v in fields.items() if k in allowed}
    if not sets:
        return False
    cx = connect()
    try:
        cur = cx.execute("UPDATE %s SET %s WHERE id=?" % (table, ", ".join(k + "=?" for k in sets)), list(sets.values()) + [rid])
        cx.commit()
        return cur.rowcount > 0
    finally:
        cx.close()


def list_tracks(limit=500):
    cx = connect()
    try:
        return [dict(r) for r in cx.execute("SELECT * FROM tracks ORDER BY COALESCE(started, created) DESC LIMIT ?", (limit,))]
    finally:
        cx.close()


def track_detail(tid):
    cx = connect()
    try:
        row = cx.execute("SELECT * FROM tracks WHERE id=?", (tid,)).fetchone()
        if not row:
            return None
        pts = [dict(r) for r in cx.execute("SELECT ts, lat, lon, alt, acc, hr FROM track_points WHERE track=? ORDER BY rowid", (tid,))]
        return dict(row, track_points=pts)
    finally:
        cx.close()


def delete_row(table, rid):
    cx = connect()
    try:
        cur = cx.execute("DELETE FROM %s WHERE id=?" % table, (rid,))
        cx.commit()
        return cur.rowcount > 0
    finally:
        cx.close()


# ---------- voice notes ----------
def add_note(meta, data, ext):
    voice_dir().mkdir(parents=True, exist_ok=True)
    cx = connect()
    try:
        nid = cx.execute("INSERT INTO voice_notes(created, title, mic, mime, bytes, duration_s, trial) VALUES (?,?,?,?,?,?,?)",
                         (time.time(), meta.get("title") or "Voice note", meta.get("mic") or "mac", meta.get("mime"),
                          len(data), meta.get("duration_s"), meta.get("trial") or "")).lastrowid
        name = "note-%d.%s" % (nid, ext)
        (voice_dir() / name).write_bytes(data)
        cx.execute("UPDATE voice_notes SET file=? WHERE id=?", (name, nid))
        cx.commit()
        return nid
    finally:
        cx.close()


def list_notes(limit=500):
    cx = connect()
    try:
        return [dict(r) for r in cx.execute("SELECT * FROM voice_notes ORDER BY created DESC LIMIT ?", (limit,))]
    finally:
        cx.close()


def get_note(nid):
    cx = connect()
    try:
        r = cx.execute("SELECT * FROM voice_notes WHERE id=?", (nid,)).fetchone()
        return dict(r) if r else None
    finally:
        cx.close()


def delete_note(nid):
    n = get_note(nid)
    if not n:
        return False
    if n.get("file"):
        f = voice_dir() / n["file"]
        if f.is_file():
            f.unlink()
    return delete_row("voice_notes", nid)
