#!/bin/bash
mkdir -p artifacts/sprint10j

echo "=================================================="
echo "SURYANET OPERATIONAL EVIDENCE TRACE AUDIT"
echo "Sprint 10J"
echo "=================================================="

echo
echo "=== PRE-FLIGHT ARTIFACT VERIFICATION ==="

FILES=(
"artifacts/backtest_window_predictions.csv"
"artifacts/research/test.parquet"
"artifacts/models/patchtst_best.pt"
"artifacts/calibrator.pkl"
"artifacts/operator_thresholds_validation_only.json"
"artifacts/explainability_examples.json"
)

for f in "${FILES[@]}"; do
    if [ -f "$f" ]; then
        echo
        echo "FOUND: $f"
        sha256sum "$f"
        stat "$f"
    else
        echo
        echo "MISSING: $f"
    fi
done

echo
echo "=== REPOSITORY FINGERPRINT ==="

find artifacts app scratch data_pipeline \
-type f \
-exec sha256sum {} \; \
| sort \
| sha256sum

echo
echo "=== CSV VALIDATION ==="

python3 - <<EOF
import pandas as pd
df=pd.read_csv("artifacts/backtest_window_predictions.csv",nrows=3)
print(df.columns.tolist())
print(len(pd.read_csv("artifacts/backtest_window_predictions.csv")))
print(df.iloc[0].to_dict())
EOF

echo
echo "=== SYSTEM MEMORY ==="

vm_stat || free -h

echo
echo "=== EXECUTING OPERATIONAL EVIDENCE AUDIT ==="

python3 scratch/sprint10j/run_evidence_chain.py \
2>&1 | tee artifacts/sprint10j/audit_log.txt

echo
echo "=== GENERATED ARTIFACTS ==="

find artifacts/sprint10j -type f

echo
echo "=== VERIFY CERTIFICATES ==="

python3 - <<EOF
import glob,json,os

required=[
"prediction_certificate",
"prediction_evidence",
"repository_fingerprint",
"artifact_hashes",
"execution_manifest"
]

for r in required:
    f=glob.glob(f"artifacts/sprint10j/{r}*")
    if f:
        print("PASS",r)
    else:
        print("FAIL",r)
EOF

echo
echo "=== FINAL INTEGRITY CHECK ==="

python3 - <<EOF
import glob,json

files=glob.glob("artifacts/sprint10j/prediction_certificate*.json")

if not files:
    print("AUDIT FAILED")
    raise SystemExit()

with open(files[-1]) as f:
    d=json.load(f)

print()

for k,v in d.items():
    print(k,":",v)

print()

if d.get("EvidenceChainComplete",False) or d.get("evidence_chain_complete",False):
    print("FINAL STATUS : PASS")
else:
    print("FINAL STATUS : FAIL")
EOF

echo
echo "Sprint 10J completed."
