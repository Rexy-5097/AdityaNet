#!/bin/zsh
# Wait for the E1-E6 chain to finish, then run E2 (uncapped) train+eval.
# E2 must not overlap the chain (MPS one-at-a-time), so we poll chain.log.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
L=artifacts/sprint26a/logs
while ! grep -q "CHAIN COMPLETE" "$L/chain.log" 2>/dev/null; do
  sleep 60
done
echo "chain done — launching E2 at $(date)"
$PY scripts/sprint26a/train_driver.py --run-id E2 --seed 42 --num-workers 2 \
   --steps-per-epoch 80646 > $L/E2.log 2>&1 ; echo "E2_train exit=$?"
$PY scripts/sprint26a/eval_run.py E2 --calib isotonic > $L/E2_eval.log 2>&1 ; echo "E2_eval exit=$?"
echo "E2 COMPLETE at $(date)"
