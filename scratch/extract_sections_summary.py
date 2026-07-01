import json

with open("scratch/extracted_json_values.json", "r") as f:
    data = json.load(f)

# We want to print summaries of keys
for main_key, val in data.items():
    print("="*40)
    print(f"KEY: {main_key}")
    if isinstance(val, dict):
        for sub_key, sub_val in val.items():
            if sub_key in ["section_7_daily_coverage_table", "audit_records", "verifications", "evidence", "report_md_files", "sqlite_files", "manifest_db_files", "checkpoint_files", "training_scripts", "calibration_files", "history_files", "operator_and_alert_files"]:
                print(f"  {sub_key}: [Truncated {len(sub_val)} items]")
            elif isinstance(sub_val, (dict, list)):
                print(f"  {sub_key}: {str(sub_val)[:300]}...")
            else:
                print(f"  {sub_key}: {sub_val}")
    elif isinstance(val, list):
        print(f"  [List of {len(val)} items, first element: {val[0] if val else None}]")
    else:
        print(f"  {val}")
