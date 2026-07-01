import os
import sys
import zipfile
import gzip
import shutil
import sqlite3

# Add root folder to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from data_pipeline.downloader.logger import logger
from data_pipeline.download_manager import DownloadManager
from data_pipeline.downloader.manifest import DownloadRecord

def create_mock_download():
    logger.info("Setting up mock downloaded zip file...")
    temp_dir = "data_pipeline/downloads/temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    source_fits = "data/aditya_l1/raw_extracted/solexs/AL1_SLX_L1_20260610_v1.0/SDD2/AL1_SOLEXS_20260610_SDD2_L1.lc.gz"
    if not os.path.exists(source_fits):
        raise FileNotFoundError(f"Source FITS file not found for testing: {source_fits}")
        
    # Zip the gzip file directly
    zip_path = "data_pipeline/downloads/temp/AL1_SLX_L1_20231213_v1.0.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(source_fits, "SDD2/AL1_SOLEXS_20231213_SDD2_L1.lc.gz")
        
    logger.info(f"Created mock ZIP archive at: {zip_path}")
    return zip_path

def run_test():
    # 1. Setup mock ZIP archive
    zip_path = create_mock_download()
    
    # 2. Initialize manager
    manager = DownloadManager(config_path="data_pipeline/config.yaml", version_override="test_dataset")
    
    # 3. Insert download record as Downloaded (to bypass http request)
    logger.info("Inserting record into test manifest database...")
    record = DownloadRecord(
        source_url="/al1/protected/downloadData/solexs/level1/2023/12/N00_0000/AL1_SLX_L1_20231213_v1.0.zip?solexs",
        filename="AL1_SLX_L1_20231213_v1.0.zip",
        payload="solex",
        date="20231213",
        status="Downloaded",
        size=os.path.getsize(zip_path)
    )
    
    # Insert record and get ID
    record_id = manager.manifest.insert(record)
    record.id = record_id
    
    # 4. Run the file processing pipeline (verify, checksum, archive, quality checks, metadata index)
    logger.info(f"Running manager.process_file for record ID {record_id}...")
    
    # Mock download to return our local valid mock ZIP path instead of calling server
    manager.downloader.download = lambda rec, prog=None, t_id=None: zip_path
    
    success = manager.process_file(record)
    
    if success:
        logger.info("Pipeline processing completed successfully!")
        
        # Verify database update
        conn = sqlite3.connect(manager.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT * FROM downloads WHERE id = ?", (record_id,))
            row = cursor.fetchone()
            logger.info(f"Manifest Record: Status={row['status']}, Path={row['path']}, Checksum={row['checksum']}")
            
            cursor = conn.execute("SELECT * FROM fits_metadata WHERE download_id = ?", (record_id,))
            meta = cursor.fetchone()
            if meta:
                logger.info(f"FITS Metadata: Instrument={meta['instrument']}, Date={meta['observation_date']}, Rows={meta['num_rows']}, Cadence={meta['cadence']}s, Channels={meta['energy_channels']}")
            else:
                logger.error("No FITS metadata was indexed!")
        finally:
            conn.close()
            
        # Generate reports
        logger.info("Generating report...")
        manager.generate_reports()
        
        report_file = os.path.join(manager.reports_dir, "download_report.md")
        if os.path.exists(report_file):
            logger.info(f"Generated report content:\n" + "-"*40)
            with open(report_file, "r") as f:
                print(f.read())
            logger.info("-"*40)
    else:
        logger.error("Pipeline processing failed!")

if __name__ == "__main__":
    run_test()
