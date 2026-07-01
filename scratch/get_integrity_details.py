import json

with open("scratch/verification_checklist_results.json", "r") as f:
    data = json.load(f)

# Integrity is the last section, let's find it
integrity = data.get("G. Repository integrity", [])[0]["value"]

print("DUPLICATE FILENAMES:")
for name, paths in integrity["duplicate_filenames"].items():
    print(f"  - {name}: {paths}")

print("\nMISSING REFERENCED FILES:")
for ref in integrity["missing_referenced_files"]:
    print(f"  - {ref}")
