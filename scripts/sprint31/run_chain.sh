#!/bin/zsh
# Sprint 31 Phases 3-4: F2 seeds 42/43/44 train + sealed S2 eval; automatic
# pre-registered escalation to seeds 45/46; then F0-on-S2 and all F1-on-S2
# sealed re-evaluations for same-span pairing. No metric reaches stdout.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
V4S2=artifacts/research_v4/dataset_v4.1.0-s2
V400=artifacts/research_v4/dataset_v4.0.0
L=artifacts/sprint31/logs
mkdir -p $L artifacts/sprint31/runs

train_eval_f2() {
  SEED=$1
  echo "=== F2 seed $SEED train ==="
  $PY scripts/sprint31/train_driver.py --run-id F2_s$SEED --seed $SEED --num-workers 2 \
    --features-file $V4S2/feature_columns_36.json \
    --train-parquet $V4S2/train.parquet --val-parquet $V4S2/validation.parquet \
    > $L/F2_s$SEED.log 2>&1 ; echo "F2_s${SEED}_train exit=$?"
  echo "=== F2 seed $SEED sealed eval ==="
  $PY scripts/sprint31/eval_s2.py F2_s$SEED \
    --checkpoint artifacts/sprint31/runs/F2_s$SEED/best.pt \
    --features-file $V4S2/feature_columns_36.json \
    --cal-val-parquet $V4S2/validation.parquet --test-parquet $V4S2/test.parquet \
    > $L/F2_s${SEED}_eval.log 2>&1 ; echo "F2_s${SEED}_eval exit=$?"
}

for SEED in 42 43 44; do train_eval_f2 $SEED; done

$PY scripts/sprint31/auto_escalate.py ; ESC=$?
if [ $ESC -eq 42 ]; then
  for SEED in 45 46; do train_eval_f2 $SEED; done
fi

echo "=== F0-on-S2 sealed eval ==="
$PY scripts/sprint31/eval_s2.py F0_s2 \
  --checkpoint artifacts/sprint26a/runs/Baseline/best.pt \
  --features-file artifacts/feature_columns.json \
  --cal-val-parquet artifacts/research/validation.parquet \
  --test-parquet artifacts/sprint14c/s2_test.parquet \
  > $L/F0_s2_eval.log 2>&1 ; echo "F0_s2_eval exit=$?"

for SEED in 42 43 44 45 46; do
  echo "=== F1_s$SEED-on-S2 sealed eval ==="
  $PY scripts/sprint31/eval_s2.py F1_s${SEED}_s2 \
    --checkpoint artifacts/sprint30/runs/F1_s$SEED/best.pt \
    --features-file $V400/feature_columns_17.json \
    --cal-val-parquet $V400/validation.parquet \
    --test-parquet $V4S2/s2_test_f1feats.parquet \
    > $L/F1_s${SEED}_s2_eval.log 2>&1 ; echo "F1_s${SEED}_s2_eval exit=$?"
done
echo "CHAIN COMPLETE"
