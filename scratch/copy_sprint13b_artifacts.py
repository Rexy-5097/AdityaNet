import shutil
import os

src_dir = "artifacts/sprint13"
dest_dir = "/Users/soumyadebtripathy/.gemini/antigravity-cli/brain/250595dc-cae6-4c3d-b6ef-612c61f56443"

files = [
    "scientific_pipeline_audit.md",
    "metrics_consistency_report.json",
    "visualization_validation.json",
    "publication_readiness_report.md",
    "final_scientific_verdict.json"
]

for f in files:
    src_path = os.path.join(src_dir, f)
    dest_path = os.path.join(dest_dir, f)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"Copied {f} to {dest_path}")
    else:
        print(f"Error: {f} not found in source!")
