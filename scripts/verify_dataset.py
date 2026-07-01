import os
import sys
import json
import pandas as pd

def main():
    print("==================================================")
    print("SuryaNet: Research-Grade Dataset Verifier")
    print("==================================================")
    
    research_dir = os.path.join("artifacts", "research")
    goes_full_path = os.path.join(research_dir, "goes_full.parquet")
    flares_full_path = os.path.join(research_dir, "flares_full.parquet")
    train_path = os.path.join(research_dir, "train.parquet")
    val_path = os.path.join(research_dir, "validation.parquet")
    test_path = os.path.join(research_dir, "test.parquet")
    
    # Check if files exist
    for p in [goes_full_path, flares_full_path, train_path, val_path, test_path]:
        if not os.path.exists(p):
            print(f"ERROR: Missing required parquet file: {p}")
            sys.exit(1)
            
    print("Loading Parquet datasets...")
    goes_df = pd.read_parquet(goes_full_path)
    flares_df = pd.read_parquet(flares_full_path)
    train_df = pd.read_parquet(train_path)
    val_df = pd.read_parquet(val_path)
    test_df = pd.read_parquet(test_path)
    
    # Ensure timestamps are parsed as datetime
    goes_df["timestamp"] = pd.to_datetime(goes_df["timestamp"])
    flares_df["start_time"] = pd.to_datetime(flares_df["start_time"])
    train_df["timestamp"] = pd.to_datetime(train_df["timestamp"])
    val_df["timestamp"] = pd.to_datetime(val_df["timestamp"])
    test_df["timestamp"] = pd.to_datetime(test_df["timestamp"])
    
    # 1. Record counts
    total_goes = len(goes_df)
    total_flares = len(flares_df)
    
    # M/X counts
    m_flares_df = flares_df[flares_df["flare_class"].str.startswith("M", na=False)]
    x_flares_df = flares_df[flares_df["flare_class"].str.startswith("X", na=False)]
    m_count = len(m_flares_df)
    x_count = len(x_flares_df)
    
    # Gap calculations
    min_time = goes_df["timestamp"].min()
    max_time = goes_df["timestamp"].max()
    expected_minutes = 0
    missing_minutes = 0
    gap_percentage = 0.0
    if total_goes > 0:
        delta = max_time - min_time
        expected_minutes = int(delta.total_seconds() / 60) + 1
        missing_minutes = max(0, expected_minutes - total_goes)
        gap_percentage = (missing_minutes / expected_minutes) * 100
        
    print(f"Total GOES Records: {total_goes:,}")
    print(f"Total Flare Events: {total_flares:,} (M: {m_count}, X: {x_count})")
    if total_goes > 0:
        print(f"Date Range:         {min_time} to {max_time}")
    print(f"Gap Percentage:     {gap_percentage:.4f}% ({missing_minutes:,} missing minutes)")
    
    # 2. Temporal Leakage Checks
    print("\nRunning Temporal Leakage Checks...")
    max_train_ts = train_df["timestamp"].max()
    min_val_ts = val_df["timestamp"].min()
    max_val_ts = val_df["timestamp"].max()
    min_test_ts = test_df["timestamp"].min()
    
    overlap_train_val = train_df["timestamp"].isin(val_df["timestamp"]).any()
    overlap_val_test = val_df["timestamp"].isin(test_df["timestamp"]).any()
    overlap_train_test = train_df["timestamp"].isin(test_df["timestamp"]).any()
    
    leakage_passed = True
    details = []
    
    if pd.notna(max_train_ts) and pd.notna(min_val_ts):
        if max_train_ts >= min_val_ts:
            leakage_passed = False
            details.append(f"Overlap detected: Train max timestamp ({max_train_ts}) >= Val min timestamp ({min_val_ts})")
        else:
            details.append("Train < Validation condition met.")
    else:
        details.append("Train or Validation timestamp is empty.")
        
    if pd.notna(max_val_ts) and pd.notna(min_test_ts):
        if max_val_ts >= min_test_ts:
            leakage_passed = False
            details.append(f"Overlap detected: Val max timestamp ({max_val_ts}) >= Test min timestamp ({min_test_ts})")
        else:
            details.append("Validation < Test condition met.")
    else:
        details.append("Validation or Test timestamp is empty.")
        
    if overlap_train_val or overlap_val_test or overlap_train_test:
        leakage_passed = False
        details.append("Duplicate timestamps found across splits.")
    else:
        details.append("No duplicate timestamps across splits.")
        
    if leakage_passed:
        print("✅ SUCCESS: No temporal leakage detected.")
    else:
        print("❌ FAILURE: Temporal leakage detected!")
        for d in details:
            print(f"  - {d}")
            
    # 3. Solar Cycle Distributions
    print("\nComputing Solar Cycle Distributions...")
    # SC24: 2010-01-01 to 2019-12-31
    # SC25: 2020-01-01 to Present
    
    sc24_goes = goes_df[(goes_df["timestamp"] >= "2010-01-01") & (goes_df["timestamp"] <= "2019-12-31 23:59:59")]
    sc25_goes = goes_df[(goes_df["timestamp"] >= "2020-01-01")]
    
    sc24_flares = flares_df[(flares_df["start_time"] >= "2010-01-01") & (flares_df["start_time"] <= "2019-12-31 23:59:59")]
    sc25_flares = flares_df[(flares_df["start_time"] >= "2020-01-01")]
    
    sc24_m = len(sc24_flares[sc24_flares["flare_class"].str.startswith("M", na=False)])
    sc24_x = len(sc24_flares[sc24_flares["flare_class"].str.startswith("X", na=False)])
    
    sc25_m = len(sc25_flares[sc25_flares["flare_class"].str.startswith("M", na=False)])
    sc25_x = len(sc25_flares[sc25_flares["flare_class"].str.startswith("X", na=False)])
    
    solar_cycle_dist = {
        "SC24": {
            "records": len(sc24_goes),
            "M": sc24_m,
            "X": sc24_x
        },
        "SC25": {
            "records": len(sc25_goes),
            "M": sc25_m,
            "X": sc25_x
        }
    }
    
    print(f"Solar Cycle 24 (2010-2019): GOES Records: {len(sc24_goes):,}, M: {sc24_m}, X: {sc24_x}")
    print(f"Solar Cycle 25 (2020-Pres): GOES Records: {len(sc25_goes):,}, M: {sc25_m}, X: {sc25_x}")
    
    # 4. Yearly distributions
    print("\nComputing Yearly Distributions...")
    goes_df["year"] = goes_df["timestamp"].dt.year
    goes_yearly = goes_df.groupby("year").size().to_dict()
    
    flares_df["year"] = flares_df["start_time"].dt.year
    flares_yearly = flares_df.groupby("year").size().to_dict()
    flares_m_yearly = flares_df[flares_df["flare_class"].str.startswith("M", na=False)].groupby("year").size().to_dict()
    flares_x_yearly = flares_df[flares_df["flare_class"].str.startswith("X", na=False)].groupby("year").size().to_dict()
    
    yearly_dist = {}
    all_years = sorted(list(set(list(goes_yearly.keys()) + list(flares_yearly.keys()))))
    for y in all_years:
        yearly_dist[str(y)] = {
            "goes_records": goes_yearly.get(y, 0),
            "total_flares": flares_yearly.get(y, 0),
            "M_flares": flares_m_yearly.get(y, 0),
            "X_flares": flares_x_yearly.get(y, 0)
        }
        print(f"  Year {y}: GOES Records: {goes_yearly.get(y, 0):,}, Flares: {flares_yearly.get(y, 0):,} (M: {flares_m_yearly.get(y, 0)}, X: {flares_x_yearly.get(y, 0)})")
        
    # 5. Verify Success Criteria
    print("\nVerifying Success Criteria...")
    goes_records_ok = total_goes >= 5000000
    m_flares_ok = m_count >= 500
    x_flares_ok = x_count >= 50
    gap_ok = gap_percentage < 2.0
    
    criteria_passed = goes_records_ok and m_flares_ok and x_flares_ok and gap_ok and leakage_passed
    
    print(f"  - GOES Records >= 5,000,000:  {'✅' if goes_records_ok else '❌'} ({total_goes:,})")
    print(f"  - M-class Flares >= 500:      {'✅' if m_flares_ok else '❌'} ({m_count})")
    print(f"  - X-class Flares >= 50:       {'✅' if x_flares_ok else '❌'} ({x_count})")
    print(f"  - Gap Percentage < 2.0%:      {'✅' if gap_ok else '❌'} ({gap_percentage:.4f}%)")
    print(f"  - No Temporal Leakage:        {'✅' if leakage_passed else '❌'}")
    
    if criteria_passed:
        print("\n🎉 SUCCESS: All research-grade dataset criteria met.")
    else:
        print("\n🚨 FAILURE: One or more criteria did not meet the required threshold.")
        
    # 6. Save JSON report
    report = {
        "goes_records": total_goes,
        "flare_records": total_flares,
        "m_class_count": m_count,
        "x_class_count": x_count,
        "date_range": {
            "start": min_time.isoformat() if min_time else None,
            "end": max_time.isoformat() if max_time else None
        },
        "missing_minutes": missing_minutes,
        "gap_percentage": gap_percentage,
        "solar_cycle_distribution": solar_cycle_dist,
        "yearly_distribution": yearly_dist,
        "temporal_leakage_checks": {
            "passed": leakage_passed,
            "details": details
        },
        "criteria_check": {
            "passed": criteria_passed,
            "goes_records_ok": goes_records_ok,
            "m_flares_ok": m_flares_ok,
            "x_flares_ok": x_flares_ok,
            "gap_ok": gap_ok
        }
    }
    
    os.makedirs("artifacts", exist_ok=True)
    report_path = os.path.join("artifacts", "research_dataset_report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Saved report summary to {report_path}")
    
    if not criteria_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
