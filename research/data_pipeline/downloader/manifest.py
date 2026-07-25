import sqlite3
import os
import threading
import json
from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional
from data_pipeline.downloader.logger import logger

# Global lock to serialize writes across threads
_db_write_lock = threading.Lock()

@dataclass
class DownloadRecord:
    id: Optional[int] = None
    source_url: str = ""
    filename: str = ""
    payload: str = ""
    date: str = ""
    size: int = 0
    checksum: str = ""
    zip_crc: str = ""
    status: str = "Queued"
    download_time: float = 0.0
    download_timestamp: str = ""
    pradan_query_params: str = ""
    http_headers: str = ""
    original_filename: str = ""
    local_filename: str = ""
    path: str = ""
    remarks: str = ""

@dataclass
class FitsMetadataRecord:
    id: Optional[int] = None
    download_id: int = 0
    instrument: str = ""
    observation_date: str = ""
    cadence: float = 0.0
    num_rows: int = 0
    start_time: str = ""
    end_time: str = ""
    energy_channels: str = "[]"
    missing_percentage: float = 0.0

class DownloadManifest:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        # Enable WAL mode and busy timeout for parallel-friendly execution
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        db_dir = os.path.dirname(self.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)
            
        with _db_write_lock:
            conn = self._get_connection()
            try:
                with conn:
                    # Create downloads table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS downloads (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            source_url TEXT UNIQUE,
                            filename TEXT,
                            payload TEXT,
                            date TEXT,
                            size INTEGER,
                            checksum TEXT,
                            zip_crc TEXT,
                            status TEXT,
                            download_time REAL,
                            download_timestamp TEXT,
                            pradan_query_params TEXT,
                            http_headers TEXT,
                            original_filename TEXT,
                            local_filename TEXT,
                            path TEXT,
                            remarks TEXT
                        )
                    """)
                    # Create index on source_url & status
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_downloads_source_url ON downloads(source_url)")
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_downloads_status ON downloads(status)")
                    
                    # Create fits_metadata table
                    conn.execute("""
                        CREATE TABLE IF NOT EXISTS fits_metadata (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            download_id INTEGER,
                            instrument TEXT,
                            observation_date TEXT,
                            cadence REAL,
                            num_rows INTEGER,
                            start_time TEXT,
                            end_time TEXT,
                            energy_channels TEXT,
                            missing_percentage REAL,
                            FOREIGN KEY (download_id) REFERENCES downloads(id) ON DELETE CASCADE
                        )
                    """)
                    conn.execute("CREATE INDEX IF NOT EXISTS idx_fits_metadata_download_id ON fits_metadata(download_id)")
            finally:
                conn.close()

    def insert(self, record: DownloadRecord) -> int:
        """Inserts a new download record into the manifest database."""
        sql = """
            INSERT INTO downloads (
                source_url, filename, payload, date, size, checksum, zip_crc, status,
                download_time, download_timestamp, pradan_query_params, http_headers,
                original_filename, local_filename, path, remarks
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            record.source_url, record.filename, record.payload, record.date, record.size,
            record.checksum, record.zip_crc, record.status, record.download_time,
            record.download_timestamp, record.pradan_query_params, record.http_headers,
            record.original_filename, record.local_filename, record.path, record.remarks
        )
        
        with _db_write_lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute(sql, params)
                    return cursor.lastrowid
            except sqlite3.IntegrityError:
                # If unique constraint fails (e.g. source_url exists), retrieve existing ID
                cursor = conn.execute("SELECT id FROM downloads WHERE source_url = ?", (record.source_url,))
                row = cursor.fetchone()
                return row["id"] if row else -1
            finally:
                conn.close()

    def update(self, record: DownloadRecord):
        """Updates an existing download record in the database."""
        sql = """
            UPDATE downloads SET
                filename = ?, payload = ?, date = ?, size = ?, checksum = ?, zip_crc = ?,
                status = ?, download_time = ?, download_timestamp = ?, pradan_query_params = ?,
                http_headers = ?, original_filename = ?, local_filename = ?, path = ?, remarks = ?
            WHERE id = ?
        """
        params = (
            record.filename, record.payload, record.date, record.size, record.checksum,
            record.zip_crc, record.status, record.download_time, record.download_timestamp,
            record.pradan_query_params, record.http_headers, record.original_filename,
            record.local_filename, record.path, record.remarks, record.id
        )
        
        with _db_write_lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute(sql, params)
            finally:
                conn.close()

    def exists(self, filename: str) -> bool:
        """Checks if a file with the given name exists in the database and is not failed."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT 1 FROM downloads WHERE filename = ? AND status NOT IN ('Failed', 'Queued')",
                (filename,)
            )
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def mark_failed(self, id_or_url: Any, error_msg: str):
        """Marks a download as failed with error remarks."""
        sql = "UPDATE downloads SET status = 'Failed', remarks = ? WHERE id = ? OR source_url = ?"
        with _db_write_lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute(sql, (error_msg, id_or_url, id_or_url))
            finally:
                conn.close()

    def mark_verified(self, record_id: int, checksum: str, zip_crc: str):
        """Marks a download as verified with verified status and checksums."""
        sql = "UPDATE downloads SET status = 'Verified', checksum = ?, zip_crc = ? WHERE id = ?"
        with _db_write_lock:
            conn = self._get_connection()
            try:
                with conn:
                    conn.execute(sql, (checksum, zip_crc, record_id))
            finally:
                conn.close()

    def insert_metadata(self, meta: FitsMetadataRecord) -> int:
        """Inserts or replaces metadata for a FITS file."""
        sql = """
            INSERT OR REPLACE INTO fits_metadata (
                download_id, instrument, observation_date, cadence, num_rows,
                start_time, end_time, energy_channels, missing_percentage
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            meta.download_id, meta.instrument, meta.observation_date, meta.cadence,
            meta.num_rows, meta.start_time, meta.end_time, meta.energy_channels,
            meta.missing_percentage
        )
        
        with _db_write_lock:
            conn = self._get_connection()
            try:
                with conn:
                    cursor = conn.execute(sql, params)
                    return cursor.lastrowid
            finally:
                conn.close()

    def get_pending(self) -> List[DownloadRecord]:
        """Retrieves all records that are Queued or Failed (eligible for retry)."""
        conn = self._get_connection()
        try:
            cursor = conn.execute(
                "SELECT * FROM downloads WHERE status IN ('Queued', 'Failed', 'Downloading')"
            )
            return [self._row_to_record(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_by_source_url(self, source_url: str) -> Optional[DownloadRecord]:
        """Retrieves a single record by its source URL."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM downloads WHERE source_url = ?", (source_url,))
            row = cursor.fetchone()
            return self._row_to_record(row) if row else None
        finally:
            conn.close()

    def get_by_checksum(self, checksum: str) -> Optional[DownloadRecord]:
        """Retrieves a single record by its SHA256 checksum (for duplicate detection)."""
        conn = self._get_connection()
        try:
            cursor = conn.execute("SELECT * FROM downloads WHERE checksum = ? AND status = 'Verified'", (checksum,))
            row = cursor.fetchone()
            return self._row_to_record(row) if row else None
        finally:
            conn.close()

    def statistics(self) -> Dict[str, Any]:
        """Computes download statistics from the database."""
        conn = self._get_connection()
        try:
            # Counts by status
            cursor = conn.execute("SELECT status, count(*), sum(size) FROM downloads GROUP BY status")
            counts = {row["status"]: row[1] for row in cursor.fetchall()}
            
            # Reset cursor for total sizes
            cursor = conn.execute("SELECT sum(size), count(*) FROM downloads WHERE status = 'Verified'")
            row = cursor.fetchone()
            verified_size = row[0] or 0
            verified_count = row[1] or 0
            
            cursor = conn.execute("SELECT count(*) FROM downloads")
            total_count = cursor.fetchone()[0] or 0
            
            cursor = conn.execute("SELECT count(*) FROM downloads WHERE status = 'Failed'")
            failed_count = cursor.fetchone()[0] or 0

            cursor = conn.execute("SELECT count(*) FROM downloads WHERE remarks LIKE '%duplicate%' OR remarks LIKE '%Duplicate%'")
            dup_count = cursor.fetchone()[0] or 0
            
            # Average speed and elapsed download time
            cursor = conn.execute(
                "SELECT sum(download_time), sum(size) FROM downloads WHERE download_time > 0"
            )
            row = cursor.fetchone()
            total_time = row[0] or 0.0
            total_size_downloaded = row[1] or 0
            
            avg_speed_mb = 0.0
            if total_time > 0:
                avg_speed_mb = (total_size_downloaded / (1024 * 1024)) / total_time
                
            return {
                "total_files": total_count,
                "verified_files": verified_count,
                "failed_files": failed_count,
                "duplicate_files": dup_count,
                "downloaded_bytes": verified_size,
                "downloaded_gb": verified_size / (1024**3),
                "total_time_seconds": total_time,
                "average_speed_mb_per_sec": avg_speed_mb
            }
        finally:
            conn.close()

    def _row_to_record(self, row: sqlite3.Row) -> DownloadRecord:
        return DownloadRecord(
            id=row["id"],
            source_url=row["source_url"],
            filename=row["filename"],
            payload=row["payload"],
            date=row["date"],
            size=row["size"],
            checksum=row["checksum"],
            zip_crc=row["zip_crc"],
            status=row["status"],
            download_time=row["download_time"],
            download_timestamp=row["download_timestamp"],
            pradan_query_params=row["pradan_query_params"],
            http_headers=row["http_headers"],
            original_filename=row["original_filename"],
            local_filename=row["local_filename"],
            path=row["path"],
            remarks=row["remarks"]
        )
