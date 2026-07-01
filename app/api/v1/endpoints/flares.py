from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import get_session
from app.models.flare import FlareEvent

router = APIRouter()


@router.get(
    "/latest", response_model=List[FlareEvent], status_code=status.HTTP_200_OK
)
async def get_latest_flares(
    limit: int = Query(default=10, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
) -> List[FlareEvent]:
    """Retrieve the most recent solar flare events cataloged from NOAA."""
    stmt = select(FlareEvent).order_by(FlareEvent.start_time.desc()).limit(limit)
    result = await session.execute(stmt)
    flares = result.scalars().all()
    return list(flares)
