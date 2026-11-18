"""Read-only live probe while the watch is worn. Only AA queries + the labelled read frames found in WatchLink.
No AB sets that change device state. Saves logs/live-<time>.jsonl."""
import asyncio, json, time
from pathlib import Path
from bleak import BleakScanner, BleakClient
U = lambda s: f"0000{s}-0000-1000-8000-00805f9b34fb"
W34, N34, W35, N35 = U("34f1"), U("34f2"), U("35f1"), U("35f2")
QUERIES = [
    ("handshake", "35F1", "a1"),
    ("battery", "34F1", "01a4aa16"),
    ("find-wear state (on wrist?)", "34F1", "01a5aa07"),
    ("config toggles", "34F1", "01a5aa01"),
    ("HR auto enabled", "34F1", "01e1aa10"),
    ("SpO2 auto enabled", "34F1", "01e1aa11"),
    ("GNSS params", "34F1", "01e9aa01"),
    ("watchface info", "34F1", "01e3aaaa"),
    ("watchface table", "34F1", "01e3aa0b"),
    ("today activity (WatchLink 26 01)", "34F1", "012601"),
]
OUT = Path(__file__).resolve().parent.parent / "logs" / time.strftime("live-%Y%m%d-%H%M%S.jsonl")
async def main():
    OUT.parent.mkdir(exist_ok=True); t0=time.time(); cur={"q":None}; f=OUT.open("w")
    def rec(**k): k["t"]=round(time.time()-t0,2); f.write(json.dumps(k)+"\n"); f.flush()
    def on(ch):
        def cb(_,data):
            b=bytes(data); rec(dir="rx",ch=ch,hex=b.hex(),during=cur["q"])
            print(f"   <- {ch} {b.hex(' ')}  |{''.join(chr(x) if 32<=x<127 else '.' for x in b)}|")
        return cb
    d=await BleakScanner.find_device_by_name("HT36",timeout=15)
    if not d: print("NOT FOUND - is the browser page connected? disconnect it first."); return
    async with BleakClient(d,timeout=30) as c:
        print("connected to", d.name)
        for u,n in ((N34,"34F2"),(N35,"35F2"),(U("ffd2"),"FFD2"),(U("ffd3"),"FFD3")):
            try: await c.start_notify(u,on(n))
            except Exception as e: print("notify fail",n,e)
        await asyncio.sleep(3)
        for name,ch,hx in QUERIES:
            b=bytes.fromhex(hx); cur["q"]=name
            print(f"-> {ch} {b.hex(' ')}  [{name}]"); rec(dir="tx",ch=ch,hex=b.hex(),name=name)
            await (c.write_gatt_char(W35,b,response=True) if ch=="35F1" else c.write_gatt_char(W34,b,response=False))
            await asyncio.sleep(3)
        print("listening 20s for any stream (HR/steps) while worn..."); await asyncio.sleep(20)
    f.close(); print("saved", OUT)
asyncio.run(main())
