from datetime import date, datetime
from sqlalchemy import select
from app.db.session import async_session_maker
from app.models.checkpoint import BackfillCheckpoint


class CheckpointManager:
    @staticmethod
    async def get_checkpoint(source: str) -> date | None:
        """Retrieve the last successfully processed date for a given backfill source."""
        async with async_session_maker() as session:
            stmt = select(BackfillCheckpoint).where(BackfillCheckpoint.source == source)
            result = await session.execute(stmt)
            checkpoint = result.scalar_one_or_none()
            if checkpoint:
                return checkpoint.last_processed_date
            return None

    @staticmethod
    async def update_checkpoint(
        source: str, last_date: date, status: str = "in_progress"
    ) -> None:
        """Update or insert a backfill checkpoint for a given source."""
        async with async_session_maker() as session:
            stmt = select(BackfillCheckpoint).where(BackfillCheckpoint.source == source)
            result = await session.execute(stmt)
            checkpoint = result.scalar_one_or_none()

            if checkpoint:
                checkpoint.last_processed_date = last_date
                checkpoint.status = status
                checkpoint.updated_at = datetime.utcnow()
            else:
                checkpoint = BackfillCheckpoint(
                    source=source,
                    last_processed_date=last_date,
                    status=status,
                    updated_at=datetime.utcnow(),
                )
            session.add(checkpoint)
            await session.commit()
