#!/bin/zsh
# Sprint 30 escalation per F1.json preregistration: "if across-seed TSS range
# > 0.015 on F1, escalate to 5 seeds before any verdict". Observed range
# 0.0426 > 0.015 (analysis.json, seeds 42/43/44). Seeds 45/46, identical
# frozen protocol, evals sealed.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
V4=artifacts/research_v4/dataset_v4.0.0
L=artifacts/sprint30/logs
for SEED in 45 46; do
  echo "=== F1 seed $SEED train ==="
  $PY scripts/sprint30/train_driver.py --run-id F1_s$SEED --seed $SEED --num-workers 2 \
    --features-file $V4/feature_columns_17.json \
    --train-parquet $V4/train.parquet --val-parquet $V4/validation.parquet \
    > $L/F1_s$SEED.log 2>&1 ; echo "F1_s${SEED}_train exit=$?"
  echo "=== F1 seed $SEED eval ==="
  $PY scripts/sprint30/eval_run.py F1_s$SEED --features-file $V4/feature_columns_17.json \
    --val-parquet $V4/validation.parquet --test-parquet $V4/test.parquet \
    > $L/F1_s${SEED}_eval.log 2>&1 ; echo "F1_s${SEED}_eval exit=$?"
done
echo "ESCALATION COMPLETE"
