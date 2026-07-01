import asyncio
import logging
from datetime import date
from app.services.backfill.goes_backfill import GOESBackfillService

logging.basicConfig(level=logging.INFO)

async def test():
    service = GOESBackfillService()
    for month in range(1, 13):
        discovered = await service.discover_nc_files(2010, month)
        print(f"2010-{month:02d}: discovered {len(discovered)} files. Satellites: {set(d['satellite'] for d in discovered)}")

asyncio.run(test())
