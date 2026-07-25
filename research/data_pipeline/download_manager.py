import os
import sys
import yaml
import time
import shutil
import argparse
import traceback
from typing import List, Dict, Any
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.progress import Progress, BarColumn, TextColumn, DownloadColumn, TransferSpeedColumn, TimeRemainingColumn

# Add current directory to path to support running from root
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.downloader.logger import logger
from data_pipeline.downloader.session import PradanSession
from data_pipeline.downloader.manifest import DownloadManifest, DownloadRecord, FitsMetadataRecord
from data_pipeline.downloader.downloader import FileDownloader
from data_pipeline.downloader.checksum import calculate_sha256, calculate_crc32, write_checksum_file
from data_pipeline.downloader.verifier import QualityInspector
from data_pipeline.downloader.inventory import InventoryGenerator

class DownloadManager:
    def __init__(self, config_path: str, version_override: str = None):
        self.config_path = config_path
        self.config = self._load_config()
        
        # Apply dataset version override if provided
        if version_override:
            self.config["current_dataset_version"] = version_override
            
        self.version = self.config["current_dataset_version"]
        logger.info(f"Initializing SuryaNet Data Manager for dataset version: {self.version}")
        
        # Resolve version-relative paths
        self.db_path = self.config["manifest_database"].replace("{version}", self.version)
        self.inventory_dir = self.config["inventory_output"].replace("{version}", self.version)
        self.checksums_dir = self.config["checksums_directory"].replace("{version}", self.version)
        self.reports_dir = self.config["reports_directory"].replace("{version}", self.version)
        self.metadata_dir = self.config["metadata_directory"].replace("{version}", self.version)
        self.download_dir = self.config["download_directory"]

        # Ensure folders exist
        os.makedirs(self.download_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # Initialize core components
        self.manifest = DownloadManifest(self.db_path)
        self.session = PradanSession(
            cookie_str=self.config["cookie"],
            base_url=self.config["base_url"],
            retry_count=self.config["retry_count"],
            timeout=self.config["timeout"]
        )
        self.inspector = QualityInspector(
            corrupted_dir=os.path.join(self.download_dir, "corrupted")
        )
        self.downloader = FileDownloader(self.session, self.manifest, self.download_dir)
        self.inventory_gen = InventoryGenerator(self.db_path, self.inventory_dir)

    def _load_config(self) -> Dict[str, Any]:
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def process_file(self, record: DownloadRecord, progress: Progress = None, task_id: Any = None) -> bool:
        """Downloads, validates, checksums, indexes and moves a single telemetry file."""
        filename = record.filename
        try:
            logger.info(f"Processing download for {filename}...")
            
            # Step 1: Download to temp folder
            record.status = "Downloading"
            self.manifest.update(record)
            
            temp_path = self.downloader.download(record, progress, task_id)
            
            # Step 2: Duplicate detection via SHA256 before insertion into archive
            logger.info(f"Calculating SHA256 for duplicate detection on {filename}...")
            sha256_val = calculate_sha256(temp_path)
            
            duplicate = self.manifest.get_by_checksum(sha256_val)
            if duplicate and duplicate.filename != filename:
                logger.warning(f"Duplicate file detected! {filename} shares SHA256 with {duplicate.filename}. Rejecting.")
                record.status = "Rejected"
                record.remarks = f"Duplicate of {duplicate.filename} (SHA256 match)"
                self.manifest.update(record)
                os.remove(temp_path)
                return False

            # Step 3: Verify ZIP structure and FITS integrity
            logger.info(f"Verifying archive structure for {filename}...")
            success, msg = self.inspector.verify_archive(temp_path, record.source_url)
            if not success:
                logger.error(f"Archive verification failed for {filename}: {msg}")
                self.manifest.mark_failed(record.id, f"Verification failed: {msg}")
                return False

            # Step 4: Write checksum to checksums directory
            logger.info(f"Writing SHA256 checksum for {filename}...")
            write_checksum_file(temp_path, sha256_val, self.checksums_dir)
            zip_crc = calculate_crc32(temp_path)

            # Step 5: Move file to final versioned location: downloads/raw/<payload>/<year>/
            year_dir = os.path.join(self.download_dir, "raw", record.payload, record.date[:4])
            os.makedirs(year_dir, exist_ok=True)
            final_path = os.path.join(year_dir, filename)
            
            logger.info(f"Archiving file: {temp_path} -> {final_path}")
            shutil.move(temp_path, final_path)
            
            record.path = final_path
            record.checksum = sha256_val
            record.zip_crc = zip_crc
            record.status = "Verified"
            self.manifest.update(record)

            # Step 6: Scientific quality check & metadata parsing
            logger.info(f"Running FITS science quality checks on {filename}...")
            quality_report = self.inspector.run_quality_check(final_path, record.source_url)
            
            # Extract metadata
            logger.info(f"Extracting scientific metadata for {filename}...")
            meta_dict = self.inspector.extract_metadata(final_path, record.source_url)
            
            # Save metadata record
            meta_record = FitsMetadataRecord(
                download_id=record.id,
                instrument=meta_dict["instrument"],
                observation_date=meta_dict["observation_date"],
                cadence=meta_dict["cadence"],
                num_rows=meta_dict["num_rows"],
                start_time=meta_dict["start_time"],
                end_time=meta_dict["end_time"],
                energy_channels=meta_dict["energy_channels"],
                missing_percentage=quality_report.get("nan_percentage", 0.0)
            )
            self.manifest.insert_metadata(meta_record)
            
            # Update record status with validation details
            if not quality_report.get("valid", True):
                record.status = "Failed"
                record.remarks = f"Quality check failed: {', '.join(quality_report.get('errors', []))}"
            else:
                record.status = "Ready For Feature Pipeline"
                record.remarks = "Passed all ZIP, FITS, and time-series quality verification checks."
            self.manifest.update(record)
            
            logger.info(f"Finished processing {filename} successfully.")
            return True

        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            self.manifest.mark_failed(record.id, f"Unexpected error: {str(e)}")
            temp_dir = os.path.join(self.download_dir, "temp")
            if os.path.exists(partial_path := os.path.join(temp_dir, f"{filename}.part")):
                try:
                    os.remove(partial_path)
                except Exception:
                    pass
            return False

    def run(self):
        """Executes the incremental download & ingestion loop."""
        # Query manifest for queued or failed downloads
        pending_records = self.manifest.get_pending()
        
        if not pending_records:
            logger.info("No pending or failed downloads in manifest. Dynamic sync is up-to-date!")
            self.generate_reports()
            return

        logger.info(f"Found {len(pending_records)} pending downloads in manifest.")
        
        # Determine execution parameters
        parallel = self.config["parallel_downloads"]
        workers = self.config["workers"]
        
        start_time = time.time()
        
        # Setup rich multi-progress bar
        progress = Progress(
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeRemainingColumn()
        )
        
        with progress:
            if parallel and workers > 1:
                logger.info(f"Starting parallel download execution using {workers} worker threads.")
                with ThreadPoolExecutor(max_workers=workers) as executor:
                    # Submit tasks
                    futures = {}
                    for record in pending_records:
                        task_id = progress.add_task(f"Queue: {record.filename}", total=None)
                        futures[executor.submit(self.process_file, record, progress, task_id)] = record
                        
                    for future in as_completed(futures):
                        rec = futures[future]
                        try:
                            future.result()
                        except Exception as e:
                            logger.error(f"Worker thread exception for {rec.filename}: {e}")
            else:
                logger.info("Starting sequential download execution.")
                for record in pending_records:
                    task_id = progress.add_task(f"Downloading: {record.filename}", total=None)
                    self.process_file(record, progress, task_id)

        elapsed = time.time() - start_time
        logger.info(f"Downloads completed in {elapsed:.2f} seconds.")
        
        # Compile final inventory
        self.inventory_gen.generate()
        
        # Generate scientific reports
        self.generate_reports(elapsed)

    def generate_reports(self, elapsed_time: float = 0.0):
        """Generates coverage, missing date, duplicates, and download statistics markdown reports."""
        os.makedirs(self.reports_dir, exist_ok=True)
        report_path = os.path.join(self.reports_dir, "download_report.md")
        
        stats = self.manifest.statistics()
        
        # Query manifest for detailed items
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            # 1. Coverage & Gaps
            cursor = conn.execute("SELECT instrument, count(*), min(observation_date), max(observation_date) FROM fits_metadata GROUP BY instrument")
            instrument_stats = cursor.fetchall()
            
            # 2. Corrupted or Quality Failure Records
            cursor = conn.execute("SELECT filename, payload, date, remarks FROM downloads WHERE status = 'Failed'")
            corrupted_files = cursor.fetchall()
            
            # 3. Duplicate Records
            cursor = conn.execute("SELECT filename, payload, date, remarks FROM downloads WHERE status = 'Rejected' OR remarks LIKE '%duplicate%'")
            duplicate_files = cursor.fetchall()
        finally:
            conn.close()
            
        # Write Markdown Report
        try:
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"# SuryaNet Data Pipeline Science Report\n\n")
                f.write(f"**Report Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n")
                f.write(f"**Dataset Version:** `{self.version}`\n\n")
                
                f.write("## 1. Execution Summary\n")
                f.write(f"- **Total Files Cataloged:** {stats['total_files']}\n")
                f.write(f"- **Successfully Verified & Archived:** {stats['verified_files']}\n")
                f.write(f"- **Failed / Corrupted:** {stats['failed_files']}\n")
                f.write(f"- **Duplicates Rejected:** {stats['duplicate_files']}\n")
                f.write(f"- **Downloaded Volume:** {stats['downloaded_gb']:.4f} GB\n")
                f.write(f"- **Elapsed Download Execution Time:** {elapsed_time:.2f} seconds\n")
                f.write(f"- **Average Download Speed:** {stats['average_speed_mb_per_sec']:.2f} MB/s\n\n")
                
                f.write("## 2. Scientific Telemetry & Coverage Analysis\n")
                f.write("| Instrument | Count | Start Date | End Date |\n")
                f.write("| --- | --- | --- | --- |\n")
                for row in instrument_stats:
                    f.write(f"| {row[0].upper()} | {row[1]} | {row[2]} | {row[3]} |\n")
                f.write("\n")
                
                f.write("## 3. Duplicate Files Report\n")
                if duplicate_files:
                    f.write("| Filename | Payload | Date | Remarks |\n")
                    f.write("| --- | --- | --- | --- |\n")
                    for row in duplicate_files:
                        f.write(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n")
                else:
                    f.write("No duplicate files detected in this dataset version.\n")
                f.write("\n")
                
                f.write("## 4. Corruption & Ingestion Failure Report\n")
                if corrupted_files:
                    f.write("| Filename | Payload | Date | Failure Reason |\n")
                    f.write("| --- | --- | --- | --- |\n")
                    for row in corrupted_files:
                        f.write(f"| {row[0]} | {row[1]} | {row[2]} | {row[3]} |\n")
                else:
                    f.write("Zero file corruptions or quality validation failures detected. Chain of custody is intact.\n")
                    
            logger.info(f"Science download report generated at {report_path}")
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise

import sqlite3 # Import local sqlite3 reference for connection queries

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SuryaNet Data Ingestion Pipeline orchestrator CLI.")
    parser.add_argument("--config", default="data_pipeline/config.yaml", help="Path to config.yaml file.")
    parser.add_argument("--version", help="Override the dataset version folder name.")
    args = parser.parse_args()
    
    manager = DownloadManager(config_path=args.config, version_override=args.version)
    manager.run()
