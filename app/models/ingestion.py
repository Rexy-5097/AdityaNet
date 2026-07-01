from datetime import datetime
from sqlmodel import Field, SQLModel


class IngestionRun(SQLModel, table=True):
    __tablename__ = "ingestionrun"

    id: int | None = Field(default=None, primary_key=True)
    source: str = Field(index=True)  # e.g., "GOES_TELEMETRY" or "NOAA_FLARES"
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(default=None)
    records_processed: int = Field(default=0)
    records_inserted: int = Field(default=0)
    records_updated: int = Field(default=0)
    status: str = Field(default="running", index=True)  # "running", "success", "failed"
    error_message: str | None = Field(default=None)
