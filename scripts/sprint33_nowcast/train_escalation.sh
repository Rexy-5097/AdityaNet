#!/bin/zsh
# Phase 1: frozen-contract escalation seeds 45/46 (clause fired: FE/month range
# 28.47 > 1.0). Reuses scripts/sprint33/train_driver.py UNMODIFIED, then the
# sealed Component 2 evaluator per seed. ';' so partial results survive.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
NDS=artifacts/research_v4/dataset_adi_nowcast
L=artifacts/sprint33/logs; mkdir -p $L
for S in 45 46; do
  echo "=== NC_s$S train ==="
  $PY scripts/sprint33/train_driver.py --run-id NC_s$S --seed $S --num-workers 2 \
    --features-file $NDS/feature_columns_15.json \
    --train-parquet $NDS/train.parquet --val-parquet $NDS/validation.parquet \
    > $L/NC_s$S.log 2>&1 ; echo "NC_s${S}_train exit=$?"
  echo "=== NC_s$S sealed episode eval ==="
  $PY scripts/sprint33_nowcast/eval_episode_nowcast.py NC_s$S $S \
    > $L/NC_s${S}_eval.log 2>&1 ; echo "NC_s${S}_eval exit=$?"
done
echo "ESCALATION COMPLETE"
