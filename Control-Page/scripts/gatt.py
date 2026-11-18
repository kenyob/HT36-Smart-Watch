import asyncio, sys
from bleak import BleakScanner, BleakClient
async def main():
    d = await BleakScanner.find_device_by_name("HT36", timeout=15)
    if not d: print("not found"); return
    async with BleakClient(d, timeout=30) as c:
        for s in c.services:
            print("SVC", s.uuid, s.description)
            for ch in s.characteristics:
                line = f"  CHR {ch.uuid} {','.join(ch.properties)}"
                if "read" in ch.properties:
                    try:
                        v = await c.read_gatt_char(ch)
                        line += f"  = {v.hex()} {v.decode('utf-8','replace')!r}"
                    except Exception as e: line += f"  (read err {e})"
                print(line)
asyncio.run(main())
