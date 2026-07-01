import asyncio
import logging
from datetime import date
from app.services.backfill.flare_backfill import FlareBackfillService, SWPCEventFetcher

logging.basicConfig(level=logging.INFO)

def parse_original(text_content):
    lines = text_content.splitlines()
    count = 0
    for line in lines:
        line_str = line.strip()
        if not line_str or line_str.startswith("#") or line_str.startswith(":"):
            continue
        padded = line_str.ljust(80)
        event_type = padded[43:48].strip()
        if event_type in ["XRA", "FLA"]:
            count += 1
    return count

def parse_new(text_content):
    lines = text_content.splitlines()
    count = 0
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith(":"):
            continue
        padded = line.ljust(85)
        event_type = padded[42:47].strip()
        if event_type in ["XRA", "FLA"]:
            count += 1
    return count

async def test():
    fetcher = SWPCEventFetcher()
    
    for filename in ["20150718events.txt", "20240101events.txt"]:
        content = fetcher.fetch_file(filename)
        if not content:
            print(f"Failed to fetch {filename}")
            continue
        orig = parse_original(content)
        new = parse_new(content)
        print(f"File {filename}:")
        print(f"  Original parsing count: {orig}")
        print(f"  New parsing count: {new}")

if __name__ == "__main__":
    asyncio.run(test())
