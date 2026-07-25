#!/bin/zsh
# Study B Phase 0.5 — Aditya-only feasibility (measure-only).
# Task 1: Aditya-only FORECAST, seeds 42/43/44, frozen Sprint 24 harness on the
#         S2 span (directly comparable to F0/F2/EMG). Task 2: Aditya-only
#         NOWCAST, seed 42, window-level eval. No metric printed before analysis.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
FDS=artifacts/research_v4/dataset_adi_forecast
NDS=artifacts/research_v4/dataset_adi_nowcast
L=artifacts/sprint33/logs; mkdir -p $L artifacts/sprint33/runs

for S in 42 43 44; do
  echo "=== ADI-forecast seed $S train ==="
  $PY scripts/sprint33/train_driver.py --run-id ADIF_s$S --seed $S --num-workers 2 \
    --features-file $FDS/feature_columns_15.json \
    --train-parquet $FDS/train.parquet --val-parquet $FDS/validation.parquet \
    > $L/ADIF_s$S.log 2>&1; echo "ADIF_s${S}_train exit=$?"
  echo "=== ADI-forecast seed $S sealed eval ==="
  $PY scripts/sprint33/eval_s2.py ADIF_s$S \
    --checkpoint artifacts/sprint33/runs/ADIF_s$S/best.pt \
    --features-file $FDS/feature_columns_15.json \
    --cal-val-parquet $FDS/validation.parquet --test-parquet $FDS/test.parquet \
    > $L/ADIF_s${S}_eval.log 2>&1; echo "ADIF_s${S}_eval exit=$?"
done

echo "=== ADI-nowcast seed 42 train ==="
$PY scripts/sprint33/train_driver.py --run-id ADIN_s42 --seed 42 --num-workers 2 \
  --features-file $NDS/feature_columns_15.json \
  --train-parquet $NDS/train.parquet --val-parquet $NDS/validation.parquet \
  > $L/ADIN_s42.log 2>&1; echo "ADIN_s42_train exit=$?"
echo "=== ADI-nowcast seed 42 window-level eval ==="
$PY scripts/sprint33/eval_nowcast.py ADIN_s42 artifacts/sprint33/runs/ADIN_s42/best.pt \
  $NDS/feature_columns_15.json $NDS/test.parquet > $L/ADIN_s42_eval.log 2>&1; echo "ADIN_s42_eval exit=$?"
echo "FEASIBILITY COMPLETE"
