import os
import pandas as pd
import glob
import numpy as np

def analyze_goes():
    print("Analyzing GOES...")
    df = pd.read_parquet("artifacts/research/goes_full.parquet")
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    first_ts = df['timestamp'].min()
    last_ts = df['timestamp'].max()
    count = len(df)
    
    # Calculate cadence: diff of timestamps
    diffs = df['timestamp'].sort_values().diff()
    median_cadence = diffs.median()
    
    print(f"GOES: First={first_ts}, Last={last_ts}, Count={count}, Cadence={median_cadence}")
    return {
        "first_timestamp": str(first_ts),
        "last_timestamp": str(last_ts),
        "cadence_seconds": median_cadence.total_seconds(),
        "total_observations": count,
        "parquet_count": 1
    }

def analyze_instrument(name, directory_pattern):
    print(f"Analyzing {name}...")
    files = sorted(glob.glob(directory_pattern))
    if not files:
        print(f"No files found for {name} in {directory_pattern}")
        return None
    
    first_timestamps = []
    last_timestamps = []
    total_obs = 0
    
    # We can sample files or read all if quick. Let's read all first/last/count per file.
    all_timestamps = []
    
    for f in files:
        df = pd.read_parquet(f, columns=["timestamp"])
        if len(df) == 0:
            continue
        ts = pd.to_datetime(df["timestamp"])
        first_timestamps.append(ts.min())
        last_timestamps.append(ts.max())
        total_obs += len(df)
        # To calculate exact cadence and missing intervals, let's keep all timestamps
        all_timestamps.extend(ts.tolist())
        
    all_timestamps = pd.Series(all_timestamps).sort_values()
    
    first_ts = all_timestamps.min()
    last_ts = all_timestamps.max()
    
    # Cadence
    diffs = all_timestamps.diff()
    median_cadence = diffs.median()
    
    # Find gaps (missing intervals) - let's define a gap as > 5 times the median cadence
    gap_limit = 5 * median_cadence
    gaps = diffs[diffs > gap_limit]
    
    missing_intervals = []
    for idx in gaps.index:
        gap_start = all_timestamps.iloc[idx - 1]
        gap_end = all_timestamps.iloc[idx]
        gap_duration = (gap_end - gap_start).total_seconds()
        missing_intervals.append({
            "start": str(gap_start),
            "end": str(gap_end),
            "duration_seconds": gap_duration
        })
        
    print(f"{name}: First={first_ts}, Last={last_ts}, Count={total_obs}, Cadence={median_cadence}, Gaps={len(missing_intervals)}")
    
    return {
        "first_timestamp": str(first_ts),
        "last_timestamp": str(last_ts),
        "cadence_seconds": median_cadence.total_seconds() if not pd.isna(median_cadence) else None,
        "total_observations": total_obs,
        "parquet_count": len(files),
        "missing_intervals": missing_intervals,
        "timestamps": all_timestamps
    }

def main():
    goes_stats = analyze_goes()
    solexs_stats = analyze_instrument("SoLEXS", "data/aditya_l1/processed/solexs/*.parquet")
    hel1os_stats = analyze_instrument("HEL1OS", "data/aditya_l1/processed/hel1os/*.parquet")
    
    # Overlap analysis
    goes_first = pd.to_datetime(goes_stats["first_timestamp"])
    goes_last = pd.to_datetime(goes_stats["last_timestamp"])
    
    solexs_first = pd.to_datetime(solexs_stats["first_timestamp"])
    solexs_last = pd.to_datetime(solexs_stats["last_timestamp"])
    
    hel1os_first = pd.to_datetime(hel1os_stats["first_timestamp"])
    hel1os_last = pd.to_datetime(hel1os_stats["last_timestamp"])
    
    overlap_start = max(goes_first, solexs_first, hel1os_first)
    overlap_end = min(goes_last, solexs_last, hel1os_last)
    
    overlap_duration_sec = (overlap_end - overlap_start).total_seconds()
    
    # Calculate duration for each instrument
    goes_dur = (goes_last - goes_first).total_seconds()
    solexs_dur = (solexs_last - solexs_first).total_seconds()
    hel1os_dur = (hel1os_last - hel1os_first).total_seconds()
    
    overlap_pct_goes = (overlap_duration_sec / goes_dur) * 100 if goes_dur > 0 else 0
    overlap_pct_solexs = (overlap_duration_sec / solexs_dur) * 100 if solexs_dur > 0 else 0
    overlap_pct_hel1os = (overlap_duration_sec / hel1os_dur) * 100 if hel1os_dur > 0 else 0
    
    # Create final json structure
    overlap_report = {
        "instruments": {
            "goes": {
                "first_timestamp": goes_stats["first_timestamp"],
                "last_timestamp": goes_stats["last_timestamp"],
                "cadence": f"{goes_stats['cadence_seconds']} seconds",
                "missing_intervals_count": 0,
                "total_observations": goes_stats["total_observations"],
                "processed_parquet_count": goes_stats["parquet_count"]
            },
            "solexs": {
                "first_timestamp": solexs_stats["first_timestamp"],
                "last_timestamp": solexs_stats["last_timestamp"],
                "cadence": f"{solexs_stats['cadence_seconds']} seconds",
                "missing_intervals_count": len(solexs_stats["missing_intervals"]),
                "total_observations": solexs_stats["total_observations"],
                "processed_parquet_count": solexs_stats["parquet_count"]
            },
            "hel1os": {
                "first_timestamp": hel1os_stats["first_timestamp"],
                "last_timestamp": hel1os_stats["last_timestamp"],
                "cadence": f"{hel1os_stats['cadence_seconds']} seconds",
                "missing_intervals_count": len(hel1os_stats["missing_intervals"]),
                "total_observations": hel1os_stats["total_observations"],
                "processed_parquet_count": hel1os_stats["parquet_count"]
            }
        },
        "common_overlap": {
            "common_overlap_start": str(overlap_start),
            "common_overlap_end": str(overlap_end),
            "overlap_duration_seconds": overlap_duration_sec,
            "overlap_duration_days": overlap_duration_sec / 86400.0,
            "overlap_percentage_relative_to_goes": overlap_pct_goes,
            "overlap_percentage_relative_to_solexs": overlap_pct_solexs,
            "overlap_percentage_relative_to_hel1os": overlap_pct_hel1os
        }
    }
    
    # Let's save a detailed report (without full list of gaps if too large, we can output count or top gaps)
    print("Overlap Start:", overlap_start)
    print("Overlap End:", overlap_end)
    print("Overlap Days:", overlap_duration_sec / 86400.0)
    
    import json
    # Let's save this json
    os.makedirs("artifacts/sprint11b", exist_ok=True)
    with open("artifacts/sprint11b/multi_instrument_overlap.json", "w") as f:
        json.dump(overlap_report, f, indent=2)
    print("Saved report to artifacts/sprint11b/multi_instrument_overlap.json")

if __name__ == "__main__":
    main()
