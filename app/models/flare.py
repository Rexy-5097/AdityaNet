from datetime import datetime
from sqlalchemy import Index, text
from sqlmodel import Field, SQLModel


class FlareEvent(SQLModel, table=True):
    __tablename__ = "flareevent"

    event_id: str = Field(primary_key=True, index=True)
    start_time: datetime = Field(index=True)
    peak_time: datetime | None = Field(default=None)
    end_time: datetime | None = Field(default=None)
    flare_class: str
    region_number: int | None = Field(default=None)
    location: str | None = Field(default=None)
    importance: str | None = Field(default=None)
    source: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Composite and sorting indexes for machine learning training lookups
    __table_args__ = (
        Index("idx_flare_class_start_time", "flare_class", "start_time"),
        Index("idx_flare_start_time_desc", text("start_time DESC")),
    )
