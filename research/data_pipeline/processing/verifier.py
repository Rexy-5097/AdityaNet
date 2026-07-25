import hashlib
import zipfile
import os
import shutil

def calculate_sha256(file_path, chunk_size=8192):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_zip_integrity(file_path):
    """Checks if a file is a valid, non-empty ZIP archive."""
    if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
        return False, "File is missing or empty"
    
    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            # testzip() returns None if no errors are found
            if zip_ref.testzip() is not None:
                return False, "ZIP file is corrupted (internal CRC check failed)"
            
            # Additional check: ensure there are files inside
            if not zip_ref.namelist():
                return False, "ZIP file is empty (no members)"
                
        return True, "Success"
    except zipfile.BadZipFile:
        return False, "Not a valid ZIP file"
    except Exception as e:
        return False, f"Unexpected error during ZIP verification: {str(e)}"

def quarantine_file(file_path, rejected_dir):
    """Moves a corrupted or rejected file to the rejected directory."""
    if not os.path.exists(rejected_dir):
        os.makedirs(rejected_dir)
    
    filename = os.path.basename(file_path)
    dest_path = os.path.join(rejected_dir, filename)
    shutil.move(file_path, dest_path)
    return dest_path
