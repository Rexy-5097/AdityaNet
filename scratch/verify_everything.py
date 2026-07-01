import os
import glob
import pandas as pd
import json
import sqlite3
import numpy as np

results = {}

# A. Downloaded scientific data
hel1os_files = glob.glob("/Users/soumyadebtripathy/AdityaNet/data/aditya_l1/raw/hel1os/*.fits")
solexs_files = glob.glob("/Users/soumyadebtripathy/AdityaNet/data/aditya_l1/raw/solexs/*.fits")

results["A_scientific_data"] = {
    "archive_counts": {
        "hel1os_raw_fits_count": len(hel1os_files),
        "solexs_raw_fits_count": len(solexs_files)
    }
}

# Let's count manifest entries
manifest_db_path = "/Users/soumyadebtripathy/AdityaNet/data_pipeline/datasets/dataset_v1/database/manifest.db" # typical path from README
# Let's look for all manifest.db files
db_paths = glob.glob("/Users/soumyadebtripathy/AdityaNet/**/manifest.db", recursive=True)
results["A_scientific_data"]["manifest_db_files"] = db_paths

for db_p in db_paths:
    db_name = os.path.basename(os.path.dirname(db_p)) + "_" + os.path.basename(db_p)
    try:
        conn = sqlite3.connect(db_p)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cursor.fetchall()]
        db_info = {"tables": tables}
        for t in tables:
            cursor.execute(f"SELECT count(*) FROM {t}")
            cnt = cursor.fetchone()[0]
            db_info[f"count_{t}"] = cnt
        results["A_scientific_data"][f"db_{db_name}"] = db_info
        conn.close()
    except Exception as e:
        results["A_scientific_data"][f"db_{db_name}_error"] = str(e)

# Let's also check the manifest count in artifacts/aditya_l1/download_manifest.json
download_manifest_path = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/download_manifest.json"
if os.path.exists(download_manifest_path):
    with open(download_manifest_path, 'r') as f:
        data = json.load(f)
    results["A_scientific_data"]["download_manifest_json"] = {
        "HEL1OS_entries": len(data.get("HEL1OS", {})),
        "SoLEXS_entries": len(data.get("SoLEXS", {}))
    }

# Checksums: count the number of .sha256 files or entries in manifest
sha256_files = glob.glob("/Users/soumyadebtripathy/AdityaNet/**/*.sha256", recursive=True)
results["A_scientific_data"]["checksum_files_count"] = len(sha256_files)

# Observation dates: let's query the min/max dates from manifest database or from the files
# For hel1os and solexs raw fits, get start/end dates from file names
hel1os_dates = sorted([os.path.basename(f).split('_')[3].split('.')[0] for f in hel1os_files if len(os.path.basename(f).split('_')) >= 4])
solexs_dates = sorted([os.path.basename(f).split('_')[3].split('.')[0] for f in solexs_files if len(os.path.basename(f).split('_')) >= 4])
results["A_scientific_data"]["file_observation_dates"] = {
    "hel1os_min": hel1os_dates[0] if hel1os_dates else "None",
    "hel1os_max": hel1os_dates[-1] if hel1os_dates else "None",
    "solexs_min": solexs_dates[0] if solexs_dates else "None",
    "solexs_max": solexs_dates[-1] if solexs_dates else "None",
}

# Metadata tables
# Check if database has fits metadata table
# Let's query metadata from database if exists
# Usually in manifest.db or another db
# Let's check all sqlite db files in workspace
sqlite_files = glob.glob("/Users/soumyadebtripathy/AdityaNet/**/*.db", recursive=True)
results["A_scientific_data"]["sqlite_files"] = sqlite_files


# B. Feature engineering
# Let's check feature_dataset.parquet and master_feature_table.parquet and overlap_dataset.parquet
results["B_feature_engineering"] = {}
for p_name, p_path in [
    ("feature_dataset", "/Users/soumyadebtripathy/AdityaNet/artifacts/feature_dataset.parquet"),
    ("master_feature_table", "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/master_feature_table.parquet"),
    ("overlap_dataset", "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/overlap_dataset.parquet"),
    ("compressed_solexs_features", "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/compressed_solexs_features.parquet")
]:
    if os.path.exists(p_path):
        try:
            df = pd.read_parquet(p_path)
            results["B_feature_engineering"][p_name] = {
                "shape": df.shape,
                "columns": df.columns.tolist()[:15],
                "timestamp_cols": [c for c in df.columns if 'time' in c.lower()],
                "features_count": len(df.columns)
            }
        except Exception as e:
            results["B_feature_engineering"][p_name] = {"error": str(e)}
    else:
        results["B_feature_engineering"][p_name] = "Not found"

# Normalization artifacts: search for min, max, mean, std, scaler, calibrator files
# Let's check calibrator.pkl size and type, and look for files with "scaler" or "normaliz"
scaler_files = glob.glob("/Users/soumyadebtripathy/AdityaNet/**/*scaler*", recursive=True) + \
               glob.glob("/Users/soumyadebtripathy/AdityaNet/**/*normalization*", recursive=True) + \
               glob.glob("/Users/soumyadebtripathy/AdityaNet/**/*.pkl", recursive=True)
results["B_feature_engineering"]["scaler_and_pkl_files"] = [f for f in scaler_files if "venv" not in f]


# C. Labels
# Training, validation, testing labels: check target_6hr_binary counts in train.parquet, validation.parquet, test.parquet
results["C_labels"] = {}
for split_name, split_path in [
    ("train", "/Users/soumyadebtripathy/AdityaNet/artifacts/research/train.parquet"),
    ("validation", "/Users/soumyadebtripathy/AdityaNet/artifacts/research/validation.parquet"),
    ("test", "/Users/soumyadebtripathy/AdityaNet/artifacts/research/test.parquet")
]:
    if os.path.exists(split_path):
        try:
            df = pd.read_parquet(split_path, columns=["timestamp", "target_6hr_binary"])
            binary_counts = df["target_6hr_binary"].value_counts().to_dict()
            results["C_labels"][split_name] = {
                "total_rows": len(df),
                "min_timestamp": str(df["timestamp"].min()),
                "max_timestamp": str(df["timestamp"].max()),
                "positive_count": int(binary_counts.get(1.0, binary_counts.get(1, 0))),
                "negative_count": int(binary_counts.get(0.0, binary_counts.get(0, 0)))
            }
        except Exception as e:
            results["C_labels"][split_name] = {"error": str(e)}
    else:
        results["C_labels"][split_name] = "Not found"

# Forecast horizons: let's see where horizons are defined in training scripts or config
# Check app/services/ml/dataset.py or scripts/train_patchtst.py or scripts/train_baseline.py
# Let's find files that mention forecast horizon or target_6hr_binary


# D. Models
# Checkpoint files
results["D_models"] = {}
checkpoint_files = glob.glob("/Users/soumyadebtripathy/AdityaNet/artifacts/**/*.pt", recursive=True) + \
                   glob.glob("/Users/soumyadebtripathy/AdityaNet/artifacts/**/*.pth", recursive=True) + \
                   glob.glob("/Users/soumyadebtripathy/AdityaNet/artifacts/**/*.ckpt", recursive=True)
results["D_models"]["checkpoint_files"] = [f for f in checkpoint_files if "venv" not in f]

# Training scripts
training_scripts = glob.glob("/Users/soumyadebtripathy/AdityaNet/**/train*.py", recursive=True)
results["D_models"]["training_scripts"] = [f for f in training_scripts if "venv" not in f]

# Calibration files
calib_files = glob.glob("/Users/soumyadebtripathy/AdityaNet/**/*calibration*", recursive=True) + \
              glob.glob("/Users/soumyadebtripathy/AdityaNet/**/*calibrator*", recursive=True)
results["D_models"]["calibration_files"] = [f for f in calib_files if "venv" not in f]

# Training history
history_files = glob.glob("/Users/soumyadebtripathy/AdityaNet/**/training_history*", recursive=True) + \
                glob.glob("/Users/soumyadebtripathy/AdityaNet/**/*history*.json", recursive=True)
results["D_models"]["history_files"] = [f for f in history_files if "venv" not in f]

# Let's check baseline_metrics.json and test_metrics.json and training_history.json
for f_path in [
    "/Users/soumyadebtripathy/AdityaNet/artifacts/baseline_metrics.json",
    "/Users/soumyadebtripathy/AdityaNet/artifacts/test_metrics.json",
    "/Users/soumyadebtripathy/AdityaNet/artifacts/training_history.json",
    "/Users/soumyadebtripathy/AdityaNet/artifacts/evaluation_audit_report.json"
]:
    if os.path.exists(f_path):
        try:
            with open(f_path, 'r') as f:
                results["D_models"][os.path.basename(f_path)] = json.load(f)
        except Exception as e:
            results["D_models"][os.path.basename(f_path)] = {"error": str(e)}


# E. Operator components
# Check decision engine, alert logic, explainability, confidence scoring
# Let's search scripts and app folders for operator-related files
results["E_operator"] = {}
operator_files = glob.glob("/Users/soumyadebtripathy/AdityaNet/**/operator*", recursive=True) + \
                 glob.glob("/Users/soumyadebtripathy/AdityaNet/**/alert*", recursive=True) + \
                 glob.glob("/Users/soumyadebtripathy/AdityaNet/**/explain*", recursive=True) + \
                 glob.glob("/Users/soumyadebtripathy/AdityaNet/**/decision*", recursive=True)
results["E_operator"]["operator_and_alert_files"] = [f for f in operator_files if "venv" not in f]

# Let's read operational_thresholds.json, operator_thresholds.json, operator_thresholds_validation_only.json, operator_readiness_report.json
for f_path in [
    "/Users/soumyadebtripathy/AdityaNet/artifacts/operational_thresholds.json",
    "/Users/soumyadebtripathy/AdityaNet/artifacts/operator_thresholds.json",
    "/Users/soumyadebtripathy/AdityaNet/artifacts/operator_thresholds_validation_only.json",
    "/Users/soumyadebtripathy/AdityaNet/artifacts/operator_readiness_report.json",
    "/Users/soumyadebtripathy/AdityaNet/artifacts/operator_backtest.json",
    "/Users/soumyadebtripathy/AdityaNet/artifacts/operator_trust_projection.json",
    "/Users/soumyadebtripathy/AdityaNet/artifacts/operator_trust_audit.json"
]:
    if os.path.exists(f_path):
        try:
            with open(f_path, 'r') as f:
                results["E_operator"][os.path.basename(f_path)] = json.load(f)
        except Exception as e:
            results["E_operator"][os.path.basename(f_path)] = {"error": str(e)}

# F. Generated reports
# Check reports in artifacts directory
report_md_files = glob.glob("/Users/soumyadebtripathy/AdityaNet/artifacts/**/*.md", recursive=True)
results["F_reports"] = {
    "report_md_files": report_md_files,
    "timestamps": {}
}
for r in report_md_files:
    try:
        mtime = os.path.getmtime(r)
        results["F_reports"]["timestamps"][os.path.basename(r)] = mtime
    except Exception as e:
        results["F_reports"]["timestamps"][os.path.basename(r)] = str(e)


# Write to output file
with open("/Users/soumyadebtripathy/AdityaNet/scratch/verify_results.json", "w") as f:
    json.dump(results, f, indent=2)

print("Verification data collection complete. Written to scratch/verify_results.json.")
