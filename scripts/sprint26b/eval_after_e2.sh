#!/bin/zsh
# Wait for E2 training to finish (run_meta.json written), then evaluate through
# the frozen Sprint 24 framework.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
while [ ! -f artifacts/sprint26b/runs/E2/run_meta.json ]; do
  sleep 60
done
echo "E2 training complete at $(date) — launching evaluation"
$PY scripts/sprint26b/eval_run.py E2 --calib isotonic > artifacts/sprint26b/logs/E2_eval.log 2>&1 ; echo "E2_eval exit=$?"
echo "E2 EVAL COMPLETE at $(date)"
grep "policy TSS" artifacts/sprint26b/logs/E2_eval.log
