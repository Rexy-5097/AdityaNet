from datetime import date, datetime
from sqlmodel import Field, SQLModel


class BackfillCheckpoint(SQLModel, table=True):
    __tablename__ = "backfillcheckpoint"

    source: str = Field(primary_key=True)  # "GOES_BACKFILL" or "FLARE_BACKFILL"
    last_processed_date: date
    status: str = Field(default="in_progress")  # "in_progress", "completed", "failed"
    updated_at: datetime = Field(default_factory=datetime.utcnow)
