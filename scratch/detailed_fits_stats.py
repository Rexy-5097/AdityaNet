import os
import json
import gc
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.time import Time

ROOT = "/Users/soumyadebtripathy/AdityaNet/data/aditya_l1/raw_extracted"

representative_files = {
    "hel1os_czt1_lightcurve": "hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/czt/lightcurve_czt1.fits",
    "hel1os_czt2_lightcurve": "hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/czt/lightcurve_czt2.fits",
    "hel1os_cdte1_lightcurve": "hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/cdte/lightcurve_cdte1.fits",
    "hel1os_cdte2_lightcurve": "hel1os/2026/06/10/HLS_20260610_000012_43174sec_lev1_V111/cdte/lightcurve_cdte2.fits",
    "hel1os_czt_spectra": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/czt/hel1os_czt_spectra_czt1.fits",
    "hel1os_cdte_spectra": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/cdte/hel1os_cdte_spectra_cdte1.fits",
    "hel1os_events": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/events/evt.fits",
    "hel1os_gti_czt1": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticzt1.fits",
    "hel1os_gti_czt2": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticzt2.fits",
    "hel1os_gti_cdte1": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticdte1.fits",
    "hel1os_gti_cdte2": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/gticdte2.fits",
    "hel1os_housekeeping": "hel1os/2026/06/11/HLS_20260611_114949_43807sec_lev1_V111/aux/hk.fits",
    "solexs_sdd2_lightcurve": "solexs/AL1_SLX_L1_20260610_v1.0/SDD2/AL1_SOLEXS_20260610_SDD2_L1.lc.gz",
    "solexs_sdd2_spectra": "solexs/AL1_SLX_L1_20260610_v1.0/SDD2/AL1_SOLEXS_20260610_SDD2_L1.pi.gz",
    "solexs_sdd1_gti": "solexs/AL1_SLX_L1_20260610_v1.0/SDD1/AL1_SOLEXS_20260610_SDD1_L1.gti.gz",
    "solexs_sdd2_gti": "solexs/AL1_SLX_L1_20260610_v1.0/SDD2/AL1_SOLEXS_20260610_SDD2_L1.gti.gz"
}

# GOES test split info to determine overlap / join feasibility
goes_parquet_path = "/Users/soumyadebtripathy/AdityaNet/artifacts/research/test.parquet"
df_goes = pd.read_parquet(goes_parquet_path, columns=["timestamp"])
df_goes["timestamp"] = pd.to_datetime(df_goes["timestamp"]).dt.floor("1min")
goes_minutes = set(df_goes["timestamp"].values)
print(f"Loaded {len(goes_minutes)} GOES test minutes")
del df_goes
gc.collect()

def isot_to_utc_series(isot_col):
    strs = [(t.decode("utf-8") if isinstance(t, bytes) else str(t)).strip() for t in isot_col]
    dti = pd.to_datetime(strs, utc=True, errors="coerce")
    return pd.Series(dti.tz_convert(None).values)

def mjd_to_utc_series(mjd_col):
    arr = mjd_col.byteswap().newbyteorder().astype(float)
    result = []
    for m in arr:
        if np.isnan(m) or np.isinf(m):
            result.append(pd.NaT)
        else:
            try:
                result.append(pd.Timestamp(Time(m, format="mjd", scale="utc").datetime))
            except Exception:
                result.append(pd.NaT)
    return pd.Series(result, dtype="datetime64[ns]")

def check_goes_join(ts_series):
    floored = pd.to_datetime(ts_series).dt.floor("1min")
    file_minutes = set(floored.dropna().values)
    overlap = file_minutes & goes_minutes
    return len(overlap) > 0, len(overlap), len(file_minutes)

results = {}

for prod_name, rel_path in representative_files.items():
    abs_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(abs_path):
        results[prod_name] = {
            "status": "missing_file",
            "file": rel_path
        }
        continue
    
    print(f"Auditing {prod_name}...")
    
    with fits.open(abs_path) as hdul:
        # Determine product-wide variables
        prod_hdus = []
        for idx in range(1, len(hdul)):
            hdu = hdul[idx]
            if hdu.data is None:
                continue
            
            colnames = list(hdu.data.names)
            n_rows = len(hdu.data)
            
            # Determine cadence
            cadence_median_s = None
            ts_series = None
            if "ISOT" in colnames:
                ts_series = isot_to_utc_series(hdu.data["ISOT"])
            elif "utc-isot" in colnames:
                ts_series = isot_to_utc_series(hdu.data["utc-isot"])
            elif "mjd" in colnames:
                ts_series = mjd_to_utc_series(hdu.data["mjd"])
            elif "MJD" in colnames:
                ts_series = mjd_to_utc_series(hdu.data["MJD"])
            elif "TIME" in colnames and "solexs" in rel_path:
                # get epoch from header
                mjdrefi = float(hdul[0].header.get("MJDREFI", hdu.header.get("MJDREFI", 40587)))
                mjdreff = float(hdul[0].header.get("MJDREFF", hdu.header.get("MJDREFF", 0.0)))
                epoch = pd.to_datetime(Time(mjdrefi + mjdreff, format="mjd", scale="utc").datetime)
                time_s = hdu.data["TIME"].byteswap().newbyteorder().astype(float)
                ts_series = pd.Series(epoch + pd.to_timedelta(time_s, unit="s"), dtype="datetime64[ns]")
            elif "TSTART" in colnames and "solexs" in rel_path:
                mjdrefi = float(hdul[0].header.get("MJDREFI", hdu.header.get("MJDREFI", 40587)))
                mjdreff = float(hdul[0].header.get("MJDREFF", hdu.header.get("MJDREFF", 0.0)))
                epoch = pd.to_datetime(Time(mjdrefi + mjdreff, format="mjd", scale="utc").datetime)
                tstart = hdu.data["TSTART"].byteswap().newbyteorder().astype(float)
                ts_series = pd.Series(epoch + pd.to_timedelta(tstart, unit="s"), dtype="datetime64[ns]")
            elif "TSTART" in colnames and "hel1os" in rel_path:
                mjdstart = float(hdul[0].header.get("MJDSTART", hdul[0].header.get("TSTART", 0.0)))
                epoch = pd.to_datetime(Time(mjdstart, format="mjd", scale="utc").datetime)
                tstart_s = hdu.data["TSTART"].byteswap().newbyteorder().astype(float)
                ts_series = pd.Series([epoch + pd.to_timedelta(v, unit='s') if np.isfinite(v) else pd.NaT for v in tstart_s], dtype="datetime64[ns]")
            elif "START" in colnames and "solexs" in rel_path:
                mjdrefi = float(hdul[0].header.get("MJDREFI", hdu.header.get("MJDREFI", 40587)))
                mjdreff = float(hdul[0].header.get("MJDREFF", hdu.header.get("MJDREFF", 0.0)))
                epoch = pd.to_datetime(Time(mjdrefi + mjdreff, format="mjd", scale="utc").datetime)
                start_s = hdu.data["START"].byteswap().newbyteorder().astype(float)
                ts_series = pd.Series(epoch + pd.to_timedelta(start_s, unit="s"), dtype="datetime64[ns]")
            elif "tstart" in colnames:
                ts_series = mjd_to_utc_series(hdu.data["tstart"])
                
            if ts_series is not None and len(ts_series) > 1:
                ts_sorted = ts_series.dropna().sort_values()
                if len(ts_sorted) > 1:
                    diffs = ts_sorted.diff().dropna().dt.total_seconds()
                    cadence_median_s = float(diffs.median())
            
            numerical_cols = []
            constant_cols = []
            varying_cols = []
            
            for col in colnames:
                col_data = hdu.data[col]
                dtype = col_data.dtype
                shape = col_data.shape
                
                is_num = np.issubdtype(dtype, np.number) or (len(shape) > 1 and np.issubdtype(dtype.subdtype[0] if hasattr(dtype, 'subdtype') and dtype.subdtype else dtype, np.number))
                if is_num:
                    numerical_cols.append(col)
                    
                # check if varying or constant
                try:
                    if len(shape) > 1:
                        # For vector/array columns: if any row differs from the first row, it varies.
                        # We can check this by comparing all rows with the first row.
                        varies = not np.all(col_data == col_data[0:1])
                    else:
                        if np.issubdtype(dtype, np.number):
                            valid = col_data[np.isfinite(col_data)]
                            if len(valid) == 0:
                                varies = False
                            else:
                                varies = np.nanstd(valid) > 0
                        else:
                            varies = len(np.unique(col_data)) > 1
                except Exception as e:
                    varies = True
                    
                if varies:
                    varying_cols.append(col)
                else:
                    constant_cols.append(col)
            
            # aggregation feasibility
            can_agg_1m = False
            can_agg_5m = False
            if cadence_median_s is not None:
                if cadence_median_s <= 60.0:
                    can_agg_1m = True
                if cadence_median_s <= 300.0:
                    can_agg_5m = True
                    
            # goes join
            can_join_goes = False
            n_overlap = 0
            n_file_min = 0
            if ts_series is not None:
                can_join_goes, n_overlap, n_file_min = check_goes_join(ts_series)
            
            prod_hdus.append({
                "hdu_name": hdu.name,
                "hdu_index": idx,
                "n_rows": n_rows,
                "cadence_median_s": cadence_median_s,
                "columns": colnames,
                "numerical_columns": numerical_cols,
                "varying_columns": varying_cols,
                "constant_columns": constant_cols,
                "can_agg_1m": can_agg_1m,
                "can_agg_5m": can_agg_5m,
                "can_join_goes": can_join_goes,
                "goes_overlap_info": {"n_overlap": n_overlap, "n_file_min": n_file_min}
            })
            
        results[prod_name] = {
            "status": "success",
            "file": rel_path,
            "hdus": prod_hdus
        }

# Special analysis for HEL1OS event files
print("Running special analysis on events...")
evt_path = os.path.join(ROOT, representative_files["hel1os_events"])
evt_info = {}
if os.path.exists(evt_path):
    with fits.open(evt_path) as hdul:
        for idx in range(1, len(hdul)):
            hdu = hdul[idx]
            hdu_name = hdu.name
            colnames = hdu.data.names
            n_rows = len(hdu.data)
            
            print(f"  Event HDU: {hdu_name}")
            
            # Find energy column
            energy_col = None
            for col in ["ener", "energy", "ENERGY", "ENER"]:
                if col in colnames:
                    energy_col = col
                    break
                    
            # Detector IDs
            # The detector ID is typically represented by the HDU itself or within headers.
            # In HEL1OS, CdTe1, CdTe2, CZT1, CZT2 are the detectors.
            detector_id = hdu_name.split("-")[0] # e.g. CZT1 from CZT1-EVENTS
            
            # Pixel IDs
            pixel_ids = []
            if "pix" in colnames:
                pixel_ids = [int(p) for p in np.unique(hdu.data["pix"])]
                
            # Photon counts per minute
            # Let's decode timestamps in a fast, vectorized way
            ts_col = hdu.data["utc-isot"]
            strs = [(t.decode() if isinstance(t, bytes) else str(t)).strip() for t in ts_col]
            dti = pd.to_datetime(strs, utc=True, errors="coerce")
            ts = pd.Series(dti.tz_convert(None).values)
            
            counts_per_min = ts.groupby(ts.dt.floor("1min")).size()
            
            photon_counts_min_stats = {
                "mean": float(counts_per_min.mean()) if len(counts_per_min) > 0 else 0.0,
                "std": float(counts_per_min.std()) if len(counts_per_min) > 1 else 0.0,
                "min": int(counts_per_min.min()) if len(counts_per_min) > 0 else 0,
                "max": int(counts_per_min.max()) if len(counts_per_min) > 0 else 0,
                "total": int(counts_per_min.sum())
            }
            
            # Photon counts per energy band
            energy_band_counts = {}
            if energy_col is not None:
                energies = hdu.data[energy_col].byteswap().newbyteorder().astype(float)
                # Define bands based on detector type
                if "CZT" in hdu_name:
                    bands = [
                        ("20-40", 20.0, 40.0),
                        ("40-60", 40.0, 60.0),
                        ("60-80", 60.0, 80.0),
                        ("80-150", 80.0, 150.0),
                        ("18-160", 18.0, 160.0)
                    ]
                else: # CdTe
                    bands = [
                        ("5-20", 5.0, 20.0),
                        ("20-30", 20.0, 30.0),
                        ("30-40", 30.0, 40.0),
                        ("40-60", 40.0, 60.0),
                        ("1.8-90", 1.8, 90.0)
                    ]
                for name, low, high in bands:
                    count = int(np.sum((energies >= low) & (energies < high)))
                    energy_band_counts[name] = count
            
            evt_info[hdu_name] = {
                "detector_id": detector_id,
                "energy_col": energy_col,
                "n_rows": n_rows,
                "unique_pixels_count": len(pixel_ids),
                "pixel_ids_sample": pixel_ids[:10],
                "pixel_ids_full": pixel_ids,
                "photon_counts_per_minute_stats": photon_counts_min_stats,
                "photon_counts_per_energy_band": energy_band_counts
            }

results["special_events_analysis"] = evt_info

# Special analysis for spectra products
print("Running special analysis on spectra...")
spectra_info = {}
for spectra_prod in ["hel1os_czt_spectra", "hel1os_cdte_spectra", "solexs_sdd2_spectra"]:
    rel_path = representative_files[spectra_prod]
    abs_path = os.path.join(ROOT, rel_path)
    if not os.path.exists(abs_path):
        continue
        
    with fits.open(abs_path) as hdul:
        # Spectra are usually in HDU 1
        hdu = hdul[1]
        colnames = hdu.data.names
        print(f"  Spectra product: {spectra_prod}")
        
        # Check number of spectral channels
        # Typically from CHANNEL column shape, or COUNTS column shape
        n_channels = None
        if "CHANNEL" in colnames:
            chan_data = hdu.data["CHANNEL"]
            if len(chan_data.shape) > 1:
                n_channels = chan_data.shape[1]
            else:
                # Variable length array
                # Let's check first row length
                n_channels = len(chan_data[0])
        elif "COUNTS" in colnames:
            counts_data = hdu.data["COUNTS"]
            if len(counts_data.shape) > 1:
                n_channels = counts_data.shape[1]
            else:
                n_channels = len(counts_data[0])
                
        # counts per bin
        # We can compute mean, std, min, max counts across all rows and all channels
        counts_stats = {}
        if "COUNTS" in colnames:
            counts_data = hdu.data["COUNTS"]
            # if variable length array, flatten it
            if len(counts_data.shape) == 1:
                flat_counts = np.concatenate(counts_data)
            else:
                flat_counts = counts_data.flatten()
            flat_counts = flat_counts.byteswap().newbyteorder().astype(float)
            flat_counts = flat_counts[np.isfinite(flat_counts)]
            
            counts_stats = {
                "mean": float(flat_counts.mean()) if len(flat_counts) > 0 else 0.0,
                "std": float(flat_counts.std()) if len(flat_counts) > 1 else 0.0,
                "min": float(flat_counts.min()) if len(flat_counts) > 0 else 0.0,
                "max": float(flat_counts.max()) if len(flat_counts) > 0 else 0.0,
                "sum": float(flat_counts.sum())
            }
            
        # energy bins
        # For HEL1OS, does primary header or EBOUNDS extension exist? Let's check hdul
        energy_bins = None
        if "EBOUNDS" in [h.name for h in hdul]:
            ebounds = hdul["EBOUNDS"]
            print("    Found EBOUNDS extension!")
            eb_cols = ebounds.data.names
            if "E_MIN" in eb_cols and "E_MAX" in eb_cols:
                emin = ebounds.data["E_MIN"].byteswap().newbyteorder().astype(float)
                emax = ebounds.data["E_MAX"].byteswap().newbyteorder().astype(float)
                energy_bins = [{"channel": int(idx), "e_min": float(emin[idx]), "e_max": float(emax[idx])} for idx in range(len(emin))]
        else:
            # Let's check if there is an energy channel configuration in the header
            print("    No EBOUNDS extension found. Energy bins not explicitly stored in data rows.")
            
        spectra_info[spectra_prod] = {
            "n_channels": n_channels,
            "counts_stats_per_bin": counts_stats,
            "has_ebounds": energy_bins is not None,
            "energy_bins_count": len(energy_bins) if energy_bins is not None else None,
            "energy_bins_sample": energy_bins[:5] if energy_bins is not None else None
        }

results["special_spectra_analysis"] = spectra_info

print("Writing output to JSON...")
with open("/Users/soumyadebtripathy/AdityaNet/scratch/detailed_audit_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Finished!")
