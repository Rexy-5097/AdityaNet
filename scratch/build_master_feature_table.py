import os
import gc
import glob
import json
import logging
import numpy as np
import pandas as pd
from astropy.io import fits
from astropy.time import Time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

ROOT = "/Users/soumyadebtripathy/AdityaNet/data/aditya_l1/raw_extracted"
HEL_BASE = os.path.join(ROOT, "hel1os")
SLX_BASE = os.path.join(ROOT, "solexs")

OUT_PARQUET = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"
OUT_JSON = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_inventory.json"
OUT_MD = "/Users/soumyadebtripathy/AdityaNet/brain/aditya_l1_master_feature_inventory.md"

os.makedirs(os.path.dirname(OUT_PARQUET), exist_ok=True)

# Define time grid
start_time = pd.Timestamp("2026-06-10 00:00:00")
end_time = pd.Timestamp("2026-06-13 23:59:00")
time_grid = pd.date_range(start_time, end_time, freq="1min")
logger.info(f"Target time grid: {len(time_grid)} rows (from {start_time} to {end_time})")

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

# 1. HEL1OS Lightcurves
def load_hel1os_lc(pattern, time_grid, prefix):
    files = sorted(glob.glob(os.path.join(HEL_BASE, "**", pattern), recursive=True))
    logger.info(f"Found {len(files)} files for {pattern}")
    dfs = []
    for f in files:
        try:
            with fits.open(f) as hdul:
                file_dfs = []
                for idx in range(1, len(hdul)):
                    h = hdul[idx]
                    if h.data is None:
                        continue
                    hdu_name = h.name
                    # format band name
                    band_part = hdu_name.split("BAND_")[-1].replace("KEV", "").replace("TO_", "-").strip().lower()
                    
                    isot = h.data["ISOT"]
                    strs = [t.decode("utf-8").strip() if isinstance(t, bytes) else str(t).strip() for t in isot]
                    ts = pd.to_datetime(strs, utc=True, errors="coerce").tz_convert(None)
                    
                    ctr = h.data["CTR"].byteswap().newbyteorder().astype(float)
                    err = h.data["STAT_ERR"].byteswap().newbyteorder().astype(float)
                    
                    df_hdu = pd.DataFrame({
                        "timestamp": ts,
                        f"{prefix}_band_{band_part}_ctr": ctr,
                        f"{prefix}_band_{band_part}_stat_err": err
                    })
                    df_hdu = df_hdu[(df_hdu["timestamp"] >= time_grid[0]) & (df_hdu["timestamp"] <= time_grid[-1])]
                    if not df_hdu.empty:
                        df_hdu_agg = df_hdu.resample("1min", on="timestamp").mean()
                        file_dfs.append(df_hdu_agg)
                if file_dfs:
                    merged_file = file_dfs[0]
                    for other_df in file_dfs[1:]:
                        merged_file = merged_file.join(other_df, how="outer")
                    dfs.append(merged_file)
        except Exception as e:
            logger.error(f"Error parsing HEL1OS LC {f}: {e}")
    if dfs:
        df_all = pd.concat(dfs).sort_index()
        df_all = df_all.groupby(df_all.index).mean()
        return df_all.reindex(time_grid)
    return pd.DataFrame(index=time_grid)

# 2. SoLEXS SDD2 Lightcurve
def load_solexs_lc(time_grid):
    files = sorted(glob.glob(os.path.join(SLX_BASE, "**", "*_SDD2_L1.lc.gz"), recursive=True))
    logger.info(f"Found {len(files)} files for SoLEXS SDD2 lightcurve")
    dfs = []
    for f in files:
        try:
            with fits.open(f) as hdul:
                h0, h1 = hdul[0].header, hdul[1].header
                mjdrefi = float(h0.get("MJDREFI", h1.get("MJDREFI", 40587)))
                mjdreff = float(h0.get("MJDREFF", h1.get("MJDREFF", 0.0)))
                epoch = pd.to_datetime(Time(mjdrefi + mjdreff, format="mjd", scale="utc").datetime)
                
                time_s = hdul[1].data["TIME"].byteswap().newbyteorder().astype(float)
                counts = hdul[1].data["COUNTS"].byteswap().newbyteorder().astype(float)
                ts = epoch + pd.to_timedelta(time_s, unit="s")
                
                df = pd.DataFrame({
                    "timestamp": ts,
                    "solexs_sdd2_lc_counts": counts
                })
                df = df[(df["timestamp"] >= time_grid[0]) & (df["timestamp"] <= time_grid[-1])]
                if not df.empty:
                    df_agg = df.resample("1min", on="timestamp")["solexs_sdd2_lc_counts"].mean().to_frame()
                    dfs.append(df_agg)
        except Exception as e:
            logger.error(f"Error parsing SoLEXS LC {f}: {e}")
    if dfs:
        df_all = pd.concat(dfs).sort_index()
        df_all = df_all.groupby(df_all.index).mean()
        return df_all.reindex(time_grid)
    return pd.DataFrame(index=time_grid)

# 3. HEL1OS Housekeeping
def load_hel1os_hk(time_grid):
    files = sorted(glob.glob(os.path.join(HEL_BASE, "**", "hk.fits"), recursive=True))
    logger.info(f"Found {len(files)} files for Housekeeping")
    dfs = []
    for f in files:
        try:
            with fits.open(f) as hdul:
                h = hdul[1]
                colnames = list(h.data.names)
                mjd_col = h.data["mjd"].byteswap().newbyteorder().astype(float)
                ts = mjd_to_utc_series(mjd_col)
                
                cols_to_use = []
                for col in colnames:
                    if col == "mjd":
                        continue
                    arr = h.data[col]
                    raw = arr.byteswap().newbyteorder() if hasattr(arr, "byteswap") else arr
                    if np.issubdtype(raw.dtype, np.number):
                        if len(raw) > 1 and np.nanstd(raw.astype(float)) > 0:
                            cols_to_use.append(col)
                            
                data_dict = {"timestamp": ts}
                for col in cols_to_use:
                    data_dict[f"hel1os_hk_{col}_mean"] = h.data[col].byteswap().newbyteorder().astype(float)
                    
                df = pd.DataFrame(data_dict)
                df = df[(df["timestamp"] >= time_grid[0]) & (df["timestamp"] <= time_grid[-1])]
                if not df.empty:
                    df_agg = df.resample("1min", on="timestamp").mean()
                    dfs.append(df_agg)
        except Exception as e:
            logger.error(f"Error parsing HEL1OS HK {f}: {e}")
    if dfs:
        df_all = pd.concat(dfs).sort_index()
        df_all = df_all.groupby(df_all.index).mean()
        return df_all.reindex(time_grid)
    return pd.DataFrame(index=time_grid)

# 4. SoLEXS SDD2 GTI
def load_solexs_gti(time_grid):
    files = sorted(glob.glob(os.path.join(SLX_BASE, "**", "*_SDD2_L1.gti.gz"), recursive=True))
    logger.info(f"Found {len(files)} files for SoLEXS SDD2 GTI")
    intervals = []
    for f in files:
        try:
            with fits.open(f) as hdul:
                h0, h1 = hdul[0].header, hdul[1].header
                mjdrefi = float(h0.get("MJDREFI", h1.get("MJDREFI", 40587)))
                mjdreff = float(h0.get("MJDREFF", h1.get("MJDREFF", 0.0)))
                epoch = pd.to_datetime(Time(mjdrefi + mjdreff, format="mjd", scale="utc").datetime)
                
                n_rows = len(hdul[1].data)
                if n_rows > 0:
                    start_s = hdul[1].data["START"].byteswap().newbyteorder().astype(float)
                    stop_s = hdul[1].data["STOP"].byteswap().newbyteorder().astype(float)
                    for i in range(n_rows):
                        t_start = epoch + pd.to_timedelta(start_s[i], unit="s")
                        t_stop = epoch + pd.to_timedelta(stop_s[i], unit="s")
                        intervals.append((t_start, t_stop))
        except Exception as e:
            logger.error(f"Error parsing SoLEXS GTI {f}: {e}")
            
    mask = np.zeros(len(time_grid), dtype=float)
    for i, t in enumerate(time_grid):
        for t_start, t_stop in intervals:
            if t_start <= t <= t_stop:
                mask[i] = 1.0
                break
    return pd.DataFrame({"solexs_sdd2_gti_mask": mask}, index=time_grid)

# 5. HEL1OS Spectra
def load_hel1os_spectra(pattern, time_grid, prefix, n_channels):
    files = sorted(glob.glob(os.path.join(HEL_BASE, "**", pattern), recursive=True))
    logger.info(f"Found {len(files)} files for {pattern}")
    dfs = []
    for f in files:
        try:
            with fits.open(f) as hdul:
                h0 = hdul[0].header
                h = hdul[1]
                n_rows = len(h.data)
                if n_rows == 0:
                    continue
                    
                mjdstart = float(h0.get("MJDSTART", h0.get("TSTART", 0.0)))
                epoch = pd.to_datetime(Time(mjdstart, format="mjd", scale="utc").datetime)
                tstart_s = h.data["TSTART"].byteswap().newbyteorder().astype(float)
                
                ts = pd.Series([epoch + pd.to_timedelta(v, unit='s') if np.isfinite(v) else pd.NaT for v in tstart_s], dtype="datetime64[ns]")
                
                counts = h.data["COUNTS"].byteswap().newbyteorder().astype(float)
                err = h.data["STAT_ERR"].byteswap().newbyteorder().astype(float)
                
                df_temp = pd.DataFrame({"timestamp": ts})
                valid_idx = (ts >= time_grid[0]) & (ts <= time_grid[-1])
                if not valid_idx.any():
                    continue
                    
                df_temp = df_temp[valid_idx]
                counts = counts[valid_idx]
                err = err[valid_idx]
                
                df_temp["minute"] = df_temp["timestamp"].dt.floor("1min")
                
                grouped_counts = pd.DataFrame(counts).groupby(df_temp["minute"]).mean()
                grouped_err = pd.DataFrame(err).groupby(df_temp["minute"]).mean()
                
                grouped_counts.columns = [f"{prefix}_counts_ch{i}" for i in range(n_channels)]
                grouped_err.columns = [f"{prefix}_err_ch{i}" for i in range(n_channels)]
                
                df_agg = pd.concat([grouped_counts, grouped_err], axis=1)
                dfs.append(df_agg)
        except Exception as e:
            logger.error(f"Error parsing HEL1OS spectra {f}: {e}")
            
    if dfs:
        df_all = pd.concat(dfs).sort_index()
        df_all = df_all.groupby(df_all.index).mean()
        return df_all.reindex(time_grid)
    return pd.DataFrame(index=time_grid)

# 6. SoLEXS Spectra
def load_solexs_spectra(time_grid, n_channels=340):
    files = sorted(glob.glob(os.path.join(SLX_BASE, "**", "*_SDD2_L1.pi.gz"), recursive=True))
    logger.info(f"Found {len(files)} files for SoLEXS spectra")
    dfs = []
    for f in files:
        try:
            with fits.open(f) as hdul:
                h0, h1 = hdul[0].header, hdul[1].header
                mjdrefi = float(h0.get("MJDREFI", h1.get("MJDREFI", 40587)))
                mjdreff = float(h0.get("MJDREFF", h1.get("MJDREFF", 0.0)))
                epoch = pd.to_datetime(Time(mjdrefi + mjdreff, format="mjd", scale="utc").datetime)
                
                tstart = hdul[1].data["TSTART"].byteswap().newbyteorder().astype(float)
                ts = epoch + pd.to_timedelta(tstart, unit="s")
                
                counts = hdul[1].data["COUNTS"].byteswap().newbyteorder().astype(float)
                
                df_temp = pd.DataFrame({"timestamp": ts})
                valid_idx = (ts >= time_grid[0]) & (ts <= time_grid[-1])
                if not valid_idx.any():
                    continue
                    
                df_temp = df_temp[valid_idx]
                counts = counts[valid_idx]
                
                df_temp["minute"] = df_temp["timestamp"].dt.floor("1min")
                
                grouped_counts = pd.DataFrame(counts).groupby(df_temp["minute"]).mean()
                grouped_counts.columns = [f"solexs_sdd2_spec_counts_ch{i}" for i in range(n_channels)]
                
                dfs.append(grouped_counts)
        except Exception as e:
            logger.error(f"Error parsing SoLEXS spectra {f}: {e}")
            
    if dfs:
        df_all = pd.concat(dfs).sort_index()
        df_all = df_all.groupby(df_all.index).mean()
        return df_all.reindex(time_grid)
    return pd.DataFrame(index=time_grid)

# 7. HEL1OS Events
def load_hel1os_events(time_grid):
    files = sorted(glob.glob(os.path.join(HEL_BASE, "**", "evt.fits"), recursive=True))
    logger.info(f"Found {len(files)} files for HEL1OS events")
    detector_dfs = {
        "cdte1": [],
        "cdte2": [],
        "czt1": [],
        "czt2": []
    }
    
    for f in files:
        try:
            with fits.open(f, memmap=True) as hdul:
                for idx in range(1, len(hdul)):
                    h = hdul[idx]
                    if h.data is None:
                        continue
                    hdu_name = h.name.lower()
                    det_key = hdu_name.split("-")[0]
                    if det_key not in detector_dfs:
                        continue
                    
                    n_rows = len(h.data)
                    if n_rows == 0:
                        continue
                    
                    utc_isot = h.data["utc-isot"]
                    ener = h.data["ener"].byteswap().newbyteorder().astype(float)
                    
                    strs = [t.decode() if isinstance(t, bytes) else str(t).strip() for t in utc_isot]
                    ts = pd.to_datetime(strs, utc=True, errors="coerce").tz_convert(None)
                    
                    valid_idx = (ts >= time_grid[0]) & (ts <= time_grid[-1])
                    if not valid_idx.any():
                        continue
                        
                    ts = ts[valid_idx]
                    ener = ener[valid_idx]
                    
                    df_temp = pd.DataFrame({
                        "minute": ts.floor("1min"),
                        "ener": ener
                    })
                    
                    df_total = df_temp.groupby("minute").size().rename(f"hel1os_evt_{det_key}_counts_total")
                    
                    band_dfs = [df_total]
                    if "czt" in det_key:
                        bands = [
                            ("20-40", 20.0, 40.0),
                            ("40-60", 40.0, 60.0),
                            ("60-80", 60.0, 80.0),
                            ("80-150", 80.0, 150.0),
                            ("18-160", 18.0, 160.0)
                        ]
                    else:
                        bands = [
                            ("5-20", 5.0, 20.0),
                            ("20-30", 20.0, 30.0),
                            ("30-40", 30.0, 40.0),
                            ("40-60", 40.0, 60.0),
                            ("1.8-90", 1.8, 90.0)
                        ]
                    for name, low, high in bands:
                        band_counts = df_temp[(df_temp["ener"] >= low) & (df_temp["ener"] < high)].groupby("minute").size()
                        band_counts = band_counts.rename(f"hel1os_evt_{det_key}_counts_band_{name}")
                        band_dfs.append(band_counts)
                        
                    df_file_det = pd.concat(band_dfs, axis=1).fillna(0)
                    detector_dfs[det_key].append(df_file_det)
                    
                    del utc_isot, ener, ts, df_temp, df_total, band_dfs
                    gc.collect()
        except Exception as e:
            logger.error(f"Error parsing HEL1OS events {f}: {e}")
                
    all_det_dfs = []
    for det_key, dfs_list in detector_dfs.items():
        if dfs_list:
            df_det = pd.concat(dfs_list).sort_index()
            df_det = df_det.groupby(df_det.index).sum()
            df_det = df_det.reindex(time_grid).fillna(0.0)
            all_det_dfs.append(df_det)
        else:
            bands = ["total"] + (["20-40", "40-60", "60-80", "80-150", "18-160"] if "czt" in det_key else ["5-20", "20-30", "30-40", "40-60", "1.8-90"])
            cols = [f"hel1os_evt_{det_key}_counts_{b}" if b == "total" else f"hel1os_evt_{det_key}_counts_band_{b}" for b in bands]
            all_det_dfs.append(pd.DataFrame(0.0, index=time_grid, columns=cols))
            
    df_events = pd.concat(all_det_dfs, axis=1)
    return df_events

# Run construction
logger.info("Starting master feature table construction...")
master_df = pd.DataFrame(index=time_grid)
master_df.index.name = "timestamp"

feature_sources = {}

# Helper to log and merge
def merge_and_register(name, df, source_name):
    global master_df
    logger.info(f"Merging {name} (shape: {df.shape})...")
    master_df = master_df.join(df, how="left")
    for col in df.columns:
        feature_sources[col] = source_name
    gc.collect()

# 1. HEL1OS Lightcurves
merge_and_register("hel1os_czt1_lc", load_hel1os_lc("lightcurve_czt1.fits", time_grid, "hel1os_czt1_lc"), "hel1os_czt1_lightcurve")
merge_and_register("hel1os_czt2_lc", load_hel1os_lc("lightcurve_czt2.fits", time_grid, "hel1os_czt2_lc"), "hel1os_czt2_lightcurve")
merge_and_register("hel1os_cdte1_lc", load_hel1os_lc("lightcurve_cdte1.fits", time_grid, "hel1os_cdte1_lc"), "hel1os_cdte1_lightcurve")
merge_and_register("hel1os_cdte2_lc", load_hel1os_lc("lightcurve_cdte2.fits", time_grid, "hel1os_cdte2_lc"), "hel1os_cdte2_lightcurve")

# 2. SoLEXS SDD2 Lightcurve
merge_and_register("solexs_sdd2_lc", load_solexs_lc(time_grid), "solexs_sdd2_lightcurve")

# 3. HEL1OS Housekeeping
merge_and_register("hel1os_hk", load_hel1os_hk(time_grid), "hel1os_housekeeping")

# 4. SoLEXS SDD2 GTI
merge_and_register("solexs_sdd2_gti", load_solexs_gti(time_grid), "solexs_sdd2_gti")

# 5. HEL1OS CZT Spectra (341 channels)
merge_and_register("hel1os_czt_spec", load_hel1os_spectra("hel1os_czt_spectra_czt1.fits", time_grid, "hel1os_czt_spec", 341), "hel1os_czt_spectra")

# 6. HEL1OS CdTe Spectra (511 channels)
merge_and_register("hel1os_cdte_spec", load_hel1os_spectra("hel1os_cdte_spectra_cdte1.fits", time_grid, "hel1os_cdte_spec", 511), "hel1os_cdte_spectra")

# 7. SoLEXS SDD2 Spectra (340 channels)
merge_and_register("solexs_sdd2_spec", load_solexs_spectra(time_grid, 340), "solexs_sdd2_spectra")

# 8. HEL1OS Events
merge_and_register("hel1os_events", load_hel1os_events(time_grid), "hel1os_events")

# Print info
logger.info(f"Master feature table shape: {master_df.shape}")
logger.info("Saving Parquet...")
master_df.reset_index().to_parquet(OUT_PARQUET, index=False)
logger.info(f"Parquet saved to {OUT_PARQUET}")

# Create feature inventory details
cols_stats = {}
earliest_ts = str(master_df.index.min())
latest_ts = str(master_df.index.max())

for col in master_df.columns:
    missing_count = int(master_df[col].isna().sum())
    cols_stats[col] = {
        "source": feature_sources[col],
        "missing_values": missing_count
    }

inventory = {
    "row_count": len(master_df),
    "column_count": len(master_df.columns),
    "earliest_timestamp": earliest_ts,
    "latest_timestamp": latest_ts,
    "features": cols_stats
}

with open(OUT_JSON, "w") as f:
    json.dump(inventory, f, indent=2)
logger.info(f"Inventory JSON saved to {OUT_JSON}")

# Build Markdown
md_lines = [
    "# Master Feature Table Construction Audit Report",
    "",
    "## 1. Executive Summary",
    "This report provides a detailed fact-collection audit of the master feature table constructed from usable Aditya-L1 telemetry products. All metrics and statistics represent measured values only.",
    "",
    "## 2. Table Statistics",
    f"- **Row Count**: {len(master_df)} (from {earliest_ts} to {latest_ts})",
    f"- **Column Count**: {len(master_df.columns)}",
    f"- **Earliest Timestamp**: {earliest_ts}",
    f"- **Latest Timestamp**: {latest_ts}",
    f"- **Parquet Path**: `artifacts/aditya_l1/master_feature_table.parquet`",
    "",
    "## 3. Feature Source Breakdown",
    ""
]

# Compute feature source counts and missing value counts
sources = {}
for col, info in cols_stats.items():
    src = info["source"]
    sources[src] = sources.get(src, {"count": 0, "missing_total": 0, "cols": []})
    sources[src]["count"] += 1
    sources[src]["missing_total"] += info["missing_values"]
    sources[src]["cols"].append(col)

md_lines.append("| Telemetry Product Source | Features Count | Total Missing Values | Pct Missing |")
md_lines.append("| --- | --- | --- | --- |")
for src in sorted(sources.keys()):
    count = sources[src]["count"]
    missing = sources[src]["missing_total"]
    total_cells = count * len(master_df)
    pct_missing = (100.0 * missing / total_cells) if total_cells > 0 else 0.0
    md_lines.append(f"| {src} | {count} | {missing} | {pct_missing:.2f}% |")

md_lines.append("")
md_lines.append("## 4. Feature Details")
md_lines.append("")

for src in sorted(sources.keys()):
    md_lines.append(f"### Source: `{src}`")
    md_lines.append(f"- **Features Count**: {sources[src]['count']}")
    
    # List a few sample features or list them in groups
    cols = sources[src]["cols"]
    md_lines.append("- **Feature Names Sample**:")
    for c in cols[:10]:
        missing_count = cols_stats[c]["missing_values"]
        md_lines.append(f"  - `{c}` (missing: {missing_count} rows)")
    if len(cols) > 10:
        md_lines.append(f"  - ... and {len(cols) - 10} more features")
    md_lines.append("")

with open(OUT_MD, "w") as f:
    f.write("\n".join(md_lines))
logger.info(f"Inventory MD saved to {OUT_MD}")

print("Master Feature Table Construction Script Finished!")
