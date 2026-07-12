#!/bin/zsh
# Sprint 32 Phase 3: F3 (late fusion) and EraMatchedGOES (EMG) — train + sealed
# S2 eval, seeds 42/43/44 with automatic pre-registered escalation to 45/46.
# F0-on-S2 and F2 sealed records are reused from Sprint 31 (not recomputed).
# No metric reaches stdout before Phase 4.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
F2DS=artifacts/research_v4/dataset_v4.1.0-s2
EMGDS=artifacts/research_v4/dataset_v4.2.0-s2-goes17
L=artifacts/sprint32/logs
mkdir -p $L artifacts/sprint32/runs

f3_one() {
  SEED=$1
  echo "=== F3 seed $SEED train ==="
  $PY scripts/sprint32/train_driver_f3.py --run-id F3_s$SEED --seed $SEED --num-workers 2 \
    --features-file $F2DS/feature_columns_36.json \
    --train-parquet $F2DS/train.parquet --val-parquet $F2DS/validation.parquet \
    > $L/F3_s$SEED.log 2>&1 ; echo "F3_s${SEED}_train exit=$?"
  echo "=== F3 seed $SEED sealed eval ==="
  $PY scripts/sprint32/eval_s2_f3.py F3_s$SEED \
    --checkpoint artifacts/sprint32/runs/F3_s$SEED/best.pt \
    --features-file $F2DS/feature_columns_36.json \
    --cal-val-parquet $F2DS/validation.parquet --test-parquet $F2DS/test.parquet \
    > $L/F3_s${SEED}_eval.log 2>&1 ; echo "F3_s${SEED}_eval exit=$?"
}

emg_one() {
  SEED=$1
  echo "=== EMG seed $SEED train ==="
  $PY scripts/sprint32/train_driver.py --run-id EMG_s$SEED --seed $SEED --num-workers 2 \
    --features-file $EMGDS/feature_columns_17.json \
    --train-parquet $EMGDS/train.parquet --val-parquet $EMGDS/validation.parquet \
    > $L/EMG_s$SEED.log 2>&1 ; echo "EMG_s${SEED}_train exit=$?"
  echo "=== EMG seed $SEED sealed eval ==="
  $PY scripts/sprint32/eval_s2.py EMG_s$SEED \
    --checkpoint artifacts/sprint32/runs/EMG_s$SEED/best.pt \
    --features-file $EMGDS/feature_columns_17.json \
    --cal-val-parquet $EMGDS/validation.parquet --test-parquet $EMGDS/test.parquet \
    > $L/EMG_s${SEED}_eval.log 2>&1 ; echo "EMG_s${SEED}_eval exit=$?"
}

for SEED in 42 43 44; do f3_one $SEED; done
$PY scripts/sprint32/auto_escalate.py F3 ; [ $? -eq 42 ] && { f3_one 45; f3_one 46; }

for SEED in 42 43 44; do emg_one $SEED; done
$PY scripts/sprint32/auto_escalate.py EMG ; [ $? -eq 42 ] && { emg_one 45; emg_one 46; }

echo "CHAIN COMPLETE"
