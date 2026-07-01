import json
import os

files = [
    "generalization_fold_results.json",
    "generalization_stability.json",
    "generalization_sign_consistency.json",
    "generalization_ci.json",
    "generalization_operator_ranking.json",
    "temporal_generalization_audit.json"
]

dir_path = "/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1"

for f_name in files:
    path = os.path.join(dir_path, f_name)
    if not os.path.exists(path):
        print(f"File {f_name} does not exist!")
        continue
    try:
        with open(path, "r") as fh:
            data = json.load(fh)
        print(f"\n=== {f_name} ===")
        if isinstance(data, dict):
            print(f"Keys: {list(data.keys())}")
            # print first level of structures
            for k in list(data.keys())[:3]:
                val = data[k]
                if isinstance(val, dict):
                    print(f"  {k} keys: {list(val.keys())}")
                else:
                    print(f"  {k}: {type(val)}")
        elif isinstance(data, list):
            print(f"Length: {len(data)}")
            if len(data) > 0:
                print(f"First element: {data[0]}")
    except Exception as e:
        print(f"Error reading {f_name}: {e}")
