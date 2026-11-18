"""Tests for the HT36 Control-Page service. Run: python3 -m unittest test_server (from this folder)."""

import json
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import db  # noqa: E402
import server  # noqa: E402



class ControlPageTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp())
        db.DB_PATH = cls.tmp / "ht36.db"  # isolate the test DB
        cls.srv = ThreadingHTTPServer(("127.0.0.1", 0), server.Handler)
        cls.base = "http://127.0.0.1:%d" % cls.srv.server_address[1]
        threading.Thread(target=cls.srv.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.shutdown()
        shutil.rmtree(cls.tmp)

    def get(self, path):
        with urllib.request.urlopen(self.base + path) as r:
            return r.status, r.read().decode("utf-8")

    def get_json(self, path):
        return json.loads(self.get(path)[1])

    def post(self, path, data):
        req = urllib.request.Request(self.base + path, data=data, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_page_is_served_with_the_service_flag(self):
        code, html = self.get("/")
        self.assertEqual(code, 200)
        self.assertIn("<title>HT36 Control</title>", html)
        self.assertIn("window.HT36_SERVICE = true", html)
        self.assertIn('id="hw-connect"', html)
        self.assertIn('id="lg-svc"', html)

    def test_page_cannot_reach_the_watch_ota_service(self):
        _, html = self.get("/")
        start = html.index("optionalServices")
        self.assertNotIn("e49a", html[start:start + 200].lower())

    def test_log_round_trip_into_sqlite(self):
        code, j = self.post("/api/log?note=unit%20test",
                            json.dumps([{"t": 1.2, "dir": "rx", "ch": "34F2", "hex": "01 a4 aa 16", "m": "battery"}]).encode())
        self.assertEqual(code, 200)
        self.assertTrue(j["ok"])
        sid = j["session"]
        listing = self.get_json("/api/sessions")
        self.assertIn(sid, [s["id"] for s in listing["sessions"]])
        one = self.get_json("/api/session?id=%d" % sid)
        self.assertEqual(one["frames"][0]["meaning"], "battery")

    def test_watch_info_round_trip(self):
        code, j = self.post("/api/watch", json.dumps({"firmware": "AT364DV003105", "battery": "100"}).encode())
        self.assertEqual(code, 200)
        w = self.get_json("/api/watch")
        self.assertEqual(w["watch"]["firmware"]["value"], "AT364DV003105")

    def test_resources_page_and_api(self):
        code, page = self.get("/resources")
        self.assertEqual(code, 200)
        self.assertIn("tcsenpai/ht36", page)
        self.assertIn("WatchLink", page)
        api = self.get_json("/api/resources")
        self.assertTrue(len(api["resources"]) >= 8)

    def test_each_tab_has_its_own_url(self):
        for path, tab in (("/", "screens"), ("/screens", "screens"), ("/log", "log"), ("/lab", "lab")):
            _, page = self.get(path)
            self.assertIn('window.HT36_TAB = "%s"' % tab, page)

    def test_every_app_and_the_bluetooth_log_have_urls(self):
        _, page = self.get("/bluetooth-log")
        self.assertIn('window.HT36_TAB = "log"', page)
        body = server.BODY_FILE.read_text(encoding="utf-8")
        for slug in server.APP_SLUGS:
            code, _ = self.get("/" + slug)
            self.assertEqual(code, 200, slug)
            self.assertIn('slug: "%s"' % slug, body, "page has no app for URL /%s" % slug)

    def test_media_rejects_unknown_commands_and_apps(self):
        code, j = self.post("/api/media?cmd=rm&app=Music", b"")
        self.assertEqual(code, 400)
        code, j = self.post("/api/media?cmd=next&app=Terminal", b"")
        self.assertFalse(j["ok"])

    def test_metrics_round_trip_dedupe_and_csv(self):
        rows = [{"ts": 1795000000, "metric": "hr", "value": 72, "unit": "bpm", "kind": "live"},
                {"ts": 1795000000, "metric": "hr", "value": 72, "unit": "bpm", "kind": "live"},
                {"ts": 1795000060, "metric": "hr", "value": 75, "unit": "bpm", "source": "apple", "kind": "import"}]
        code, j = self.post("/api/metrics", json.dumps(rows).encode())
        self.assertEqual((code, j["stored"]), (200, 2))  # the duplicate is ignored
        got = self.get_json("/api/metrics?metric=hr")["metrics"]
        self.assertEqual(sorted(r["source"] for r in got), ["apple", "ht36"])
        _, csv_text = self.get("/api/metrics.csv?metric=hr&source=apple")
        self.assertIn("2026-", csv_text.splitlines()[1][:5] + "-")
        self.assertIn("apple,hr,75.0,bpm", csv_text)
        summary = self.get_json("/api/metrics/summary")["summary"]
        self.assertIn({"source": "ht36", "metric": "hr"}, [{"source": r["source"], "metric": r["metric"]} for r in summary])

    def post_raw(self, path, data, ctype):
        req = urllib.request.Request(self.base + path, data=data, headers={"Content-Type": ctype}, method="POST")
        try:
            with urllib.request.urlopen(req) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())

    def test_tracks_create_append_distance_and_delete(self):
        pts = [{"ts": 1795000000, "lat": 42.4790, "lon": -71.1520}, {"ts": 1795000060, "lat": 42.4880, "lon": -71.1520}]
        code, j = self.post("/api/tracks", json.dumps({"name": "unit walk", "source": "gpx", "kind": "import", "points": pts}).encode())
        self.assertEqual(code, 200)
        tid = j["id"]
        self.post("/api/track/append?id=%d" % tid, json.dumps([{"ts": 1795000120, "lat": 42.4970, "lon": -71.1520}, {"lat": 999, "lon": 0}]).encode())
        t = self.get_json("/api/track?id=%d" % tid)["track"]
        self.assertEqual(t["points"], 3)  # the out-of-range point is dropped
        self.assertAlmostEqual(t["distance_m"], 2001, delta=15)  # 0.018 deg of latitude is about 2.0 km
        self.assertEqual((t["started"], t["ended"]), (1795000000, 1795000120))
        self.assertEqual(self.post("/api/track/delete?id=%d" % tid, b"")[0], 200)
        self.assertEqual(self.post("/api/track/delete?id=%d" % tid, b"")[0], 404)

    def test_voice_note_upload_play_transcript_delete(self):
        code, j = self.post_raw("/api/voice?mic=mac&duration=1.5&title=unit", b"\x1a\x45\xdf\xa3fake-webm", "audio/webm")
        self.assertEqual(code, 200)
        nid = j["id"]
        with urllib.request.urlopen(self.base + "/api/voice/audio?id=%d" % nid) as r:
            self.assertEqual((r.headers.get_content_type(), r.read()[:4]), ("audio/webm", b"\x1a\x45\xdf\xa3"))
        note = [n for n in self.get_json("/api/voice")["notes"] if n["id"] == nid][0]
        self.assertEqual((note["status"], note["mic"]), ("pending", "mac"))
        self.post("/api/voice/update?id=%d" % nid, json.dumps({"transcript": "hello", "status": "transcribed", "file": "x"}).encode())
        note = [n for n in self.get_json("/api/voice")["notes"] if n["id"] == nid][0]
        self.assertEqual((note["transcript"], note["file"]), ("hello", "note-%d.webm" % nid))  # file is not writable via update
        self.assertEqual(self.post_raw("/api/voice", b"x", "text/html")[0], 400)
        self.assertEqual(self.post("/api/voice/delete?id=%d" % nid, b"")[0], 200)
        self.assertFalse((db.voice_dir() / ("note-%d.webm" % nid)).exists())

    def test_tracks_subpage_url(self):
        code, _ = self.get("/workouts-gps/tracks")
        self.assertEqual(code, 200)

    def test_log_rejects_bad_bodies(self):
        self.assertEqual(self.post("/api/log", b"not json")[0], 400)
        self.assertEqual(self.post("/api/log", b'{"a": 1}')[0], 400)

    def test_unknown_paths_404(self):
        with self.assertRaises(urllib.error.HTTPError) as cm:
            self.get("/../server.py")
        self.assertEqual(cm.exception.code, 404)



if __name__ == "__main__":
    unittest.main()
