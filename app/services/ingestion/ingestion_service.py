import logging
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.db.session import async_session_maker
from app.models.flare import FlareEvent
from app.models.goes import GOESXRS
from app.models.ingestion import IngestionRun
from app.services.ingestion.flare_client import FlareClient
from app.services.ingestion.goes_client import GOESClient

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self) -> None:
        self.goes_client = GOESClient()
        self.flare_client = FlareClient()

    async def ingest_goes_xray(self) -> IngestionRun:
        """Fetch, validate, and bulk-upsert GOES XRS telemetry, logging run status."""
        logger.info("Starting GOES X-ray telemetry ingestion...")
        run = IngestionRun(source="GOES_TELEMETRY", status="running")

        # Save initial run status
        async with async_session_maker() as session:
            session.add(run)
            await session.commit()
            await session.refresh(run)

        try:
            # 1. Fetch and validate DataFrame
            df = await self.goes_client.fetch_and_validate()

            if df.empty:
                run.status = "success"
                run.completed_at = datetime.utcnow()
                run.records_processed = 0
                run.records_inserted = 0
                run.records_updated = 0
                async with async_session_maker() as session:
                    session.add(run)
                    await session.commit()
                logger.info("GOES ingestion complete: 0 records processed.")
                return run

            # 2. Convert DataFrame rows to records dicts
            records = df.to_dict(orient="records")

            # 3. Perform bulk upsert in batches to avoid query parameter limit (32767)
            chunk_size = 2000
            records_updated = 0
            records_inserted = 0

            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                chunk_timestamps = [r["timestamp"] for r in chunk]

                async with async_session_maker() as session:
                    # Determine existing for this chunk
                    stmt = select(GOESXRS.timestamp).where(
                        GOESXRS.timestamp.in_(chunk_timestamps)
                    )
                    result = await session.execute(stmt)
                    existing_chunk_timestamps = set(result.scalars().all())

                    chunk_updated = len(existing_chunk_timestamps)
                    chunk_inserted = len(chunk) - chunk_updated

                    records_updated += chunk_updated
                    records_inserted += chunk_inserted

                    # Perform bulk upsert for this chunk
                    insert_stmt = insert(GOESXRS).values(chunk)
                    update_cols = {
                        col.name: col
                        for col in insert_stmt.excluded
                        if col.name not in ["timestamp", "created_at"]
                    }
                    upsert_stmt = insert_stmt.on_conflict_do_update(
                        index_elements=["timestamp"], set_=update_cols
                    )
                    await session.execute(upsert_stmt)
                    await session.commit()

            # 4. Log success stats
            run.status = "success"
            run.completed_at = datetime.utcnow()
            run.records_processed = len(records)
            run.records_inserted = records_inserted
            run.records_updated = records_updated

            async with async_session_maker() as session:
                session.add(run)
                await session.commit()
                await session.refresh(run)

            logger.info(
                f"GOES Ingestion successful: processed={run.records_processed}, "
                f"inserted={run.records_inserted}, updated={run.records_updated}"
            )
            return run

        except Exception as e:
            logger.error(f"GOES Ingestion failed: {e}")
            run.status = "failed"
            run.completed_at = datetime.utcnow()
            run.error_message = str(e)

            async with async_session_maker() as session:
                session.add(run)
                await session.commit()

            raise e

    async def ingest_flares(self) -> IngestionRun:
        """Fetch, validate, and bulk-upsert NOAA solar flare events, logging run status."""
        logger.info("Starting NOAA solar flare events ingestion...")
        run = IngestionRun(source="NOAA_FLARES", status="running")

        # Save initial run status
        async with async_session_maker() as session:
            session.add(run)
            await session.commit()
            await session.refresh(run)

        try:
            # 1. Fetch and validate DataFrame
            df = await self.flare_client.fetch_and_validate()

            if df.empty:
                run.status = "success"
                run.completed_at = datetime.utcnow()
                run.records_processed = 0
                run.records_inserted = 0
                run.records_updated = 0
                async with async_session_maker() as session:
                    session.add(run)
                    await session.commit()
                logger.info("NOAA flares ingestion complete: 0 records processed.")
                return run

            # 2. Convert DataFrame rows to records dicts
            records = df.to_dict(orient="records")

            # 3. Perform bulk upsert in batches
            chunk_size = 2000
            records_updated = 0
            records_inserted = 0

            for i in range(0, len(records), chunk_size):
                chunk = records[i:i + chunk_size]
                chunk_event_ids = [r["event_id"] for r in chunk]

                async with async_session_maker() as session:
                    # Determine existing for this chunk
                    stmt = select(FlareEvent.event_id).where(
                        FlareEvent.event_id.in_(chunk_event_ids)
                    )
                    result = await session.execute(stmt)
                    existing_chunk_event_ids = set(result.scalars().all())

                    chunk_updated = len(existing_chunk_event_ids)
                    chunk_inserted = len(chunk) - chunk_updated

                    records_updated += chunk_updated
                    records_inserted += chunk_inserted

                    # Perform bulk upsert for this chunk
                    insert_stmt = insert(FlareEvent).values(chunk)
                    update_cols = {
                        col.name: col
                        for col in insert_stmt.excluded
                        if col.name not in ["event_id", "created_at"]
                    }
                    upsert_stmt = insert_stmt.on_conflict_do_update(
                        index_elements=["event_id"], set_=update_cols
                    )
                    await session.execute(upsert_stmt)
                    await session.commit()

            # 4. Log success stats
            run.status = "success"
            run.completed_at = datetime.utcnow()
            run.records_processed = len(records)
            run.records_inserted = records_inserted
            run.records_updated = records_updated

            async with async_session_maker() as session:
                session.add(run)
                await session.commit()
                await session.refresh(run)

            logger.info(
                f"NOAA Flares Ingestion successful: processed={run.records_processed}, "
                f"inserted={run.records_inserted}, updated={run.records_updated}"
            )
            return run

        except Exception as e:
            logger.error(f"NOAA Flares Ingestion failed: {e}")
            run.status = "failed"
            run.completed_at = datetime.utcnow()
            run.error_message = str(e)

            async with async_session_maker() as session:
                session.add(run)
                await session.commit()

            raise e

