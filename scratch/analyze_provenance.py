import os
import json

def main():
    path = "artifacts/aditya_l1/download_manifest.json"
    if not os.path.exists(path):
        print("Manifest not found")
        return
        
    with open(path, "r") as f:
        manifest = json.load(f)
        
    hel1os_files = []
    solexs_files = []
    
    for fname, meta in manifest.items():
        if meta["payload"] == "HEL1OS":
            hel1os_files.append((fname, meta))
        elif meta["payload"] == "SoLEXS":
            solexs_files.append((fname, meta))
            
    def summarize(payload_name, files):
        count = len(files)
        total_bytes = sum(m["file_size_bytes"] for _, m in files)
        dates = [m["observation_date"] for _, m in files]
        min_date = min(dates) if dates else None
        max_date = max(dates) if dates else None
        checksums = set(m["checksum_sha256"] for _, m in files)
        unique_checksums = len(checksums)
        
        print(f"=== {payload_name} ===")
        print(f"File Count: {count}")
        print(f"Total Bytes: {total_bytes} bytes ({total_bytes / (1024*1024):.4f} MB)")
        print(f"Date Range: {min_date} to {max_date}")
        print(f"Unique Checksums: {unique_checksums} (checksums: {checksums})")
        
    summarize("HEL1OS", hel1os_files)
    summarize("SoLEXS", solexs_files)

if __name__ == "__main__":
    main()
