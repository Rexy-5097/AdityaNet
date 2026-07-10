#!/bin/zsh
# Sprint 26A sequential chain: the six non-E2 experiments, one at a time on MPS.
# Runs regardless of individual failures (';' not '&&') so partial results survive.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
TD=scripts/sprint26a/train_driver.py
EV=scripts/sprint26a/eval_run.py
L=artifacts/sprint26a/logs

echo "=== [2/6] E1 regime-inclusive train+eval ==="
$PY $TD --run-id E1 --seed 42 --num-workers 2 \
   --train-parquet artifacts/sprint26a/e1_train.parquet \
   --val-parquet artifacts/sprint26a/e1_val.parquet > $L/E1.log 2>&1 ; echo "E1_train exit=$?"
$PY $EV E1 --calib isotonic > $L/E1_eval.log 2>&1 ; echo "E1_eval exit=$?"

echo "=== [3/6] E3 patience=8 train+eval ==="
$PY $TD --run-id E3 --seed 42 --num-workers 2 --patience 8 > $L/E3.log 2>&1 ; echo "E3_train exit=$?"
$PY $EV E3 --calib isotonic > $L/E3_eval.log 2>&1 ; echo "E3_eval exit=$?"

echo "=== [4/6] E4 T_max=10 train+eval ==="
$PY $TD --run-id E4 --seed 42 --num-workers 2 --t-max 10 > $L/E4.log 2>&1 ; echo "E4_train exit=$?"
$PY $EV E4 --calib isotonic > $L/E4_eval.log 2>&1 ; echo "E4_eval exit=$?"

echo "=== [5/6] E5 alpha=0.50 train+eval ==="
$PY $TD --run-id E5 --seed 42 --num-workers 2 --alpha 0.50 > $L/E5.log 2>&1 ; echo "E5_train exit=$?"
$PY $EV E5 --calib isotonic > $L/E5_eval.log 2>&1 ; echo "E5_eval exit=$?"

echo "=== [6/6] E6 Platt calibration (reuse Baseline checkpoint) ==="
mkdir -p artifacts/sprint26a/runs/E6
cp artifacts/sprint26a/runs/Baseline/best.pt artifacts/sprint26a/runs/E6/best.pt
cp artifacts/sprint26a/runs/Baseline/history.json artifacts/sprint26a/runs/E6/history.json 2>/dev/null
cp artifacts/sprint26a/runs/Baseline/run_meta.json artifacts/sprint26a/runs/E6/run_meta.json 2>/dev/null
$PY $EV E6 --calib platt > $L/E6_eval.log 2>&1 ; echo "E6_eval exit=$?"

echo "=== CHAIN COMPLETE ==="
