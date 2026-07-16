#!/bin/zsh
# Layer 3 orchestrator (frozen contract file-plan step 4). Reproduces the full
# sprint from scratch: 3 pre-registered seeds + escalation seeds (the clause
# fired) + sealed per-seed episode evaluations + frozen aggregation.
# ';' not '&&' so partial results survive.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
NDS=artifacts/research_v4/dataset_adi_nowcast
L=artifacts/sprint33/logs; mkdir -p $L artifacts/sprint33_nowcast/runs

for S in 42 43 44 45 46; do
  echo "=== NC_s$S train ==="
  $PY scripts/sprint33/train_driver.py --run-id NC_s$S --seed $S --num-workers 2 \
    --features-file $NDS/feature_columns_15.json \
    --train-parquet $NDS/train.parquet --val-parquet $NDS/validation.parquet \
    > $L/NC_s$S.log 2>&1 ; echo "NC_s${S}_train exit=$?"
  echo "=== NC_s$S sealed episode eval ==="
  $PY scripts/sprint33_nowcast/eval_episode_nowcast.py NC_s$S $S \
    > $L/NC_s${S}_eval.log 2>&1 ; echo "NC_s${S}_eval exit=$?"
done
echo "=== frozen aggregation + decision rule ==="
$PY scripts/sprint33_nowcast/analyze.py
echo "LAYER3 RUN COMPLETE"
