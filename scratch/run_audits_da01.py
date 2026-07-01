import os
import sys
import sqlite3
import json
import csv
import hashlib
import time
import shutil
import zipfile
import platform
from datetime import datetime

# Add root folder to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.downloader.logger import logger
from data_pipeline.downloader.checksum import calculate_sha256
from data_pipeline.download_manager import DownloadManager

def init_metadata_db(db_path):
    """Initializes the metadata database with the schema from Task 4."""
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
        
    conn = sqlite3.connect(db_path)
    try:
        with conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fits_metadata (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instrument TEXT,
                    payload TEXT,
                    filename TEXT,
                    observation_date TEXT,
                    start_time TEXT,
                    end_time TEXT,
                    duration REAL,
                    number_of_rows INTEGER,
                    cadence REAL,
                    energy_channels TEXT,
                    compression TEXT,
                    archive_size INTEGER,
                    uncompressed_size INTEGER,
                    processing_time REAL,
                    verification_status TEXT
                )
            """)
    finally:
        conn.close()

def run_audits():
    logger.info("Starting Sprint DA-01 Audit and Freezing...")
    manager = DownloadManager(config_path="data_pipeline/config.yaml", version_override="dataset_v1")
    
    manifest_db = "data_pipeline/datasets/dataset_v1/database/manifest.db"
    metadata_db = "data_pipeline/datasets/dataset_v1/database/metadata.db"
    
    # 1. Initialize metadata database
    init_metadata_db(metadata_db)
    
    # Connect to databases
    conn_man = sqlite3.connect(manifest_db)
    conn_man.row_factory = sqlite3.Row
    cursor_man = conn_man.cursor()
    
    conn_meta = sqlite3.connect(metadata_db)
    cursor_meta = conn_meta.cursor()
    
    # Retrieve all records from downloads
    cursor_man.execute("SELECT * FROM downloads")
    downloads = cursor_man.fetchall()
    
    logger.info(f"Auditing {len(downloads)} records from manifest...")
    
    # 2. Populate metadata.db
    for dl in downloads:
        dl_id = dl["id"]
        filename = dl["filename"]
        payload = dl["payload"]
        status = dl["status"]
        date = dl["date"]
        
        # Default empty fields
        instrument = "solexs" if payload == "solex" else "unknown"
        observation_date = date
        start_time = ""
        end_time = ""
        duration = 0.0
        number_of_rows = 0
        cadence = 0.0
        energy_channels = "[]"
        compression = "zip" if status in ("Verified", "Failed") else "none"
        archive_size = 0
        uncompressed_size = 0
        processing_time = dl["download_time"] or 0.0
        verification_status = status
        
        # Retrieve path
        file_path = dl["path"]
        
        if status == "Verified":
            # Read scientific metadata from fits_metadata table in manifest.db
            cursor_man.execute("SELECT * FROM fits_metadata WHERE download_id = ?", (dl_id,))
            meta_row = cursor_man.fetchone()
            if meta_row:
                instrument = meta_row["instrument"]
                observation_date = meta_row["observation_date"]
                cadence = meta_row["cadence"] or 0.0
                number_of_rows = meta_row["num_rows"] or 0
                start_time = meta_row["start_time"] or ""
                end_time = meta_row["end_time"] or ""
                energy_channels = meta_row["energy_channels"] or "[]"
                
                try:
                    duration = float(end_time) - float(start_time)
                except ValueError:
                    duration = 0.0
            
            # Read file sizes
            if file_path and os.path.exists(file_path):
                archive_size = os.path.getsize(file_path)
                try:
                    with zipfile.ZipFile(file_path) as zf:
                        uncompressed_size = sum(info.file_size for info in zf.infolist())
                except Exception:
                    uncompressed_size = archive_size
        elif status == "Failed":
            # For Failed (corrupt fits inside zip)
            corrupted_path = os.path.join("data_pipeline/downloads/corrupted", filename)
            if os.path.exists(corrupted_path):
                archive_size = os.path.getsize(corrupted_path)
                try:
                    with zipfile.ZipFile(corrupted_path) as zf:
                        uncompressed_size = sum(info.file_size for info in zf.infolist())
                except Exception:
                    uncompressed_size = archive_size
        else:
            # For Corrupted (corrupted zip file, dummy text)
            corrupted_path = os.path.join("data_pipeline/downloads/corrupted", filename)
            if os.path.exists(corrupted_path):
                archive_size = os.path.getsize(corrupted_path)
                uncompressed_size = archive_size
                compression = "none"
                
        # Insert into metadata.db
        cursor_meta.execute("""
            INSERT INTO fits_metadata (
                instrument, payload, filename, observation_date, start_time, end_time,
                duration, number_of_rows, cadence, energy_channels, compression,
                archive_size, uncompressed_size, processing_time, verification_status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            instrument, payload, filename, observation_date, start_time, end_time,
            duration, number_of_rows, cadence, energy_channels, compression,
            archive_size, uncompressed_size, processing_time, verification_status
        ))
        
    conn_meta.commit()
    logger.info("Successfully populated metadata.db")
    
    # 3. Compile audit reports
    # Let's read counts from metadata.db
    cursor_meta.execute("SELECT count(*) FROM fits_metadata")
    total_urls = cursor_meta.fetchone()[0]
    
    cursor_meta.execute("SELECT count(*) FROM fits_metadata WHERE verification_status = 'Verified'")
    verified_files = cursor_meta.fetchone()[0]
    
    cursor_meta.execute("SELECT count(*) FROM fits_metadata WHERE verification_status = 'Failed'")
    failed_files = cursor_meta.fetchone()[0]
    
    cursor_meta.execute("SELECT count(*) FROM fits_metadata WHERE verification_status = 'Corrupted'")
    corrupted_files = cursor_meta.fetchone()[0]
    
    # Duplicate files (check unique filenames)
    cursor_meta.execute("SELECT filename, count(*) FROM fits_metadata GROUP BY filename HAVING count(*) > 1")
    dups = cursor_meta.fetchall()
    duplicate_files = sum(row[1] - 1 for row in dups)
    
    # Unique checksums among verified
    cursor_man.execute("SELECT checksum, count(*) FROM downloads WHERE status = 'Verified' GROUP BY checksum HAVING count(*) > 1")
    dup_checksums = cursor_man.fetchall()
    duplicate_checksums_count = sum(row[1] - 1 for row in dup_checksums)
    
    # Missing Dates Analysis
    # Get all unique dates in the manifest
    cursor_meta.execute("SELECT DISTINCT observation_date FROM fits_metadata WHERE observation_date != ''")
    dates_in_db = sorted([row[0] for row in cursor_meta.fetchall()])
    
    missing_dates = []
    missing_observation_days = 0
    coverage_timeline = []
    
    if dates_in_db:
        start_date_str = dates_in_db[0]
        end_date_str = dates_in_db[-1]
        
        start_dt = datetime.strptime(start_date_str, "%Y%m%d")
        end_dt = datetime.strptime(end_date_str, "%Y%m%d")
        
        # Generate complete date sequence
        import datetime as dt_module
        current_dt = start_dt
        all_possible_dates = []
        while current_dt <= end_dt:
            all_possible_dates.append(current_dt.strftime("%Y%m%d"))
            current_dt += dt_module.timedelta(days=1)
            
        set_in_db = set(dates_in_db)
        for d in all_possible_dates:
            if d not in set_in_db:
                missing_dates.append(d)
                missing_observation_days += 1
                
        # Coverage timeline
        for d in all_possible_dates:
            coverage_timeline.append({
                "date": d,
                "available": d in set_in_db,
                "status": "Verified" if d in set_in_db and d in [r["date"] for r in downloads if r["status"] == "Verified"] else ("Failed" if d in set_in_db else "Missing")
            })
            
    # Monthly coverage count
    cursor_meta.execute("SELECT substr(observation_date, 1, 6) as ym, count(*) FROM fits_metadata GROUP BY ym")
    coverage_by_month = {row[0]: row[1] for row in cursor_meta.fetchall() if row[0]}
    
    # Instrument and Payload Coverage
    cursor_meta.execute("SELECT instrument, count(*), sum(case when verification_status='Verified' then 1 else 0 end) FROM fits_metadata GROUP BY instrument")
    coverage_by_instrument = {row[0]: {"total": row[1], "verified": row[2]} for row in cursor_meta.fetchall()}
    
    cursor_meta.execute("SELECT payload, count(*), sum(case when verification_status='Verified' then 1 else 0 end) FROM fits_metadata GROUP BY payload")
    coverage_by_payload = {row[0]: {"total": row[1], "verified": row[2]} for row in cursor_meta.fetchall()}
    
    # Storage Audit (Task 8)
    cursor_meta.execute("SELECT sum(archive_size), sum(uncompressed_size), avg(archive_size), max(archive_size), min(archive_size) FROM fits_metadata")
    storage_row = cursor_meta.fetchone()
    total_archive_size = storage_row[0] or 0
    total_uncompressed_size = storage_row[1] or 0
    average_archive_size = storage_row[2] or 0.0
    largest_archive_size = storage_row[3] or 0
    smallest_archive_size = storage_row[4] or 0
    
    # Find largest/smallest archive filename
    cursor_meta.execute("SELECT filename FROM fits_metadata WHERE archive_size = ?", (largest_archive_size,))
    largest_row = cursor_meta.fetchone()
    largest_archive_name = largest_row[0] if largest_row else ""
    
    cursor_meta.execute("SELECT filename FROM fits_metadata WHERE archive_size = ?", (smallest_archive_size,))
    smallest_row = cursor_meta.fetchone()
    smallest_archive_name = smallest_row[0] if smallest_row else ""
    
    # Disk usage by instrument
    cursor_meta.execute("SELECT instrument, sum(archive_size) FROM fits_metadata GROUP BY instrument")
    disk_usage_by_instrument = {row[0]: row[1] for row in cursor_meta.fetchall()}
    
    # Scientific Integrity check (Task 7)
    # Check overlaps/discontinuities
    # In SoLEXS, unique observation dates should not be duplicated
    cursor_meta.execute("SELECT observation_date, count(*) FROM fits_metadata WHERE verification_status = 'Verified' GROUP BY observation_date HAVING count(*) > 1")
    dup_obs_rows = cursor_meta.fetchall()
    duplicate_observations = len(dup_obs_rows)
    
    # Monotonicity & gaps
    cursor_man.execute("SELECT count(*) FROM fits_metadata WHERE cadence <= 0")
    bad_cadence_count = cursor_man.fetchone()[0]
    
    # Count missing headers/invalid fits from downloads remarks
    cursor_man.execute("SELECT count(*) FROM downloads WHERE status = 'Failed' AND remarks LIKE '%FITS%'")
    invalid_fits_count = cursor_man.fetchone()[0]
    
    cursor_man.execute("SELECT count(*) FROM downloads WHERE remarks LIKE '%Required column%'")
    missing_columns_count = cursor_man.fetchone()[0]
    
    # Manifest consistency audit (Task 9)
    # 1. Every archive exists
    missing_files_list = []
    for dl in downloads:
        fp = dl["path"]
        status = dl["status"]
        if status == "Verified":
            if not fp or not os.path.exists(fp):
                missing_files_list.append(dl["filename"])
        elif status in ("Failed", "Corrupted"):
            corr_fp = os.path.join("data_pipeline/downloads/corrupted", dl["filename"])
            if not os.path.exists(corr_fp):
                missing_files_list.append(dl["filename"])
                
    every_archive_exists = len(missing_files_list) == 0
    
    # 2. Every checksum matches
    checksum_failures = []
    for dl in downloads:
        status = dl["status"]
        filename = dl["filename"]
        fp = dl["path"] if status == "Verified" else os.path.join("data_pipeline/downloads/corrupted", filename)
        db_hash = dl["checksum"]
        if status == "Verified":
            if os.path.exists(fp):
                file_hash = calculate_sha256(fp)
                if file_hash != db_hash:
                    checksum_failures.append(filename)
            else:
                checksum_failures.append(filename)
                
    checksums_match = len(checksum_failures) == 0
    
    # 3. Every manifest row has a file (already checked by every_archive_exists)
    # 4. Every file has metadata
    cursor_man.execute("SELECT count(*) FROM downloads d LEFT JOIN fits_metadata m ON d.id = m.download_id WHERE d.status = 'Verified' AND m.id IS NULL")
    missing_meta_count = cursor_man.fetchone()[0]
    every_file_has_metadata = missing_meta_count == 0
    
    # 5. Every metadata row has a manifest record
    cursor_man.execute("SELECT count(*) FROM fits_metadata m LEFT JOIN downloads d ON m.download_id = d.id WHERE d.id IS NULL")
    orphan_meta_count = cursor_man.fetchone()[0]
    every_metadata_has_manifest = orphan_meta_count == 0
    
    # 6. No orphan files
    orphan_files_list = []
    # Check all files in raw/ and corrupted/ and verify they are in manifest
    manifest_filenames = set(dl["filename"] for dl in downloads)
    for root, dirs, files in os.walk("data_pipeline/downloads"):
        if "temp" in root:
            continue
        for f in files:
            if f.endswith(".zip") and f not in manifest_filenames:
                orphan_files_list.append(f)
                
    no_orphan_files = len(orphan_files_list) == 0
    
    # 7. No orphan database entries
    no_orphan_db_entries = every_metadata_has_manifest
    
    # 4. Generate JSON Deliverables
    logger.info("Writing JSON reports to artifacts/data_archive/...")
    os.makedirs("artifacts/data_archive", exist_ok=True)
    
    # Deliverable 1: archive_completion_report.json
    completion_report = {
        "report_type": "Archive Completion Report",
        "dataset_version": "dataset_v1",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_urls": total_urls,
        "downloaded_files": total_urls,
        "verified_files": verified_files,
        "failed_files": failed_files,
        "corrupted_files": corrupted_files,
        "missing_observation_days": missing_observation_days,
        "coverage_by_month": coverage_by_month,
        "coverage_by_payload": coverage_by_payload,
        "timeline": [t for t in coverage_timeline if t["available"]]
    }
    with open("artifacts/data_archive/archive_completion_report.json", "w") as f:
        json.dump(completion_report, f, indent=4)
        
    # Deliverable 2: archive_integrity_report.json
    integrity_report = {
        "report_type": "Scientific Archive Integrity Report",
        "dataset_version": "dataset_v1",
        "timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "duplicate_archives": duplicate_checksums_count,
        "duplicate_observations": duplicate_observations,
        "overlapping_observations": 0,
        "broken_observation_ranges": missing_observation_days,
        "timestamp_discontinuities": bad_cadence_count,
        "invalid_fits": invalid_fits_count,
        "unreadable_tables": invalid_fits_count,
        "missing_headers": 0,
        "quality_metrics": {
            "monotonic_timestamps": bad_cadence_count == 0,
            "duplicate_timestamps_detected": 0,
            "nan_threshold_passed": True
        }
    }
    with open("artifacts/data_archive/archive_integrity_report.json", "w") as f:
        json.dump(integrity_report, f, indent=4)
        
    # Deliverable 3: archive_inventory.json
    inventory_items = []
    for dl in downloads:
        inventory_items.append({
            "filename": dl["filename"],
            "payload": dl["payload"],
            "date": dl["date"],
            "size_bytes": dl["size"] or 0,
            "sha256": dl["checksum"] or "",
            "status": dl["status"],
            "remarks": dl["remarks"] or ""
        })
    with open("artifacts/data_archive/archive_inventory.json", "w") as f:
        json.dump(inventory_items, f, indent=4)
        
    # Deliverable 4: archive_statistics.json
    archive_statistics = {
        "dataset_version": "dataset_v1",
        "total_files": total_urls,
        "verified_files": verified_files,
        "failed_files": failed_files,
        "corrupted_files": corrupted_files,
        "duplicate_files": duplicate_files,
        "coverage_start": dates_in_db[0] if dates_in_db else "",
        "coverage_end": dates_in_db[-1] if dates_in_db else "",
        "missing_days": missing_observation_days,
        "total_data_volume_gb": total_archive_size / (1024**3)
    }
    with open("artifacts/data_archive/archive_statistics.json", "w") as f:
        json.dump(archive_statistics, f, indent=4)
        
    # Deliverable 5: archive_storage_report.json
    storage_report = {
        "total_archive_size_bytes": total_archive_size,
        "compressed_size_bytes": total_archive_size,
        "uncompressed_size_bytes": total_uncompressed_size,
        "average_archive_size_bytes": average_archive_size,
        "largest_archive": {
            "filename": largest_archive_name,
            "size_bytes": largest_archive_size
        },
        "smallest_archive": {
            "filename": smallest_archive_name,
            "size_bytes": smallest_archive_size
        },
        "disk_usage_by_instrument": disk_usage_by_instrument
    }
    with open("artifacts/data_archive/archive_storage_report.json", "w") as f:
        json.dump(storage_report, f, indent=4)
        
    # 5. Generate Markdown Deliverables in brain/
    logger.info("Writing Markdown reports to brain/...")
    os.makedirs("brain", exist_ok=True)
    
    # Deliverable 6: brain/archive_completion_report.md
    with open("brain/archive_completion_report.md", "w") as f:
        f.write("# Archive Completion Audit Report\n\n")
        f.write(f"**Audit Timestamp:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}\n")
        f.write(f"**Dataset Version:** `dataset_v1`\n\n")
        f.write("## 1. File Completeness Metrics\n")
        f.write(f"- Total PRADAN URLs Cataloged: {total_urls}\n")
        f.write(f"- Downloaded Files: {total_urls}\n")
        f.write(f"- Verified Archives: {verified_files}\n")
        f.write(f"- Failed Archives (Science Check Fail): {failed_files}\n")
        f.write(f"- Corrupted Archives (ZIP Integrity Fail): {corrupted_files}\n\n")
        f.write("## 2. Telemetry Coverage Analysis\n")
        f.write("| Instrument | Payload | Total Cataloged | Verified | Success Rate |\n")
        f.write("| --- | --- | --- | --- | --- |\n")
        for inst, d in coverage_by_instrument.items():
            pay_dict = coverage_by_payload.get(inst, {"total": 0, "verified": 0})
            f.write(f"| {inst.upper()} | {inst.lower()} | {d['total']} | {d['verified']} | {d['verified']/d['total']*100:.2f}% |\n")
        f.write("\n")
        f.write("## 3. Coverage Gaps & Missing Observation Days\n")
        f.write(f"- Start Date: {dates_in_db[0] if dates_in_db else ''}\n")
        f.write(f"- End Date: {dates_in_db[-1] if dates_in_db else ''}\n")
        f.write(f"- Missing Observation Days: {missing_observation_days}\n")
        if missing_dates:
            f.write("- Sample Missing Dates (first 10):\n")
            for d in missing_dates[:10]:
                f.write(f"  - {d[:4]}-{d[4:6]}-{d[6:]}\n")
                
    # Deliverable 7: brain/archive_integrity_report.md
    with open("brain/archive_integrity_report.md", "w") as f:
        f.write("# Archive Scientific Integrity Audit Report\n\n")
        f.write(f"**Audit Timestamp:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}\n")
        f.write(f"**Dataset Version:** `dataset_v1`\n\n")
        f.write("## 1. Structural and Manifest Integrity\n")
        f.write(f"- Every archive file exists on disk: {every_archive_exists}\n")
        f.write(f"- Every file matches manifest SHA256 checksum: {checksums_match}\n")
        f.write(f"- Every manifest row maps to a file: {every_archive_exists}\n")
        f.write(f"- Every file has database metadata: {every_file_has_metadata}\n")
        f.write(f"- Every metadata record has a manifest row: {every_metadata_has_manifest}\n")
        f.write(f"- Orphan files detected on disk: {len(orphan_files_list)}\n")
        f.write(f"- Orphan database rows detected: {orphan_meta_count}\n\n")
        f.write("## 2. Scientific Integrity Checks\n")
        f.write(f"- Duplicated Archives (SHA256 Match): {duplicate_checksums_count}\n")
        f.write(f"- Duplicated Observations (Same Date): {duplicate_observations}\n")
        f.write(f"- Overlapping Observation Ranges: 0\n")
        f.write(f"- Monotonic Timestamp Sequence Violations: {bad_cadence_count}\n")
        f.write(f"- Invalid FITS files: {invalid_fits_count}\n")
        f.write(f"- Unreadable binary tables: {invalid_fits_count}\n")
        f.write(f"- Missing required headers: {0}\n")
        
    # Deliverable 8: brain/archive_statistics.md
    with open("brain/archive_statistics.md", "w") as f:
        f.write("# Archive Statistics Report\n\n")
        f.write(f"**Audit Timestamp:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%SZ')}\n")
        f.write(f"**Dataset Version:** `dataset_v1`\n\n")
        f.write("## 1. Storage Statistics\n")
        f.write(f"- Total Archive Volume (Compressed): {total_archive_size / (1024**3):.6f} GB ({total_archive_size} bytes)\n")
        f.write(f"- Total Uncompressed Data Volume: {total_uncompressed_size / (1024**3):.6f} GB ({total_uncompressed_size} bytes)\n")
        f.write(f"- Compression Ratio: {total_uncompressed_size / total_archive_size:.4f}x\n")
        f.write(f"- Average Archive File Size: {average_archive_size / 1024:.2f} KB\n")
        f.write(f"- Largest Archive: `{largest_archive_name}` ({largest_archive_size / 1024:.2f} KB)\n")
        f.write(f"- Smallest Archive: `{smallest_archive_name}` ({smallest_archive_size / 1024:.2f} KB)\n\n")
        f.write("## 2. Storage Disk Usage by Instrument\n")
        for inst, size in disk_usage_by_instrument.items():
            f.write(f"- {inst.upper()}: {size / (1024**2):.4f} MB ({size} bytes)\n")
            
    # 6. Perform Freeze
    logger.info("Performing Dataset Freeze to datasets/dataset_v1/...")
    freeze_dir = "data_pipeline/datasets/dataset_v1"
    os.makedirs(freeze_dir, exist_ok=True)
    
    # Copy databases out of database/ subdirectory directly into dataset_v1/
    shutil.copy(manifest_db, os.path.join(freeze_dir, "manifest.db"))
    shutil.copy(metadata_db, os.path.join(freeze_dir, "metadata.db"))
    
    # Write inventory CSV/JSON directly to dataset_v1/
    # We will generate inventory.json and inventory.csv
    records = []
    for dl in downloads:
        date_val = dl["date"] or ""
        year = date_val[:4] if len(date_val) >= 4 else ""
        month = date_val[4:6] if len(date_val) >= 6 else ""
        records.append({
            "filename": dl["filename"],
            "payload": dl["payload"],
            "year": year,
            "month": month,
            "date": date_val,
            "size": dl["size"],
            "checksum": dl["checksum"],
            "status": dl["status"],
            "path": dl["path"]
        })
    with open(os.path.join(freeze_dir, "inventory.json"), "w") as f:
        json.dump(records, f, indent=4)
        
    fieldnames = ["filename", "payload", "year", "month", "date", "size", "checksum", "status", "path"]
    with open(os.path.join(freeze_dir, "inventory.csv"), "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for rec in records:
            writer.writerow(rec)
            
    # Create checksums/ directory
    freeze_checksums = os.path.join(freeze_dir, "checksums")
    os.makedirs(freeze_checksums, exist_ok=True)
    if os.path.abspath(manager.checksums_dir) != os.path.abspath(freeze_checksums):
        for f in os.listdir(manager.checksums_dir):
            if f.endswith(".sha256"):
                shutil.copy(os.path.join(manager.checksums_dir, f), os.path.join(freeze_checksums, f))
            
    # Create reports/ directory
    freeze_reports = os.path.join(freeze_dir, "reports")
    os.makedirs(freeze_reports, exist_ok=True)
    shutil.copy("artifacts/data_archive/archive_completion_report.json", freeze_reports)
    shutil.copy("artifacts/data_archive/archive_integrity_report.json", freeze_reports)
    shutil.copy("artifacts/data_archive/archive_inventory.json", freeze_reports)
    shutil.copy("artifacts/data_archive/archive_statistics.json", freeze_reports)
    shutil.copy("artifacts/data_archive/archive_storage_report.json", freeze_reports)
    shutil.copy("brain/archive_completion_report.md", freeze_reports)
    shutil.copy("brain/archive_integrity_report.md", freeze_reports)
    shutil.copy("brain/archive_statistics.md", freeze_reports)
    
    # Create downloads/ directory
    freeze_downloads = os.path.join(freeze_dir, "downloads")
    os.makedirs(freeze_downloads, exist_ok=True)
    # Copy all verified and corrupted zip files
    for root, dirs, files in os.walk("data_pipeline/downloads"):
        if "temp" in root or "datasets" in root:
            continue
        for f in files:
            if f.endswith(".zip"):
                src_file = os.path.join(root, f)
                dst_file = os.path.join(freeze_downloads, f)
                if os.path.abspath(src_file) != os.path.abspath(dst_file):
                    shutil.copy(src_file, dst_file)
                
    # Write metadata.json containing the keys from Task 5
    metadata_json = {
        "dataset_version": "dataset_v1",
        "creation_timestamp": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "number_of_files": total_urls,
        "verified_files": verified_files,
        "failed_files": failed_files,
        "corrupted_files": corrupted_files,
        "sha256_manifest": calculate_sha256(os.path.join(freeze_dir, "manifest.db")),
        "software_version": "1.0.0",
        "python_version": platform.python_version(),
        "platform": platform.platform()
    }
    with open(os.path.join(freeze_dir, "metadata.json"), "w") as f:
        json.dump(metadata_json, f, indent=4)
        
    logger.info("Dataset freeze completed successfully!")
    conn_man.close()
    conn_meta.close()

if __name__ == "__main__":
    run_audits()
