import os
import re
import yaml
import argparse
from typing import Dict, Any, List
from data_pipeline.downloader.logger import logger
from data_pipeline.downloader.manifest import DownloadManifest, DownloadRecord

def parse_pradan_script(script_path: str) -> Dict[str, Any]:
    """Parses a PRADAN bash downloader script using regex to extract cookies, base URL, and data file paths."""
    if not os.path.exists(script_path):
        raise FileNotFoundError(f"PRADAN script not found at: {script_path}")
        
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()
        
    # Extract cookies
    cookie_match = re.search(r'cookies=["\'](.*?)["\']', content)
    if not cookie_match:
        raise ValueError("Could not find 'cookies' variable definition in the script.")
    cookies = cookie_match.group(1)
    
    # Extract urlPrefix
    url_prefix_match = re.search(r'urlPrefix=["\'](.*?)["\']', content)
    if not url_prefix_match:
        raise ValueError("Could not find 'urlPrefix' variable definition in the script.")
    base_url = url_prefix_match.group(1)
    
    # Extract dataFilePaths
    data_paths_match = re.search(r'dataFilePaths=\((.*?)\)', content, re.DOTALL)
    if not data_paths_match:
        raise ValueError("Could not find 'dataFilePaths' array definition in the script.")
    
    raw_paths_block = data_paths_match.group(1)
    # Match double-quoted or single-quoted strings inside the array block
    urls = re.findall(r'["\'](.*?)["\']', raw_paths_block)
    
    return {
        "cookie": cookies,
        "base_url": base_url,
        "urls": urls
    }

def update_config(config_path: str, cookie: str, base_url: str):
    """Updates the cookie and base_url parameters inside the config.yaml file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Config file not found at: {config_path}")
        
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    config["cookie"] = cookie
    config["base_url"] = base_url
    
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(config, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Successfully updated cookies and base_url in {config_path}")

def parse_url_metadata(url_path: str) -> Dict[str, str]:
    """Parses filename, payload instrument, and observation date from the PRADAN URL path."""
    filename = url_path.split('/')[-1].split('?')[0]
    
    # Default fallbacks
    payload = "unknown"
    date_str = ""
    
    # Identify payload/instrument
    if "solexs" in url_path.lower() or "slx" in filename.lower():
        payload = "solex"
    elif "hel1os" in url_path.lower() or "h1" in filename.lower():
        payload = "hel1os"
    elif "goes" in url_path.lower():
        payload = "goes"
    elif "noaa" in url_path.lower() or "swpc" in url_path.lower():
        payload = "noaa"
    elif "sdo" in url_path.lower() or "jsoc" in url_path.lower():
        payload = "sdo"
        
    # Extract date (e.g. 20260615 from AL1_SLX_L1_20260615_v1.0.zip)
    date_match = re.search(r'\d{8}', filename)
    if date_match:
        date_str = date_match.group(0)
    else:
        # Fallback to path parsing (e.g., /2026/06/)
        path_parts = url_path.split('/')
        for i, part in enumerate(path_parts):
            if part.isdigit() and len(part) == 4:
                # If year found, check next part for month
                year = part
                month = "01"
                if i + 1 < len(path_parts) and path_parts[i+1].isdigit() and len(path_parts[i+1]) == 2:
                    month = path_parts[i+1]
                date_str = f"{year}{month}01"
                break
                
    return {
        "filename": filename,
        "payload": payload,
        "date": date_str
    }

def migrate(script_path: str, config_path: str, dataset_version: str = None):
    """Executes the migration process from bash script to SQLite manifest."""
    logger.info(f"Starting migration check from {script_path}...")
    
    # 1. Parse bash script
    data = parse_pradan_script(script_path)
    logger.info(f"Parsed {len(data['urls'])} files to download from the PRADAN script.")
    
    # 2. Update config.yaml with extracted auth details
    update_config(config_path, data["cookie"], data["base_url"])
    
    # 3. Read config to resolve SQLite DB location
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
        
    version = dataset_version or config["current_dataset_version"]
    db_path = config["manifest_database"].replace("{version}", version)
    
    logger.info(f"Seeding SQLite manifest database for version '{version}' at {db_path}...")
    manifest = DownloadManifest(db_path)
    
    seeded_count = 0
    skipped_count = 0
    
    for url in data["urls"]:
        # Check if record already exists in database
        existing = manifest.get_by_source_url(url)
        if existing:
            skipped_count += 1
            continue
            
        # Parse metadata
        meta = parse_url_metadata(url)
        
        record = DownloadRecord(
            source_url=url,
            filename=meta["filename"],
            payload=meta["payload"],
            date=meta["date"],
            status="Queued"
        )
        
        manifest.insert(record)
        seeded_count += 1
        
    logger.info(f"Migration completed successfully.")
    logger.info(f"Seeded records: {seeded_count}")
    logger.info(f"Existing records skipped: {skipped_count}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Migrate PRADAN downloader script data into SuryaNet SQLite manifest.")
    parser.add_argument("--script", default="legacy/pradan_downloader.sh", help="Path to legacy bash script.")
    parser.add_argument("--config", default="data_pipeline/config.yaml", help="Path to config.yaml file.")
    parser.add_argument("--version", help="Target dataset version (overrides config.yaml default).")
    args = parser.parse_args()
    
    migrate(args.script, args.config, args.version)
