import os
import json
import csv
import sqlite3
from typing import List, Dict, Any
from data_pipeline.downloader.logger import logger

class InventoryGenerator:
    def __init__(self, db_path: str, output_dir: str):
        self.db_path = db_path
        self.output_dir = output_dir

    def _get_records(self) -> List[Dict[str, Any]]:
        """Queries the manifest database for all downloads."""
        if not os.path.exists(self.db_path):
            logger.warning(f"Manifest database not found at {self.db_path}. Cannot generate inventory.")
            return []
            
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            cursor = conn.execute("SELECT * FROM downloads ORDER BY id DESC")
            records = []
            for row in cursor.fetchall():
                # Parse date to extract year/month
                date_val = row["date"] or ""
                year = date_val[:4] if len(date_val) >= 4 else ""
                month = date_val[4:6] if len(date_val) >= 6 else ""
                
                records.append({
                    "filename": row["filename"],
                    "payload": row["payload"],
                    "year": year,
                    "month": month,
                    "date": date_val,
                    "size": row["size"],
                    "checksum": row["checksum"],
                    "status": row["status"],
                    "path": row["path"]
                })
            return records
        finally:
            conn.close()

    def generate(self):
        """Generates inventory.json and inventory.csv in the output directory."""
        records = self._get_records()
        if not records:
            logger.info("No records found in manifest database. Inventory will be empty.")
            
        os.makedirs(self.output_dir, exist_ok=True)
        
        json_path = os.path.join(self.output_dir, "inventory.json")
        csv_path = os.path.join(self.output_dir, "inventory.csv")
        
        # 1. Write inventory.json
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(records, f, indent=4)
            logger.info(f"Inventory JSON successfully written to {json_path}")
        except Exception as e:
            logger.error(f"Failed to write inventory JSON: {e}")
            raise

        # 2. Write inventory.csv
        try:
            fieldnames = ["filename", "payload", "year", "month", "date", "size", "checksum", "status", "path"]
            with open(csv_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                for rec in records:
                    writer.writerow(rec)
            logger.info(f"Inventory CSV successfully written to {csv_path}")
        except Exception as e:
            logger.error(f"Failed to write inventory CSV: {e}")
            raise
