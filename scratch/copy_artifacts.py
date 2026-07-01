import shutil
import os

src_dir = "artifacts/sprint12b"
dest_dir = "/Users/soumyadebtripathy/.gemini/antigravity-cli/brain/250595dc-cae6-4c3d-b6ef-612c61f56443"

files = [
    "training_pipeline_v2_report.md",
    "optimizer_validation.json",
    "gradient_flow_report.json",
    "reproducibility_certificate_v2.json",
    "checkpoint_validation.json",
    "calibration_certificate.json",
    "training_readiness_certificate.json"
]

for f in files:
    src_path = os.path.join(src_dir, f)
    dest_path = os.path.join(dest_dir, f)
    if os.path.exists(src_path):
        shutil.copy2(src_path, dest_path)
        print(f"Copied {f} to {dest_path}")
    else:
        print(f"Error: {f} not found in source!")
