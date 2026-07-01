import os
import re
import zipfile
import gzip
import numpy as np
import pandas as pd
from typing import Dict, Any
from astropy.io import fits
from data_pipeline.plugins.base import BasePayloadPlugin

class SolexsPayloadPlugin(BasePayloadPlugin):
    @property
    def name(self) -> str:
        return "solexs"

    def match_url(self, url: str) -> bool:
        filename = url.split('/')[-1].split('?')[0].lower()
        return "solexs" in url.lower() or "slx" in filename

    def verify(self, file_path: str) -> bool:
        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            return False
        
        try:
            # Step 1: ZIP integrity check
            with zipfile.ZipFile(file_path) as zf:
                if zf.testzip() is not None:
                    return False
                
                # Step 2: Ensure it contains SoLEXS FITS files
                fits_files = [n for n in zf.namelist() if n.endswith('.gz') or n.endswith('.fits')]
                if not fits_files:
                    return False
                
                # Step 3: FITS readability check on at least one file
                test_file = fits_files[0]
                with zf.open(test_file) as f_zip:
                    if test_file.endswith('.gz'):
                        with gzip.open(f_zip) as f_gz:
                            with fits.open(f_gz) as hdul:
                                if len(hdul) < 2:
                                    return False
                    else:
                        with fits.open(f_zip) as hdul:
                            if len(hdul) < 2:
                                return False
            return True
        except Exception:
            return False

    def check_quality(self, file_path: str) -> Dict[str, Any]:
        report = {
            "valid": True,
            "errors": [],
            "nan_percentage": 0.0,
            "duplicate_timestamps": 0,
            "time_continuity": True,
            "corrupted_records": 0
        }
        
        try:
            with zipfile.ZipFile(file_path) as zf:
                # Find lightcurve or spectra data files
                data_files = [n for n in zf.namelist() if ('.lc' in n or '.pi' in n) and n.endswith('.gz')]
                if not data_files:
                    report["valid"] = False
                    report["errors"].append("No lightcurve (.lc) or spectra (.pi) data files found inside ZIP.")
                    return report
                
                nan_counts = 0
                total_cells = 0
                
                for df_name in data_files:
                    with zf.open(df_name) as f_zip:
                        with gzip.open(f_zip) as f_gz:
                            with fits.open(f_gz) as hdul:
                                # Data extension is usually extension 1
                                if len(hdul) < 2:
                                    continue
                                table_hdu = hdul[1]
                                data = table_hdu.data
                                if data is None or len(data) == 0:
                                    continue
                                
                                # Verify required columns
                                colnames = [col.name.upper() for col in table_hdu.columns]
                                if "TIME" not in colnames:
                                    report["valid"] = False
                                    report["errors"].append(f"Required column 'TIME' missing in {df_name}")
                                    continue
                                
                                times = data["TIME"]
                                
                                # Check duplicate timestamps
                                dups = len(times) - len(np.unique(times))
                                if dups > 0:
                                    report["duplicate_timestamps"] += dups
                                    report["errors"].append(f"Found {dups} duplicate timestamps in {df_name}")
                                
                                # Check timestamp continuity (monotonicity)
                                is_monotonic = np.all(np.diff(times) >= 0)
                                if not is_monotonic:
                                    report["time_continuity"] = False
                                    report["errors"].append(f"Time array is not monotonic increasing in {df_name}")
                                
                                # Calculate NaNs across all numeric columns
                                for col in table_hdu.columns:
                                    col_data = data[col.name]
                                    total_cells += col_data.size
                                    if np.issubdtype(col_data.dtype, np.number):
                                        nans = np.isnan(col_data).sum()
                                        nan_counts += nans
                                        
                                        # Out of bounds / corrupted value checks (e.g. negative values in rates/counts)
                                        if col.name.upper() in ["RATE", "COUNTS"]:
                                            corrupted = (col_data < 0).sum()
                                            if corrupted > 0:
                                                report["corrupted_records"] += corrupted
                                                report["errors"].append(f"Negative values found in column '{col.name}' in {df_name}")
                
                if total_cells > 0:
                    report["nan_percentage"] = float(nan_counts / total_cells) * 100.0
                
                if report["nan_percentage"] > 20.0:
                    report["valid"] = False
                    report["errors"].append(f"High NaN percentage: {report['nan_percentage']:.2f}%")
                    
        except Exception as e:
            report["valid"] = False
            report["errors"].append(f"Exception during quality check: {str(e)}")
            
        return report

    def extract_metadata(self, file_path: str) -> Dict[str, Any]:
        meta = {
            "instrument": "solexs",
            "observation_date": "",
            "cadence": 1.0,
            "num_rows": 0,
            "start_time": "",
            "end_time": "",
            "energy_channels": "[]",
            "missing_percentage": 0.0
        }
        
        try:
            filename = os.path.basename(file_path)
            # Try to get date from filename
            date_match = re.search(r'\d{8}', filename)
            if date_match:
                meta["observation_date"] = date_match.group(0)
            
            with zipfile.ZipFile(file_path) as zf:
                fits_files = [n for n in zf.namelist() if n.endswith('.gz') or n.endswith('.fits')]
                for fits_name in fits_files:
                    if ".lc" in fits_name or ".pi" in fits_name:
                        with zf.open(fits_name) as f_zip:
                            with gzip.open(f_zip) as f_gz:
                                with fits.open(f_gz) as hdul:
                                    # Parse primary header
                                    hdr0 = hdul[0].header
                                    meta["observation_date"] = hdr0.get("DATE-OBS", meta["observation_date"]).split('T')[0].replace('-', '')
                                    
                                    if len(hdul) > 1:
                                        table_hdu = hdul[1]
                                        hdr1 = table_hdu.header
                                        data = table_hdu.data
                                        
                                        meta["num_rows"] = len(data) if data is not None else 0
                                        
                                        # Retrieve start/end time and cadence
                                        tstart = hdr1.get("TSTART") or (data["TIME"][0] if data is not None and len(data) > 0 else "")
                                        tstop = hdr1.get("TSTOP") or (data["TIME"][-1] if data is not None and len(data) > 0 else "")
                                        meta["start_time"] = str(tstart)
                                        meta["end_time"] = str(tstop)
                                        
                                        # Compute average cadence
                                        if data is not None and len(data) > 1:
                                            diffs = np.diff(data["TIME"])
                                            meta["cadence"] = float(np.median(diffs))
                                        
                                        # Energy channels check
                                        if "CHANNEL" in [c.name.upper() for c in table_hdu.columns]:
                                            channels = list(np.unique(data["CHANNEL"]))
                                            meta["energy_channels"] = str(channels[:50]) # store sample of channels
                                        elif ".pi" in fits_name:
                                            meta["energy_channels"] = "[13-37]" # Energy band representation
                        break
        except Exception:
            pass
            
        return meta
