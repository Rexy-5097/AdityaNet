import argparse
import asyncio
import logging
import os
import sys
from datetime import datetime, date

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.backfill.flare_backfill import FlareBackfillService
from app.db.init_db import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


async def main() -> None:
    parser = argparse.ArgumentParser(description="SuryaNet Flare Catalog Backfill CLI")
    parser.add_argument(
        "--start-date",
        type=str,
        default="2010-01-01",
        help="Start date in YYYY-MM-DD format (default: 2010-01-01)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=date.today().strftime("%Y-%m-%d"),
        help="End date in YYYY-MM-DD format (default: today)",
    )
    args = parser.parse_args()

    try:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end_date = datetime.strptime(args.end_date, "%Y-%m-%d").date()
    except ValueError as e:
        logger.error(f"Invalid date format. Use YYYY-MM-DD: {e}")
        sys.exit(1)

    print("==================================================")
    print("SuryaNet: Flare Events Historical Backfill")
    print(f"Target Range: {start_date} -> {end_date}")
    print("==================================================")

    # Initialize database tables and hypertables
    await init_db()

    service = FlareBackfillService()
    try:
        await service.backfill(start_date, end_date)
        print("\nFlare Events Backfill Successful!")
    except Exception as e:
        print(f"\nERROR: Flare Events Backfill failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
