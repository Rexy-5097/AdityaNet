from datetime import datetime
from sqlmodel import Field, SQLModel


class GOESXRS(SQLModel, table=True):
    __tablename__ = "goesxrs"

    timestamp: datetime = Field(primary_key=True, index=True)
    satellite: int
    short_flux: float | None = Field(default=None)
    long_flux: float | None = Field(default=None)
    source: str = Field(default="NOAA_GOES_PRIMARY")
    quality_flag: int = Field(default=0)
    source_file: str | None = Field(default=None)
    processing_version: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
