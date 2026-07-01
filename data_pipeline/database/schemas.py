from sqlalchemy import create_engine, Table, Column, Integer, String, Float, Boolean, Meta_Data, Enum, ForeignKey
from sqlalchemy.sql import select, insert, update
import enum

metadata = Meta_Data()

class ProcessingStage(enum.Enum):
    QUEUED = "Queued"
    DOWNLOADING = "Downloading"
    DOWNLOADED = "Downloaded"
    CHECKSUM_PASSED = "Checksum Passed"
    ZIP_VERIFIED = "ZIP Verified"
    EXTRACTED = "Extracted"
    METADATA_PARSED = "Metadata Parsed"
    INDEXED = "Indexed"
    READY = "Ready For Feature Pipeline"
    ARCHIVED = "Archived"
    FAILED = "Failed"
    REJECTED = "Rejected"

manifest = Table(
    "manifest", metadata,
    Column("id", Integer, primary_key=True),
    Column("url", String, unique=True),
    Column("filename", String),
    Column("instrument", String),
    Column("product", String),
    Column("year", String),
    Column("month", String),
    Column("date", String),
    Column("download_timestamp", String),
    Column("checksum", String),
    Column("zip_verified", Boolean, default=False),
    Column("fits_verified", Boolean, default=False),
    Column("metadata_indexed", Boolean, default=False),
    Column("size", Integer),
    Column("retry_count", Integer, default=0),
    Column("download_speed", Float),
    Column("processing_stage", String),
    Column("dataset_version", String),
    Column("remarks", String),
)

fits_metadata = Table(
    "fits_metadata", metadata,
    Column("id", Integer, primary_key=True),
    Column("manifest_id", Integer, ForeignKey("manifest.id")),
    Column("instrument", String),
    Column("product", String),
    Column("observation_date", String),
    Column("start_time", String),
    Column("end_time", String),
    Column("cadence", Float),
    Column("exposure", Float),
    Column("rows", Integer),
    Column("cols", Integer),
    Column("energy_range", String),
    Column("mission", String),
)

def init_db(db_path):
    engine = create_engine(f"sqlite:///{db_path}")
    metadata.create_all(engine)
    return engine
