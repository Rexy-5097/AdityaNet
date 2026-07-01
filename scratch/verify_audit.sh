#!/bin/bash
SEP="════════════════════════════════════════════"

# ── V1: PARAMETER COUNTS ─────────────────────────────────────────────────────
echo "$SEP"
echo "PARAMETER COUNT: V3 Seed 42 Checkpoint"
echo "$SEP"

python3 - << 'EOF'
import torch, os

paths = [
    "artifacts/sprint14b/model_seed_42_best_tss.pt",
    "artifacts/sprint14b/stage1_seed_42_pretrained.pt",
]
for path in paths:
    if not os.path.exists(path):
        print(f"NOT FOUND: {path}")
        continue
    ck = torch.load(path, map_location="cpu", weights_only=True)
    state = ck.get("model_state_dict", ck.get("model", ck)) if isinstance(ck, dict) else ck
    total = sum(p.numel() for p in state.values() if hasattr(p, "numel"))
    print(f"\n{path}:")
    print(f"  PARAMETER_COUNT: {total:,}")
    print(f"  CHECKPOINT_KEYS: {list(ck.keys()) if isinstance(ck, dict) else 'raw_state_dict'}")
    print(f"  FIRST_10_LAYER_NAMES: {sorted(state.keys())[:10]}")
    
    # Extract n_layers from layer names
    import re
    layer_nums = set()
    for k in state.keys():
        m = re.findall(r'\.(\d+)\.', k)
        for n in m:
            layer_nums.add(int(n))
    if layer_nums:
        print(f"  MAX_LAYER_INDEX_FOUND: {max(layer_nums)}")
        print(f"  ALL_LAYER_INDICES: {sorted(layer_nums)}")
EOF

echo ""
echo "$SEP"
echo "PARAMETER COUNT: V1 Production Checkpoint"
echo "$SEP"

python3 - << 'EOF'
import torch, os, re

path = "artifacts/models/patchtsk_best.pt"
for p in ["artifacts/models/patchtst_best.pt", "artifacts/models/patchtsk_best.pt"]:
    if os.path.exists(p):
        path = p
        break

if not os.path.exists(path):
    print(f"NOT FOUND: {path}")
else:
    ck = torch.load(path, map_location="cpu", weights_only=True)
    state = ck.get("model_state_dict", ck.get("model", ck)) if isinstance(ck, dict) else ck
    total = sum(p.numel() for p in state.values() if hasattr(p, "numel"))
    print(f"V1 path: {path}")
    print(f"V1 PARAMETER_COUNT: {total:,}")
    print(f"V1 FIRST_10_LAYER_NAMES: {sorted(state.keys())[:10]}")
    layer_nums = set()
    for k in state.keys():
        for n in re.findall(r'\.(\d+)\.', k):
            layer_nums.add(int(n))
    if layer_nums:
        print(f"V1 MAX_LAYER_INDEX: {max(layer_nums)}")
        print(f"V1 ALL_LAYER_INDICES: {sorted(layer_nums)}")
EOF

# ── V2: WINDOW COUNT IN EVALUATION ───────────────────────────────────────────
echo "$SEP"
echo "EVALUATION WINDOW COUNT CHECK"
echo "$SEP"

echo "--- stride/window lines in eval_seed_42.py ---"
find . -name "eval_seed_42*" 2>/dev/null | head -5
grep -n -i "stride\|window\|arange\|30106\|261455\|262480\|indices\|dataset" \
    scratch/eval_seed_42.py 2>/dev/null \
    || find . -name "eval_seed_42*" -exec grep -n -i \
       "stride\|window\|arange\|30106\|261455\|indices" {} \; 2>/dev/null \
    || echo "eval_seed_42.py NOT FOUND"

# ── V3: SPRINT 14B ARTIFACT INVENTORY ────────────────────────────────────────
echo "$SEP"
echo "SPRINT 14B ARTIFACT INVENTORY"
echo "$SEP"

ls -lah artifacts/sprint14b/ 2>/dev/null || echo "DIRECTORY NOT FOUND"

echo ""
echo "--- JSON files ---"
for f in artifacts/sprint14b/*.json; do
    [ -f "$f" ] || continue
    echo ""
    echo "=== $f ==="
    cat "$f"
done

echo ""
echo "--- CSV files ---"
python3 - << 'EOF'
import pandas as pd, glob, os
for path in glob.glob("artifacts/sprint14b/*.csv"):
    df = pd.read_csv(path)
    print(f"\n{path}:")
    print(f"  ROW_COUNT: {len(df)}")
    print(f"  COLUMNS: {list(df.columns)}")
    # Check for confusion matrix totals
    for col_tp in ['TP','tp','true_positive']:
        if col_tp in df.columns:
            row = df.iloc[0]
            tp = row.get('TP', row.get('tp', 0))
            fp = row.get('FP', row.get('fp', 0))
            fn = row.get('FN', row.get('fn', 0))
            tn = row.get('TN', row.get('tn', 0))
            print(f"  WINDOW_TOTAL: {tp+fp+fn+tn}")
            break
EOF

# ── V4: LOSS FUNCTION COMPARISON ─────────────────────────────────────────────
echo "$SEP"
echo "LOSS FUNCTION — V3 TRAINING SCRIPT"
echo "$SEP"

grep -n -i "focal\|bce\|cross_entropy\|criterion\|loss_fn\|gamma\|alpha\|weight" \
    run_sprint14b_training_v2.py 2>/dev/null \
    || find . -name "run_sprint14b*" -exec grep -n -i \
       "focal\|bce\|criterion\|gamma\|alpha" {} \; 2>/dev/null \
    || echo "Sprint14B training script NOT FOUND"

echo ""
echo "--- Loss function in V1 training ---"
grep -n -i "focal\|bce\|cross_entropy\|criterion\|loss_fn\|gamma\|alpha" \
    app/services/ml/trainer.py 2>/dev/null \
    || grep -rn "FocalLoss\|BCELoss\|criterion" \
       app/services/ml/ --include="*.py" 2>/dev/null | head -20

# ── V5: STAGE 2 SPLIT BOUNDARIES ─────────────────────────────────────────────
echo "$SEP"
echo "STAGE 2 SPLIT DATE BOUNDARIES"
echo "$SEP"

grep -rn "2023-12-13\|2025-06-14\|2025-06-15\|2025-12-14\|2025-12-15\|2026-06-14" \
    . --include="*.py" --include="*.json" 2>/dev/null \
    | grep -v "__pycache__" | head -30

echo ""
echo "--- Stage 2 parquet files ---"
python3 - << 'EOF'
import pandas as pd, os, glob

patterns = [
    "data/**/*train_v3*",
    "data/**/*validation_v3*",
    "artifacts/sprint14b/**/*.parquet",
    "**/*stage2*",
    "**/*overlap*train*",
    "**/*overlap*val*",
    "**/*overlap*test*",
]
import glob as g
found = set()
for p in patterns:
    for f in g.glob(p, recursive=True):
        found.add(f)

for path in sorted(found):
    if not os.path.exists(path): continue
    try:
        df = pd.read_parquet(path)
        print(f"\n{path}:")
        print(f"  rows: {len(df):,}")
        print(f"  size_bytes: {os.path.getsize(path):,}")
        tc = [c for c in df.columns if 'time' in c.lower()]
        if tc:
            df[tc[0]] = pd.to_datetime(df[tc[0]])
            print(f"  timestamp_min: {df[tc[0]].min()}")
            print(f"  timestamp_max: {df[tc[0]].max()}")
        if 'target_6hr_binary' in df.columns:
            pos = df['target_6hr_binary'].sum()
            print(f"  positive_rate: {pos/len(df):.6f}")
    except Exception as e:
        print(f"  ERROR: {e}")
EOF

echo "=== VERIFICATION AUDIT COMPLETE ==="
