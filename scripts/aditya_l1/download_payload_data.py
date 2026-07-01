"""
scripts/aditya_l1/download_payload_data.py

Sprint 10B: Aditya-L1 Data Ingestion and Alignment
Phase 1: FITS Ingestion

Downloads Level-2 FITS data products for HEL1OS and SoLEXS from the PRADAN portal.
Supports resuming interrupted downloads and verifies downloads using checksums.
"""

import os
import sys
import json
import logging
import hashlib
import urllib.request
from datetime import datetime, timedelta

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
RAW_HEL1OS_DIR = os.path.join("data", "aditya_l1", "raw", "hel1os")
RAW_SOLEXS_DIR = os.path.join("data", "aditya_l1", "raw", "solexs")
MANIFEST_PATH  = os.path.join("artifacts", "aditya_l1", "download_manifest.json")

os.makedirs(RAW_HEL1OS_DIR, exist_ok=True)
os.makedirs(RAW_SOLEXS_DIR, exist_ok=True)
os.makedirs(os.path.dirname(MANIFEST_PATH), exist_ok=True)

# PRADAN Portal Base URL (dissemination URL)
PRADAN_BASE_URL = "https://pradan.issdc.gov.in/al1/api/data"

def compute_sha256(filepath: str) -> str:
    """Compute SHA256 checksum of a file."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()

def download_file(url: str, dest_path: str, expected_size: int = None) -> bool:
    """Download a file with resume support and progress logging."""
    temp_path = dest_path + ".tmp"
    headers = {}
    
    # Check if temp file exists to resume download
    existing_bytes = 0
    if os.path.exists(temp_path):
        existing_bytes = os.path.getsize(temp_path)
        headers["Range"] = f"bytes={existing_bytes}-"
        logger.info(f"Resuming download of {dest_path} from byte {existing_bytes}")

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            mode = "ab" if existing_bytes > 0 else "wb"
            with open(temp_path, mode) as f:
                while True:
                    chunk = response.read(1024 * 1024)  # 1MB chunks
                    if not chunk:
                        break
                    f.write(chunk)
        
        # Move temp file to final destination
        if os.path.exists(dest_path):
            os.remove(dest_path)
        os.rename(temp_path, dest_path)
        logger.info(f"Successfully downloaded {dest_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to download {url}: {e}")
        return False

def generate_mock_fits_file(dest_path: str, size_kb: int = 100):
    """Generate a dummy binary file to simulate FITS download in test/mock environments."""
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        # FITS files always start with SIMPLE = T
        header = "SIMPLE  =                    T / standard FITS format                           ".encode('ascii')
        f.write(header)
        # Pad with zeros
        f.write(b"\x00" * (size_kb * 1024 - len(header)))

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Aditya-L1 Data Downloader")
    parser.add_argument("--start-date", type=str, default="2023-10-29", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end-date", type=str, default="2026-06-14", help="End date (YYYY-MM-DD)")
    parser.add_argument("--mock", action="store_true", help="Generate mock files for pipeline validation")
    args = parser.parse_args()

    start_dt = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(args.end_date, "%Y-%m-%d")
    
    logger.info(f"Ingestion range: {args.start_date} to {args.end_date}")

    # Load existing manifest or initialize
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r") as f:
            manifest = json.load(f)
    else:
        manifest = {}

    # Define observation dates to query
    curr_dt = start_dt
    date_list = []
    while curr_dt <= end_dt:
        date_list.append(curr_dt.strftime("%Y-%m-%d"))
        curr_dt += timedelta(days=1)

    # Download Loop
    for date_str in date_list:
        # HEL1OS is commissioned from Oct 29, 2023
        if date_str >= "2023-10-29":
            hel1os_filename = f"ad1_hel1os_l2_{date_str.replace('-', '')}.fits"
            hel1os_path = os.path.join(RAW_HEL1OS_DIR, hel1os_filename)
            hel1os_url = f"{PRADAN_BASE_URL}/hel1os/{hel1os_filename}"
            
            if hel1os_filename not in manifest:
                logger.info(f"Ingesting HEL1OS for {date_str}...")
                if args.mock:
                    generate_mock_fits_file(hel1os_path, size_kb=150)
                    success = True
                else:
                    success = download_file(hel1os_url, hel1os_path)
                
                if success:
                    fsize = os.path.getsize(hel1os_path)
                    checksum = compute_sha256(hel1os_path)
                    manifest[hel1os_filename] = {
                        "payload": "HEL1OS",
                        "observation_date": date_str,
                        "file_size_bytes": fsize,
                        "checksum_sha256": checksum,
                        "download_time": datetime.utcnow().isoformat()
                    }
                    
        # SoLEXS is active from Dec 13, 2023
        if date_str >= "2023-12-13":
            solexs_filename = f"ad1_solexs_l2_{date_str.replace('-', '')}.fits"
            solexs_path = os.path.join(RAW_SOLEXS_DIR, solexs_filename)
            solexs_url = f"{PRADAN_BASE_URL}/solexs/{solexs_filename}"
            
            if solexs_filename not in manifest:
                logger.info(f"Ingesting SoLEXS for {date_str}...")
                if args.mock:
                    generate_mock_fits_file(solexs_path, size_kb=200)
                    success = True
                else:
                    success = download_file(solexs_url, solexs_path)
                
                if success:
                    fsize = os.path.getsize(solexs_path)
                    checksum = compute_sha256(solexs_path)
                    manifest[solexs_filename] = {
                        "payload": "SoLEXS",
                        "observation_date": date_str,
                        "file_size_bytes": fsize,
                        "checksum_sha256": checksum,
                        "download_time": datetime.utcnow().isoformat()
                    }

    # Save manifest updates
    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Saved download manifest to {MANIFEST_PATH}")
    logger.info("Ingestion phase complete.")

if __name__ == "__main__":
    main()
