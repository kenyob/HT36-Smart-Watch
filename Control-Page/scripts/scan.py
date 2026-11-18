import asyncio
from bleak import BleakScanner
async def main():
    found = await BleakScanner.discover(timeout=15, return_adv=True)
    for addr,(d,adv) in sorted(found.items(), key=lambda x: -x[1][1].rssi):
        name = adv.local_name or d.name
        if not name: continue
        print(f"{adv.rssi:>4} {addr} {name!r} svc={adv.service_uuids} mfr={ {k:v.hex() for k,v in adv.manufacturer_data.items()} }")
asyncio.run(main())
