# Read-only P0 probe: only AA query frames + A1 handshake. Never touches OTA e49a*.
import asyncio, time
from bleak import BleakScanner, BleakClient
U=lambda s: f"0000{s}-0000-1000-8000-00805f9b34fb"
W34, N34, W35, N35 = U("34f1"), U("34f2"), U("35f1"), U("35f2")
t0=time.time(); log=[]
def on(name):
    def cb(_, data):
        b=bytes(data); log.append((round(time.time()-t0,2), name, b.hex()))
        print(f"{time.time()-t0:6.2f} {name} {b.hex(' ')}  {b.decode('latin1','replace')!r}")
    return cb
async def main():
    d = await BleakScanner.find_device_by_name("HT36", timeout=15)
    if not d: print("not found"); return
    async with BleakClient(d, timeout=30) as c:
        print("connected")
        for u,n in ((N34,"34F2"),(N35,"35F2"),(U("ffd2"),"FFD2"),(U("ffd3"),"FFD3")):
            try: await c.start_notify(u, on(n))
            except Exception as e: print("notify fail", n, e)
        await asyncio.sleep(2)
        print(">> 35F1 a1 (handshake)"); await c.write_gatt_char(W35, bytes([0xa1]), response=True); await asyncio.sleep(2)
        print(">> 34F1 01a4aa16 (battery)"); await c.write_gatt_char(W34, bytes.fromhex("01a4aa16"), response=False); await asyncio.sleep(2)
        print(">> 34F1 01a4aaaa (device info)"); await c.write_gatt_char(W34, bytes.fromhex("01a4aaaa"), response=False); await asyncio.sleep(5)
        print("listening 25s for stream..."); await asyncio.sleep(25)
    print(f"done, {len(log)} frames")
asyncio.run(main())
