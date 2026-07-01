import json

with open("/Users/soumyadebtripathy/AdityaNet/artifacts/aditya_l1/temporal_generalization_audit.json", "r") as f:
    data = json.load(f)

print("Metadata keys and values:")
for k, v in data["metadata"].items():
    print(f"  {k}: {v}")

print("\nGeneralization Fold Results:")
for fold, val in data["generalization_fold_results"].items():
    print(f"  {fold}: degenerate={val['degenerate']}, train_days={val['train_days']}, test_days={val['test_days']}")
