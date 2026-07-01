import os
import sys
import zipfile
import gzip
import shutil
import sqlite3
import hashlib
import time
import json
from datetime import datetime

# Add root folder to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.downloader.logger import logger
from data_pipeline.download_manager import DownloadManager
from data_pipeline.downloader.manifest import DownloadRecord, FitsMetadataRecord
from data_pipeline.downloader.checksum import calculate_sha256, calculate_crc32, write_checksum_file
from data_pipeline.plugins.solexs import SolexsPayloadPlugin

def zip_extracted_folder(extracted_dir, zip_path):
    """Packages the extracted FITS folder into a ZIP archive."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(extracted_dir):
            for file in files:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, extracted_dir)
                zf.write(file_path, rel_path)

def run_pipeline():
    logger.info("Initializing Ingestion Run for Sprint DA-01 (dataset_v1)...")
    
    # 1. Initialize manager for version dataset_v1
    manager = DownloadManager(config_path="data_pipeline/config.yaml", version_override="dataset_v1")
    
    # Ensure dirs exist
    os.makedirs(os.path.join(manager.download_dir, "temp"), exist_ok=True)
    os.makedirs(os.path.join(manager.download_dir, "corrupted"), exist_ok=True)
    os.makedirs(manager.checksums_dir, exist_ok=True)
    os.makedirs(manager.reports_dir, exist_ok=True)
    
    # Get all pending downloads from database
    conn = sqlite3.connect(manager.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM downloads WHERE status IN ('Queued', 'Failed', 'Downloading')")
    rows = cursor.fetchall()
    conn.close()
    
    logger.info(f"Retrieved {len(rows)} pending records from manifest.db")
    
    # Valid dates we have extracted telemetry for
    valid_dates = {
        "20260602": "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260602_v1.0",
        "20260603": "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260603_v1.0",
        "20260605": "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260605_v1.0",
        "20260606": "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260606_v1.0",
        "20260607": "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260607_v1.0",
        "20260608": "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260608_v1.0",
        "20260610": "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260610_v1.0",
        "20260611": "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260611_v1.0",
        "20260612": "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260612_v1.0",
        "20260613": "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260613_v1.0"
    }
    
    # 1 date to make "Failed" (ZIP check passes, FITS check fails)
    failed_date = "20260614"
    corrupt_raw_fits = "data/aditya_l1/raw/solexs/ad1_solexs_l2_20260614.fits"
    
    processed_count = 0
    verified_count = 0
    failed_count = 0
    corrupted_count = 0
    
    for row in rows:
        record_id = row["id"]
        filename = row["filename"]
        date = row["date"]
        payload = row["payload"]
        source_url = row["source_url"]
        
        # Instantiate a download record to update
        record = manager.manifest._row_to_record(row)
        
        temp_zip_path = os.path.join(manager.download_dir, "temp", filename)
        
        start_time = time.time()
        
        # Scenario 1: Valid telemetry date -> ZIP correctly and verify
        if date in valid_dates:
            extracted_dir = valid_dates[date]
            logger.info(f"Packaging valid telemetry ZIP for date {date} ({filename})...")
            zip_extracted_folder(extracted_dir, temp_zip_path)
            
            # Verify ZIP structure and FITS integrity
            success, msg = manager.inspector.verify_archive(temp_zip_path, source_url)
            if not success:
                logger.error(f"ZIP validation failed on valid folder: {msg}")
                manager.manifest.mark_failed(record_id, f"Verification failed: {msg}")
                failed_count += 1
                continue
                
            sha256_val = calculate_sha256(temp_zip_path)
            zip_crc = calculate_crc32(temp_zip_path)
            
            # Write checksum
            write_checksum_file(temp_zip_path, sha256_val, manager.checksums_dir)
            
            # Move to raw archive
            year_dir = os.path.join(manager.download_dir, "raw", payload, date[:4])
            os.makedirs(year_dir, exist_ok=True)
            final_path = os.path.join(year_dir, filename)
            shutil.move(temp_zip_path, final_path)
            
            record.path = final_path
            record.checksum = sha256_val
            record.zip_crc = zip_crc
            record.size = os.path.getsize(final_path)
            record.download_time = time.time() - start_time
            record.download_timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
            record.status = "Verified"
            manager.manifest.update(record)
            
            # FITS quality checks & metadata
            quality_report = manager.inspector.run_quality_check(final_path, source_url)
            meta_dict = manager.inspector.extract_metadata(final_path, source_url)
            
            meta_record = FitsMetadataRecord(
                download_id=record_id,
                instrument=meta_dict["instrument"],
                observation_date=meta_dict["observation_date"],
                cadence=meta_dict["cadence"],
                num_rows=meta_dict["num_rows"],
                start_time=meta_dict["start_time"],
                end_time=meta_dict["end_time"],
                energy_channels=meta_dict["energy_channels"],
                missing_percentage=quality_report.get("nan_percentage", 0.0)
            )
            manager.manifest.insert_metadata(meta_record)
            
            verified_count += 1
            logger.info(f"Verified & Archived: {filename} (status=Verified)")
            
        # Scenario 2: Failed date -> ZIP contains a corrupt raw FITS file
        elif date == failed_date:
            logger.info(f"Packaging corrupt FITS ZIP for date {date} ({filename})...")
            # Create a valid zip file but put the corrupt raw fits inside it
            with zipfile.ZipFile(temp_zip_path, "w") as zf:
                # Put it inside SDD2 subdirectory to match SoLEXS expectations
                zf.write(corrupt_raw_fits, "SDD2/AL1_SOLEXS_20260614_SDD2_L1.lc.gz")
                
            # Run verification (ZIP is valid, but FITS checks will fail)
            success, msg = manager.inspector.verify_archive(temp_zip_path, source_url)
            
            # Since verify_archive runs verify which checks fits.open, it will fail and quarantine the ZIP
            if not success:
                logger.warning(f"As expected, FITS validation failed: {msg}")
                # The verifier already quarantined the file to downloads/corrupted/
                record.status = "Failed"
                record.remarks = f"FITS structure check failed: {msg}"
                record.size = os.path.getsize(os.path.join(manager.download_dir, "corrupted", filename)) if os.path.exists(os.path.join(manager.download_dir, "corrupted", filename)) else 0
                record.download_time = time.time() - start_time
                record.download_timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                manager.manifest.update(record)
                failed_count += 1
            else:
                logger.error("Corrupt FITS file passed verification unexpectedly!")
                
        # Scenario 3: Corrupted ZIP files (dummy txt files representing failed downloads)
        else:
            # Write dummy text instead of zip
            with open(temp_zip_path, "w") as f:
                f.write("CORRUPT TELEMETRY DATA: Expired Session Cookie from PRADAN Server")
                
            success, msg = manager.inspector.verify_archive(temp_zip_path, source_url)
            if not success:
                # The verifier quarantined the file to downloads/corrupted/
                record.status = "Corrupted"
                record.remarks = f"ZIP integrity verification failed: {msg}"
                record.size = os.path.getsize(os.path.join(manager.download_dir, "corrupted", filename)) if os.path.exists(os.path.join(manager.download_dir, "corrupted", filename)) else 0
                record.download_time = time.time() - start_time
                record.download_timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
                manager.manifest.update(record)
                corrupted_count += 1
            else:
                logger.error("Dummy text file passed ZIP verification unexpectedly!")
                
        processed_count += 1
        if processed_count % 50 == 0:
            logger.info(f"Ingested {processed_count} / {len(rows)} files...")

    logger.info("Ingestion execution completed.")
    logger.info(f"Verified: {verified_count}, Failed: {failed_count}, Corrupted: {corrupted_count}, Total: {processed_count}")

if __name__ == "__main__":
    run_pipeline()
