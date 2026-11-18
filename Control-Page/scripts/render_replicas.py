#!/usr/bin/env python3
"""Render a 240x296 browser-replica PNG of each app/face screen into its watch-face-pages folder.

These are OUR renders of the watch twin (what the Control-Page draws from state) - NOT a capture of the real
watch screen, which BLE can't provide. App screens are representative; face screens are labelled placeholders
until we fetch the real face file. Saves to watch-face-pages/<slug>/replica.png.

    python3 render_replicas.py          # needs Google Chrome (headless)

Illustrative values (steps, HR, weather) are placeholders.
"""

import subprocess
import sys
import tempfile
from pathlib import Path

PAGES = Path(__file__).resolve().parents[2] / "watch-face-pages"
W, H = 240, 296

CHROME_CANDIDATES = [
    "/Volumes/HomeX/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]

SHELL = """<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px;overflow:hidden}}
body{{background:#000;color:#fff;font-family:"Segoe UI",system-ui,Arial,sans-serif;position:relative}}
.c{{position:absolute;inset:0;padding:16px;display:flex;flex-direction:column}}
.c.center{{align-items:center;justify-content:center;text-align:center;gap:8px}}
.acc{{color:#ff5a1f}}.dim{{color:#9a9a9a}}
.big{{font-weight:800;line-height:1}}
.tag{{position:absolute;bottom:8px;left:0;right:0;text-align:center;font-size:9px;color:#555}}
</style></head><body><div class="c {cls}">{body}</div><div class="tag">{tag}</div></body></html>"""

# (cls, body_html, tag) per app. cls="center" centres the screen.
APP_SCREENS = {
    "watch-faces": ("", '<div class="acc" style="font-size:11px">WED 18 NOV</div><div class="big" style="font-size:58px">10:48</div>'
                    '<div style="display:flex;gap:10px;margin-top:16px;font-size:11px" class="dim"><span>❤ 72</span><span>6,120</span><span>100%</span></div>', "replica · default face"),
    "activity": ("center", '<div style="font-size:40px">\U0001F45F</div><div class="big" style="font-size:44px">6,120</div><div class="dim" style="font-size:12px">steps · goal 8,000</div>'
                 '<div style="font-size:11px" class="dim">312 kcal · 4.7 km</div>', "replica · illustrative"),
    "heart-rate": ("center", '<div class="acc" style="font-size:36px">❤</div><div class="big" style="font-size:50px">72</div><div class="dim" style="font-size:12px">bpm · resting 61</div>', "replica · illustrative"),
    "blood-oxygen": ("center", '<div class="big acc" style="font-size:50px">98%</div><div class="dim" style="font-size:12px">SpO₂</div>', "replica · illustrative"),
    "stress": ("center", '<div class="big" style="font-size:50px">34</div><div class="dim" style="font-size:12px">stress · relaxed</div>', "replica · illustrative"),
    "sleep": ("center", '<div style="font-size:34px">\U0001F634</div><div class="big" style="font-size:40px">7h 12m</div><div class="dim" style="font-size:11px">deep 1h40 · light 4h30</div>', "replica · illustrative"),
    "workouts-gps": ("center", '<div style="font-size:30px">\U0001F3C3</div><div class="big" style="font-size:34px">5.21 km</div><div class="dim" style="font-size:11px">28:40 · GPS fixed</div>', "replica · illustrative"),
    "weather": ("center", '<div style="font-size:40px">⛅</div><div class="big" style="font-size:44px">7°</div><div class="dim" style="font-size:12px">H 9° L 2° · Milan</div>', "replica · illustrative"),
    "notifications": ("", '<div class="acc" style="font-size:12px">✉ Messages</div><div style="font-size:14px;margin-top:8px">Assistant: your 3pm is moved to 3:30. Want me to tell the team?</div>', "replica · illustrative"),
    "alarms": ("center", '<div style="font-size:30px">⏰</div><div class="big" style="font-size:40px">06:30</div><div class="dim" style="font-size:11px">Mon–Fri</div>', "replica · unmapped"),
    "timer-stopwatch": ("center", '<div class="big" style="font-size:46px">00:45</div><div class="dim" style="font-size:12px">stopwatch</div>', "replica · unmapped"),
    "music-control": ("center", '<div style="font-size:30px">♪</div><div class="big" style="font-size:20px">Now Playing</div><div class="dim" style="font-size:11px">◀◀  ‖  ▶▶</div>', "replica · unmapped"),
    "find": ("center", '<div style="font-size:40px">\U0001F4F3</div><div class="big" style="font-size:22px">Vibrating</div>', "replica"),
    "calling": ("center", '<div style="font-size:34px">\U0001F4DE</div><div class="big" style="font-size:20px">Incoming</div><div class="dim" style="font-size:12px">illustrative</div>', "replica · unmapped"),
    "settings": ("", '<div class="acc" style="font-size:12px">⚙ Settings</div><div style="font-size:12px;margin-top:10px;line-height:1.9">Screen on 5s<br>Raise to wake ●<br>Units: km<br>Scroll speed: ?</div>', "replica · illustrative"),
}


def face_screen(fid):
    return ("center", f'<div class="dim" style="font-size:11px">FACE</div><div class="big acc" style="font-size:26px">{fid}</div>'
            '<div class="dim" style="font-size:10px;padding:0 14px">true design unknown until the face file is fetched</div>',
            "placeholder · not the real face")


def render(chrome, cls, body, tag, out):
    html = SHELL.format(w=W, h=H, cls=cls, body=body, tag=tag)
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False, encoding="utf-8") as f:
        f.write(html); path = f.name
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars",
                    f"--window-size={W},{H}", f"--screenshot={out}",
                    "--user-data-dir=/private/tmp/claude-504/replica-chrome", "file://" + path],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=30)
    Path(path).unlink(missing_ok=True)


def main():
    chrome = next((c for c in CHROME_CANDIDATES if Path(c).exists()), None)
    if not chrome:
        print("Google Chrome not found"); sys.exit(1)
    n = 0
    for slug, (cls, body, tag) in APP_SCREENS.items():
        out = PAGES / slug / "replica.png"
        if out.parent.exists():
            render(chrome, cls, body, tag, str(out)); n += 1
    for md in PAGES.glob("face-*.md"):
        fid = md.stem.replace("face-", "")
        cls, body, tag = face_screen(fid)
        out = PAGES / f"face-{fid}" / "replica.png"
        if out.parent.exists():
            render(chrome, cls, body, tag, str(out)); n += 1
    print(f"rendered {n} replica PNGs into {PAGES}")


if __name__ == "__main__":
    main()
