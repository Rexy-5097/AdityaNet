import asyncio
from sqlalchemy import text
from app.db.session import async_session_maker

async def main():
    async with async_session_maker() as session:
        await session.execute(text("DELETE FROM backfillcheckpoint;"))
        await session.execute(text("DELETE FROM flareevent WHERE EXTRACT(year FROM start_time) = 2015;"))
        await session.commit()
        print("Checkpoints and 2015 flare events deleted successfully!")

if __name__ == "__main__":
    asyncio.run(main())
