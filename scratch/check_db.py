import asyncio
import os
import sys
from sqlalchemy import text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import async_session_maker

async def main():
    async with async_session_maker() as session:
        # Get count of goesxrs
        res = await session.execute(text("SELECT count(*) FROM goesxrs;"))
        goes_count = res.scalar()
        
        # Get count of flareevent
        res = await session.execute(text("SELECT count(*) FROM flareevent;"))
        flare_count = res.scalar()
        
        # Get count of M-class flares
        res = await session.execute(text("SELECT count(*) FROM flareevent WHERE flare_class LIKE 'M%';"))
        m_count = res.scalar()

        # Get count of X-class flares
        res = await session.execute(text("SELECT count(*) FROM flareevent WHERE flare_class LIKE 'X%';"))
        x_count = res.scalar()
        
        # Get checkpoints
        res = await session.execute(text("SELECT source, last_processed_date, status, updated_at FROM backfillcheckpoint;"))
        checkpoints = res.fetchall()
        
        print("=========================================")
        print(f"GOES records count: {goes_count:,}")
        print(f"Flare event count:  {flare_count:,} (M: {m_count:,}, X: {x_count:,})")
        print("=========================================")
        print("Checkpoints:")
        for cp in checkpoints:
            print(f"  Source: {cp[0]}, Last processed: {cp[1]}, Status: {cp[2]}, Updated: {cp[3]}")
        print("=========================================")

if __name__ == "__main__":
    asyncio.run(main())
