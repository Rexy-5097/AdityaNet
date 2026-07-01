import shutil
import os

src_dir = "artifacts/sprint14b"
dest_dir = "/Users/soumyadebtripathy/.gemini/antigravity-cli/brain/250595dc-cae6-4c3d-b6ef-612c61f56443"

os.makedirs(dest_dir, exist_ok=True)

# Files to copy
files = [
    "training_history.csv",
    "convergence_report.md",
    "ablation_study.md",
    "attention_analysis.md",
    "threshold_analysis.md",
    "publication_results.md",
    "final_scientific_verdict.md",
    "publication_readiness_certificate.json"
]

for f in files:
    src_path = os.path.join(src_dir, f)
    dest_path = os.path.join(dest_dir, f)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"✓ Copied {f} to {dest_path}")
    else:
        print(f"✗ Warning: {f} not found in source!")

# Directories to copy
dirs = [
    "publication_figures",
    "publication_tables"
]

for d in dirs:
    src_path = os.path.join(src_dir, d)
    dest_path = os.path.join(dest_dir, d)
    if os.path.exists(src_path):
        if os.path.exists(dest_path):
            shutil.rmtree(dest_path)
        shutil.copytree(src_path, dest_path)
        print(f"✓ Copied directory {d} to {dest_path}")
    else:
        print(f"✗ Warning: Directory {d} not found in source!")
