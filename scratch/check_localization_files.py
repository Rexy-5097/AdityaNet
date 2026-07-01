import os
import json

filenames = [
    "raw_channel_generalization.json",
    "physical_band_generalization.json",
    "compression_generalization.json",
    "localization_vs_incremental.json",
    "localization_stability.json",
    "localization_ci.json",
    "localization_spread_sign_audit.json",
    "raw_channel_rankings.json",
    "localization_rankings.json",
    "signal_localization_audit.json",
    "signal_localization_audit.md"
]

dir_path = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1"

for f in filenames:
    path = os.path.join(dir_path, f)
    exists = os.path.exists(path)
    print(f"File: {f} -> Exists: {exists}")
    if exists:
        try:
            if f.endswith(".json"):
                with open(path, "r") as fh:
                    data = json.load(fh)
                print(f"  Parsed JSON successfully. Keys: {list(data.keys())[:3] if isinstance(data, dict) else len(data)}")
            else:
                with open(path, "r") as fh:
                    content = fh.read()
                print(f"  Read text file successfully. Length: {len(content)}")
        except Exception as e:
            print(f"  Error reading: {e}")
