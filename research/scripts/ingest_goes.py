import asyncio
import logging
import os
import sys

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ingestion.ingestion_service import IngestionService

# Simple formatting for script console output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)


async def main() -> None:
    print("==================================================")
    print("SuryaNet NOAA Data Ingestion CLI")
    print("==================================================")

    service = IngestionService()

    # Step 1: GOES X-ray Flux Ingestion
    try:
        print("\n[1/2] Commencing GOES XRS 7-day telemetry ingestion...")
        goes_run = await service.ingest_goes_xray()
        print(f" -> Status: {goes_run.status.upper()}")
        print(f" -> Records Processed: {goes_run.records_processed}")
        print(f" -> Records Inserted:  {goes_run.records_inserted}")
        print(f" -> Records Updated:   {goes_run.records_updated}")
    except Exception as e:
        print(f" -> ERROR: GOES ingestion failed: {e}")

    # Step 2: NOAA Solar Flare Catalog Ingestion
    try:
        print("\n[2/2] Commencing NOAA solar flare events catalog ingestion...")
        flare_run = await service.ingest_flares()
        print(f" -> Status: {flare_run.status.upper()}")
        print(f" -> Records Processed: {flare_run.records_processed}")
        print(f" -> Records Inserted:  {flare_run.records_inserted}")
        print(f" -> Records Updated:   {flare_run.records_updated}")
    except Exception as e:
        print(f" -> ERROR: Flare ingestion failed: {e}")

    print("\n==================================================")
    print("Ingestion CLI Pipeline Complete.")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(main())
