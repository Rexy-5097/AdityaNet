import asyncio
from sqlalchemy import select, extract
from app.db.session import async_session_maker
from app.models.flare import FlareEvent

async def main():
    async with async_session_maker() as session:
        # Check flare events for 2015
        stmt = select(FlareEvent).where(extract('year', FlareEvent.start_time) == 2015)
        res = await session.execute(stmt)
        flares = res.scalars().all()
        print("Total 2015 flare events in DB:", len(flares))
        for fl in flares[:20]:
            print(f"ID: {fl.event_id}, Class: {fl.flare_class}, Region: {fl.region_number}, Loc: {fl.location}, Imp: {fl.importance}, Start: {fl.start_time}")

if __name__ == "__main__":
    asyncio.run(main())
