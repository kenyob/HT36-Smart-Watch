"""Read-only capability probe for the HT36: sends ONLY query frames (marker AA) and the A1 handshake.
Never writes a set (AB) frame and never touches the OTA service e49a*. Output: logs/probe-<time>.jsonl

    .venv/bin/python scripts/probe_all.py
"""
import asyncio, json, time
from pathlib import Path
from bleak import BleakScanner, BleakClient

U = lambda s: f"0000{s}-0000-1000-8000-00805f9b34fb"
W34, N34, W35, N35 = U("34f1"), U("34f2"), U("35f1"), U("35f2")
QUERIES = [  # (name, channel, hex) -- every frame is a query
    ("handshake", "35F1", "a1"),
    ("battery", "34F1", "01a4aa16"),
    ("device info", "34F1", "01a4aaaa"),
    ("find-wear state", "34F1", "01a5aa07"),
    ("default config toggles", "34F1", "01a5aa01"),
    ("continuous HR enabled", "34F1", "01e1aa10"),
    ("continuous SpO2 enabled", "34F1", "01e1aa11"),
    ("supported message types", "34F1", "01b3aaaa"),
    ("GPS ephemeris params", "34F1", "01e9aa01"),
    ("watchface info", "34F1", "01e3aaaa"),
    ("watchface table", "34F1", "01e3aa0b"),
    ("watchface slot config", "34F1", "01e3aa0c"),
    ("image watchface", "34F1", "01e4aa020100"),
    ("support set C7", "34F1", "01c7aaaa"),
    ("support command A7", "34F1", "01a7aa01"),
]
OUT = Path(__file__).resolve().parent.parent / "logs" / time.strftime("probe-%Y%m%d-%H%M%S.jsonl")

async def main():
    OUT.parent.mkdir(exist_ok=True)
    t0 = time.time(); cur = {"q": None}
    f = OUT.open("w")
    def rec(**kw):
        kw["t"] = round(time.time() - t0, 2); f.write(json.dumps(kw) + "\n"); f.flush()
    def on(ch):
        def cb(_, data):
            b = bytes(data); rec(dir="rx", ch=ch, hex=b.hex(), during=cur["q"])
            print(f"   <- {ch} {b.hex(' ')}  |{''.join(chr(x) if 32 <= x < 127 else '.' for x in b)}|")
        return cb
    d = await BleakScanner.find_device_by_name("HT36", timeout=15)
    if not d: print("not found (is the browser page connected? disconnect it first)"); return
    async with BleakClient(d, timeout=30) as c:
        for u, n in ((N34, "34F2"), (N35, "35F2"), (U("ffd2"), "FFD2"), (U("ffd3"), "FFD3")):
            try: await c.start_notify(u, on(n))
            except Exception as e: print("notify fail", n, e)
        await asyncio.sleep(3)
        for name, ch, hx in QUERIES:
            b = bytes.fromhex(hx.replace(" ", "")); cur["q"] = name
            print(f"-> {ch} {b.hex(' ')}  [{name}]"); rec(dir="tx", ch=ch, hex=b.hex(), name=name)
            if ch == "35F1": await c.write_gatt_char(W35, b, response=True)
            else: await c.write_gatt_char(W34, b, response=False)
            await asyncio.sleep(3)
    f.close(); print("saved", OUT)

asyncio.run(main())
