#!/bin/zsh
# Component 1: reuse scripts/sprint33/train_driver.py UNMODIFIED (contract file-plan step 1).
# Three-seed Aditya-only nowcast training on dataset_adi_nowcast. ';' not '&&' so
# partial results survive.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
NDS=artifacts/research_v4/dataset_adi_nowcast
L=artifacts/sprint33/logs; mkdir -p $L
for S in 42 43 44; do
  echo "=== NC_s$S train ==="
  $PY scripts/sprint33/train_driver.py --run-id NC_s$S --seed $S --num-workers 2 \
    --features-file $NDS/feature_columns_15.json \
    --train-parquet $NDS/train.parquet --val-parquet $NDS/validation.parquet \
    > $L/NC_s$S.log 2>&1 ; echo "NC_s${S} exit=$?"
done
echo "COMPONENT1 TRAINING COMPLETE"
