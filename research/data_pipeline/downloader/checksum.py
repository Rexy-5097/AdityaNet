import os
import hashlib
import zlib
from data_pipeline.downloader.logger import logger

def calculate_sha256(file_path: str) -> str:
    """Calculates the SHA256 hash of a file using chunked streaming for memory efficiency."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating SHA256 for {file_path}: {e}")
        raise

def calculate_crc32(file_path: str) -> str:
    """Calculates the CRC32 checksum of a file in hex string format."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
        
    crc_value = 0
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                crc_value = zlib.crc32(chunk, crc_value)
        return f"{crc_value & 0xFFFFFFFF:08X}"
    except Exception as e:
        logger.error(f"Error calculating CRC32 for {file_path}: {e}")
        raise

def write_checksum_file(file_path: str, sha256_val: str, checksums_dir: str):
    """Writes a .sha256 file containing the calculated hash to the target directory."""
    os.makedirs(checksums_dir, exist_ok=True)
    filename = os.path.basename(file_path)
    checksum_path = os.path.join(checksums_dir, f"{filename}.sha256")
    
    try:
        with open(checksum_path, "w", encoding="utf-8") as f:
            f.write(sha256_val)
    except Exception as e:
        logger.error(f"Failed to write checksum file {checksum_path}: {e}")
        raise
