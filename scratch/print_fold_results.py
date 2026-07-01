import json

with open("/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/generalization_fold_results.json", "r") as f:
    data = json.load(f)

for fold_name, fold_data in data.items():
    print(f"Fold: {fold_name}")
    print(f"  train_days: {fold_data.get('train_days')}")
    print(f"  test_days: {fold_data.get('test_days')}")
    print(f"  degenerate: {fold_data.get('degenerate')}")
    print(f"  metrics keys: {list(fold_data.get('metrics', {}).keys())}")
