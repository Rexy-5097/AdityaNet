import os
import json
from typing import Any, Dict, List
from fastapi import APIRouter, Depends, status
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text
from app.db.session import get_session
from app.models.ingestion import IngestionRun

router = APIRouter()


@router.get("/ingestion-status", status_code=status.HTTP_200_OK)
async def get_ingestion_status(
    session: AsyncSession = Depends(get_session),
) -> List[Dict[str, Any]]:
    """Retrieve the latest ingestion status summary for all telemetry and catalog sources."""
    # Query the most recent run for GOES Telemetry
    goes_stmt = (
        select(IngestionRun)
        .where(IngestionRun.source == "GOES_TELEMETRY")
        .order_by(IngestionRun.started_at.desc())
        .limit(1)
    )
    # Query the most recent run for NOAA Flares catalog
    flares_stmt = (
        select(IngestionRun)
        .where(IngestionRun.source == "NOAA_FLARES")
        .order_by(IngestionRun.started_at.desc())
        .limit(1)
    )

    goes_result = await session.execute(goes_stmt)
    goes_run = goes_result.scalar_one_or_none()

    flares_result = await session.execute(flares_stmt)
    flares_run = flares_result.scalar_one_or_none()

    response = []

    if goes_run:
        response.append(
            {
                "last_run": goes_run.completed_at or goes_run.started_at,
                "source": "GOES_TELEMETRY",
                "records": goes_run.records_processed,
                "status": goes_run.status,
            }
        )

    if flares_run:
        response.append(
            {
                "last_run": flares_run.completed_at or flares_run.started_at,
                "source": "NOAA_FLARES",
                "records": flares_run.records_processed,
                "status": flares_run.status,
            }
        )

    return response


@router.get("/dataset-summary", status_code=status.HTTP_200_OK)
async def get_dataset_summary(
    session: AsyncSession = Depends(get_session),
) -> Dict[str, Any]:
    """Retrieve database record counts, date ranges, and quality metrics, and write report to disk."""
    # 1. Count GOES records
    goes_cnt_stmt = text("SELECT COUNT(*) FROM goesxrs;")
    goes_cnt = (await session.execute(goes_cnt_stmt)).scalar() or 0

    # 2. Count Flare records
    flare_cnt_stmt = text("SELECT COUNT(*) FROM flareevent;")
    flare_cnt = (await session.execute(flare_cnt_stmt)).scalar() or 0

    # 3. Count M and X class flares
    m_cnt_stmt = text("SELECT COUNT(*) FROM flareevent WHERE flare_class LIKE 'M%';")
    m_cnt = (await session.execute(m_cnt_stmt)).scalar() or 0

    x_cnt_stmt = text("SELECT COUNT(*) FROM flareevent WHERE flare_class LIKE 'X%';")
    x_cnt = (await session.execute(x_cnt_stmt)).scalar() or 0

    # 4. Get date range
    range_stmt = text("SELECT MIN(timestamp), MAX(timestamp) FROM goesxrs;")
    range_res = (await session.execute(range_stmt)).fetchone()
    min_time, max_time = None, None
    if range_res and range_res[0] is not None:
        min_time = range_res[0].isoformat()
        max_time = range_res[1].isoformat()

    # 5. Data quality metrics (missing minutes, gap percentage)
    missing_minutes = 0
    gap_percentage = 0.0
    if goes_cnt > 0 and range_res and range_res[0] is not None:
        delta = range_res[1] - range_res[0]
        expected_minutes = int(delta.total_seconds() / 60) + 1
        missing_minutes = max(0, expected_minutes - goes_cnt)
        gap_percentage = (missing_minutes / expected_minutes) * 100

    # 6. Quality flag distribution
    q_dist_stmt = text("SELECT quality_flag, COUNT(*) FROM goesxrs GROUP BY quality_flag;")
    q_dist_res = (await session.execute(q_dist_stmt)).fetchall()
    quality_flag_distribution = {str(row[0]): row[1] for row in q_dist_res}

    # 7. Class distribution
    class_dist_stmt = text(
        "SELECT SUBSTRING(flare_class FROM 1 FOR 1) AS letter, COUNT(*) "
        "FROM flareevent GROUP BY letter;"
    )
    class_dist_res = (await session.execute(class_dist_stmt)).fetchall()
    class_distribution = {"A": 0, "B": 0, "C": 0, "M": 0, "X": 0}
    for row in class_dist_res:
        letter = row[0].upper()
        if letter in class_distribution:
            class_distribution[letter] = row[1]

    summary = {
        "goes_records": goes_cnt,
        "flare_records": flare_cnt,
        "m_class_count": m_cnt,
        "x_class_count": x_cnt,
        "date_range": {
            "start": min_time,
            "end": max_time,
        },
        "missing_minutes": missing_minutes,
        "gap_percentage": gap_percentage,
        "quality_flag_distribution": quality_flag_distribution,
        "class_distribution": class_distribution,
    }

    # Save to artifacts/dataset_summary.json
    artifacts_dir = "artifacts"
    os.makedirs(artifacts_dir, exist_ok=True)
    summary_path = os.path.join(artifacts_dir, "dataset_summary.json")
    try:
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
    except Exception as e:
        # Ignore write errors to prevent API failure
        pass

    return summary


@router.get("/class-distribution", status_code=status.HTTP_200_OK)
async def get_class_distribution(
    session: AsyncSession = Depends(get_session),
) -> Dict[str, int]:
    """Retrieve the class distribution of historical flare records."""
    class_dist_stmt = text(
        "SELECT SUBSTRING(flare_class FROM 1 FOR 1) AS letter, COUNT(*) "
        "FROM flareevent GROUP BY letter;"
    )
    class_dist_res = (await session.execute(class_dist_stmt)).fetchall()
    class_distribution = {"A": 0, "B": 0, "C": 0, "M": 0, "X": 0}
    for row in class_dist_res:
        letter = row[0].upper()
        if letter in class_distribution:
            class_distribution[letter] = row[1]
    return class_distribution
