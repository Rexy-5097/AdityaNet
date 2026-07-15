#!/bin/zsh
# Forecast Reliability Diagnostic battery (frozen pre-reg 48cbaad). ';' not '&&'
# so partial results survive. Decisive arms (ceiling + H1/H2) front-loaded.
cd "/Volumes/T7 Shield/Projects/AI/AdityaNet"
PY=./venv/bin/python
D=scripts/sprint33_diag/train_driver_diag.py
V1=artifacts/research_v4/dataset_v4.0.0            # V1 GOES-17
S2G=artifacts/research_v4/dataset_v4.2.0-s2-goes17 # S2 GOES-17
S2A=artifacts/research_v4/dataset_adi_forecast     # S2 Aditya-15
L=artifacts/sprint_diagnostic/logs; mkdir -p $L artifacts/sprint_diagnostic/runs

run() { echo "=== $1 ==="; $PY $D "${@:2}" > $L/$1.log 2>&1; echo "$1 exit=$?"; }

# --- S2-GOES 100% x3 (ceiling baseline, full diagnostic logging) ---
for S in 42 43 44; do
  run S2G_f100_s$S --run-id S2G_f100_s$S --seed $S --subset-seed $S \
    --features-file $S2G/feature_columns_17.json --train-parquet $S2G/train.parquet --val-parquet $S2G/validation.parquet
done
# --- size-matched-V1 x3 draws (H1 vs H2 — decisive) ---
for S in 42 43 44; do
  run SMV1_d$S --run-id SMV1_d$S --seed $S --subset-seed $S --match-count 786298 \
    --features-file $V1/feature_columns_17.json --train-parquet $V1/train.parquet --val-parquet $V1/validation.parquet
done
# --- S2-GOES data-scaling 25/50% x3 (H1 within regime) ---
for FR in 0.25 0.5; do FT=$(echo $FR | tr -d '.'); for S in 42 43 44; do
  run S2G_f${FT}_s$S --run-id S2G_f${FT}_s$S --seed $S --subset-seed $S --data-fraction $FR \
    --features-file $S2G/feature_columns_17.json --train-parquet $S2G/train.parquet --val-parquet $S2G/validation.parquet
done; done
# --- S2-Aditya 25/100% x2 (Study B ceiling) ---
for FR in 1.0 0.25; do FT=$(echo $FR | tr -d '.'); for S in 42 43; do
  run S2A_f${FT}_s$S --run-id S2A_f${FT}_s$S --seed $S --subset-seed $S --data-fraction $FR \
    --features-file $S2A/feature_columns_15.json --train-parquet $S2A/train.parquet --val-parquet $S2A/validation.parquet
done; done
# --- screening (S2-GOES 100%, seed 42): H3 reg, H4 steps, H7 sampler, H7/H2 base-rate ---
run SCR_reg    --run-id SCR_reg    --seed 42 --subset-seed 42 --dropout 0.4 --weight-decay 1e-3 \
  --features-file $S2G/feature_columns_17.json --train-parquet $S2G/train.parquet --val-parquet $S2G/validation.parquet
run SCR_steps  --run-id SCR_steps  --seed 42 --subset-seed 42 --steps-per-epoch 1250 \
  --features-file $S2G/feature_columns_17.json --train-parquet $S2G/train.parquet --val-parquet $S2G/validation.parquet
run SCR_natural --run-id SCR_natural --seed 42 --subset-seed 42 --sampler-mode natural \
  --features-file $S2G/feature_columns_17.json --train-parquet $S2G/train.parquet --val-parquet $S2G/validation.parquet
run SCR_baserate --run-id SCR_baserate --seed 42 --subset-seed 42 --base-rate 0.006 \
  --features-file $S2G/feature_columns_17.json --train-parquet $S2G/train.parquet --val-parquet $S2G/validation.parquet
echo "BATTERY COMPLETE"
