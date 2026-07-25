from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from app.db.session import get_session
from app.models.goes import GOESXRS

router = APIRouter()


@router.get(
    "/latest", response_model=GOESXRS, status_code=status.HTTP_200_OK
)
async def get_latest_observation(
    session: AsyncSession = Depends(get_session),
) -> GOESXRS:
    """Retrieve the single most recent GOES XRS telemetry observation."""
    stmt = select(GOESXRS).order_by(GOESXRS.timestamp.desc()).limit(1)
    result = await session.execute(stmt)
    observation = result.scalar_one_or_none()

    if not observation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No GOES telemetry found in database. Execute ingestion pipeline first.",
        )
    return observation


@router.get(
    "/history", response_model=List[GOESXRS], status_code=status.HTTP_200_OK
)
async def get_observation_history(
    limit: int = Query(default=100, ge=1, le=10000),
    session: AsyncSession = Depends(get_session),
) -> List[GOESXRS]:
    """Retrieve a listing of recent GOES XRS telemetry observations ordered by descending time."""
    stmt = select(GOESXRS).order_by(GOESXRS.timestamp.desc()).limit(limit)
    result = await session.execute(stmt)
    observations = result.scalars().all()
    return list(observations)
