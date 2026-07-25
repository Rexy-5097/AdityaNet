#!/bin/zsh
# Sprint 30 Phases 3-4: F0 re-evaluation (frozen checkpoint, per F0.json
# "training: NONE") then F1 at pre-registered seeds 42/43/44, sequentially on
# MPS. ';' not '&&' so partial results survive individual failures.
# Eval runner prints NO test metrics (Phase 5 integrity rule).
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
TD=scripts/sprint30/train_driver.py
EV=scripts/sprint30/eval_run.py
V4=artifacts/research_v4/dataset_v4.0.0
L=artifacts/sprint30/logs
mkdir -p $L artifacts/sprint30/runs

echo "=== [1/7] F0 re-evaluation (frozen Baseline checkpoint, 14 features) ==="
$PY $EV F0 --checkpoint artifacts/sprint26a/runs/Baseline/best.pt \
  > $L/F0_eval.log 2>&1 ; echo "F0_eval exit=$?"

for SEED in 42 43 44; do
  echo "=== F1 seed $SEED train ==="
  $PY $TD --run-id F1_s$SEED --seed $SEED --num-workers 2 \
    --features-file $V4/feature_columns_17.json \
    --train-parquet $V4/train.parquet --val-parquet $V4/validation.parquet \
    > $L/F1_s$SEED.log 2>&1 ; echo "F1_s${SEED}_train exit=$?"
  echo "=== F1 seed $SEED eval ==="
  $PY $EV F1_s$SEED --features-file $V4/feature_columns_17.json \
    --val-parquet $V4/validation.parquet --test-parquet $V4/test.parquet \
    > $L/F1_s${SEED}_eval.log 2>&1 ; echo "F1_s${SEED}_eval exit=$?"
done
echo "CHAIN COMPLETE"
