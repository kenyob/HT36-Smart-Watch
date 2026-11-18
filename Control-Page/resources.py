"""Single source of truth for every resource the HT36 project uses, and why.

The /resources page renders this list. Keep it curated: when the project starts or stops using a tool,
a repo, a doc or an endpoint, edit it here. Each entry: category, name, url (optional), what, why.
"""

RESOURCES = [
    # ---- The watch itself ----
    {"cat": "Watch", "name": "HT36 (BRUBOSES, Amazon)", "url": "https://manuals.plus/ko/asin/B0FDGPTYJN",
     "what": "The device: rugged GPS smartwatch, BLE only, Bluetooth calling, AI-voice button.",
     "why": "The thing we are controlling. Model string AT364DV003105, type NAL-WB00, screen 240×296."},
    {"cat": "Watch", "name": "Actions ATS3085 SoC", "url": "https://products.psacertified.org/products/ats3085-ats3089-series",
     "what": "The chip family the firmware string and SDK point to (M4F 96 MHz + DSP, 8 MB OPI).",
     "why": "Settles the processor question (it is Actions, not Telink). Guides any firmware work."},
    {"cat": "Watch", "name": "GloryFitPro (vendor app)", "url": "https://apps.apple.com/us/app/gloryfit/id1237479843",
     "what": "The official phone app, SDK com.yc.nadalsdk (vendor UTE / Youchuangyi).",
     "why": "Its APK is the realistic reverse-engineering target: it holds every command, incl. the face-delete frame we lack."},

    # ---- Protocol prior art ----
    {"cat": "Protocol", "name": "tcsenpai/ht36", "url": "https://github.com/tcsenpai/ht36",
     "what": "MIT, TypeScript. Reverse-engineered HT36 BLE client: frames, watchface encoder, GPS, health sync.",
     "why": "Our protocol came from here. Every frame on the Screens tab is ported from its proto.ts (read-only; we don't run it)."},
    {"cat": "Protocol", "name": "LydianLover/WatchLink (APK in apk/)", "url": "https://github.com/LydianLover/WatchLink",
     "what": "Independent Android app for GloryFitPro / ATS3085 watches. v1.15 APK downloaded. Does face install/switch/delete + an editor, incl. always-on faces and the slot-full workaround. Targets AT364CD (P131), sibling of our AT364D.",
     "why": "It has SOLVED the custom-face upload our prior art was blocked on. Decompile its classes.dex with REA to read the real delete/install frames. THE key target."},
    {"cat": "Protocol", "name": "Gadgetbridge GloryFit / GloryFitPro", "url": "https://gadgetbridge.org/gadgets/wearables/gloryfitpro/",
     "what": "Open companion-app project; partial GloryFitPro support, Wireshark dissector + Frida script in gadgetbridge-tools.",
     "why": "Cross-check of the protocol and a second implementation to compare frames against."},
    {"cat": "Protocol", "name": "Gadgetbridge DM58 PR #6401", "url": "https://codeberg.org/Freeyourgadget/Gadgetbridge/pulls/6401",
     "what": "Open Java PR adding GloryFitPro support for the DM58 (ATS3085L), the same BLE dialect (com.yc.gloryfitpro).",
     "why": "A second, readable (non-obfuscated) implementation of our protocol to compare frame-by-frame against WatchLink."},
    {"cat": "Protocol", "name": "gadgetbridge-tools (Codeberg, jayyee)", "url": "https://codeberg.org/jayyee/Gadgetbridge-tools",
     "what": "PoC helper scripts with a gloryfit/ folder: a Wireshark dissector for the GloryFit protocol.",
     "why": "Decodes captured BLE packets into named fields — speeds up reading an HCI btsnoop capture later."},

    # ---- Watch faces ----
    {"cat": "Faces", "name": "ArnCepTech/ATSDialFactory", "url": "https://github.com/ArnCepTech/ATSDialFactory",
     "what": "GPL-3.0, TypeScript. Browser watch-face editor for ATS3085L IDO watches; .iwf face format.",
     "why": "Reference for the face-file format and an editor UX for our own face builder (goal: add/edit clock faces)."},

    # ---- Firmware (gated) ----
    {"cat": "Firmware", "name": "sonigeez/actions-adfu", "url": "https://github.com/sonigeez/actions-adfu",
     "what": "MIT, Python. Flashes Actions ATS30xx firmware over USB ADFU mode (no vendor Windows tool).",
     "why": "A possible firmware route WITHOUT opening the case. Write-only, brick-capable → needs the owner's explicit yes before any use."},
    {"cat": "Firmware", "name": "REA (reverse-engineer-anything)", "url": "",
     "what": "The reverse-engineering toolset available in this session (mcp__rea__* / the reverse-engineer-anything skill).",
     "why": "Decompiles a binary we HOLD — the WatchLink APK in apk/ first; watch firmware only once we have a flash dump or ADFU image."},
    {"cat": "Firmware", "name": "apk/ (apps for analysis)", "url": "",
     "what": "apk/WatchLink-v1.15.apk (from GitHub releases); docs/GloryFitPro-HOW-TO-GET.md (Play Store + adb pull).",
     "why": "Static-analysis targets. Untrusted: read/decompile only, never installed or run (AGENTS rule 3)."},

    # ---- Tools we used ----
    {"cat": "Tools", "name": "jadx 1.5.6", "url": "https://github.com/skylot/jadx",
     "what": "Apache-2.0 Android decompiler (installed with Homebrew; JAR in jar/, git-ignored).",
     "why": "Turned the WatchLink and GloryFitPro APKs into readable Java to find the frame builders."},
    {"cat": "Tools", "name": "apkeep 1.1.0 (EFF)", "url": "https://github.com/EFForg/apkeep",
     "what": "MIT. Downloads a specific app version (we used the APKPure source, research only).",
     "why": "Got GloryFitPro 1.8.6.2, 1.9.0.2, 1.9.0.3 and 1.9.2 for the version diff without a phone."},
    {"cat": "Tools", "name": "bleak", "url": "https://github.com/hbldh/bleak",
     "what": "MIT Python BLE library (scripts/requirements.txt).",
     "why": "The scan, GATT discovery and probe scripts that found and first read the watch."},
    {"cat": "Tools", "name": "Leaflet 1.9.4 + OpenStreetMap", "url": "https://leafletjs.com/",
     "what": "BSD-2-Clause map library loaded from unpkg; tiles © OpenStreetMap contributors.",
     "why": "The map on the GPS Tracks page."},
    {"cat": "Tools", "name": "Playwright + headless Chrome", "url": "https://playwright.dev/",
     "what": "Apache-2.0 browser automation.",
     "why": "Checks that each page renders and works (fake mic, GPX import) without touching the real watch."},
    {"cat": "Tools", "name": "REAP prompts (Skills/)", "url": "",
     "what": "MIT reverse-engineering workflows by Joas Antonio dos Santos (Skills/REAP-LICENSE).",
     "why": "The audit-an-APK, trace-a-feature and version-comparison workflows we followed."},

    # ---- Our build ----
    {"cat": "Ours", "name": "Control-Page", "url": "http://localhost:8736/",
     "what": "This local page + service: Web Bluetooth control, Bluetooth log, Lab, GPS, resources.",
     "why": "The cockpit. The browser talks to the watch; the service stores logs, tests and watch info in SQLite."},
    {"cat": "Ours", "name": "Project docs", "url": "",
     "what": "docs/01-discover.md (GATT map + prior art), docs/04-plan-all-features.md (the plan).",
     "why": "What the watch is, how we talk to it, and the route to every feature + the three goals."},
]

CATEGORIES = ["Watch", "Protocol", "Faces", "Firmware", "Tools", "Ours"]

# Private-only entries (not in the public repo) live in resources_private.py, if present.
try:
    from resources_private import RESOURCES as _PRIVATE
    RESOURCES = RESOURCES + _PRIVATE
except ImportError:
    pass
