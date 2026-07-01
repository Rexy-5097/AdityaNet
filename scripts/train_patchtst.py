"""
scripts/train_patchtst.py

SuryaNet Sprint 4: PatchTST End-to-End Training Script

Strict split isolation:
  Train      ← artifacts/research/train.parquet       (2010-2019)
  Validation ← artifacts/research/validation.parquet  (2020-2022)
  Test       ← artifacts/research/test.parquet        (2023-present)

These are NEVER concatenated or cross-contaminated.

Artifacts produced:
  artifacts/models/patchtst_best.pt        ← best val TSS checkpoint
  artifacts/models/patchtst_last.pt        ← last epoch checkpoint
  artifacts/training_history.json          ← per-epoch metrics
  artifacts/test_metrics.json             ← full test metrics
  artifacts/calibration/probs.npy         ← test sigmoid probabilities
  artifacts/calibration/labels.npy        ← test true labels
  artifacts/attention_maps/               ← attention weights for a flare event
  artifacts/feature_importance/           ← permutation feature importance
  artifacts/runs/                         ← TensorBoard logs

Usage:
  PYTHONPATH=$PWD venv/bin/python3 scripts/train_patchtst.py
  PYTHONPATH=$PWD venv/bin/python3 scripts/train_patchtst.py --batch-size 64
  PYTHONPATH=$PWD venv/bin/python3 scripts/train_patchtst.py --max-epochs 10 --steps-per-epoch 3000
"""

import argparse
import json
import logging
import os
import sys

import numpy as np
import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.dataset import (
    SolarFlareWindowDataset,
    make_train_loader,
    make_eval_loader,
    _load_feature_columns,
)
from app.services.ml.model import (
    PatchTST,
    predict_with_uncertainty,
    extract_attention_maps,
)
from app.services.ml.trainer import Trainer
from app.services.ml.metrics import compute_metrics, compute_prob_metrics

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────────────────────
TRAIN_PARQUET = os.path.join("artifacts", "research", "train.parquet")
VAL_PARQUET   = os.path.join("artifacts", "research", "validation.parquet")
TEST_PARQUET  = os.path.join("artifacts", "research", "test.parquet")

ARTIFACT_DIR      = "artifacts"
MODEL_DIR         = os.path.join(ARTIFACT_DIR, "models")
CALIB_DIR         = os.path.join(ARTIFACT_DIR, "calibration")
ATTN_DIR          = os.path.join(ARTIFACT_DIR, "attention_maps")
FEAT_IMP_DIR      = os.path.join(ARTIFACT_DIR, "feature_importance")
TB_LOG_DIR        = os.path.join(ARTIFACT_DIR, "runs")
HISTORY_PATH      = os.path.join(ARTIFACT_DIR, "training_history.json")
TEST_METRICS_PATH = os.path.join(ARTIFACT_DIR, "test_metrics.json")

for d in [MODEL_DIR, CALIB_DIR, ATTN_DIR, FEAT_IMP_DIR, TB_LOG_DIR]:
    os.makedirs(d, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────
def print_banner(text: str) -> None:
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_metrics(tag: str, m: dict, pm: dict | None = None) -> None:
    cm = m["confusion_matrix"]
    print(f"\n[{tag}]")
    print(f"  Confusion Matrix: TP={cm['tp']:,}  FP={cm['fp']:,}  FN={cm['fn']:,}  TN={cm['tn']:,}")
    print(f"  TSS:       {m['tss']:.4f}")
    print(f"  POD:       {m['pod']:.4f}")
    print(f"  POFD:      {m['pofd']:.4f}")
    print(f"  FAR:       {m['far']:.4f}")
    print(f"  Precision: {m['precision']:.4f}")
    print(f"  Recall:    {m['recall']:.4f}")
    print(f"  F1:        {m['f1']:.4f}")
    if pm:
        print(f"  ROC-AUC:   {pm.get('roc_auc', float('nan')):.4f}")
        print(f"  PR-AUC:    {pm.get('pr_auc', float('nan')):.4f}")
        print(f"  Brier:     {pm.get('brier_score', float('nan')):.4f}")


def tss_tier(tss: float) -> str:
    if tss > 0.5:  return "✅ EXCELLENT (TSS > 0.5)"
    if tss > 0.4:  return "✅ STRONG    (TSS > 0.4)"
    if tss > 0.2:  return "✅ GOOD      (TSS > 0.2)"
    if tss > 0.0:  return "✅ MINIMUM   (TSS > 0.0)"
    return "❌ BELOW BASELINE (TSS ≤ 0.0)"


def json_safe(obj):
    """Recursively convert numpy types to native Python for JSON serialisation."""
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [json_safe(v) for v in obj]
    if isinstance(obj, (np.integer,)):
        return int(obj)
    if isinstance(obj, (np.floating,)):
        return float(obj)
    if isinstance(obj, float) and (obj != obj):   # NaN
        return None
    return obj


# ──────────────────────────────────────────────────────────────────────────────
# Feature Importance (Permutation)
# ──────────────────────────────────────────────────────────────────────────────
def compute_feature_importance(
    model: PatchTST,
    test_ds: SolarFlareWindowDataset,
    feature_cols: list[str],
    device: torch.device,
    threshold: float,
    n_batches: int = 200,
    batch_size: int = 32,
) -> dict[str, float]:
    """
    Permutation feature importance: for each feature, shuffle its values
    across the test windows, measure TSS drop vs baseline, and rank features.

    Args:
        model:        Trained PatchTST (best checkpoint loaded).
        test_ds:      Test dataset (features pre-loaded as numpy array).
        feature_cols: List of feature names.
        device:       Torch device.
        threshold:    Classification threshold from best val checkpoint.
        n_batches:    Number of test batches to evaluate (default 200).
        batch_size:   Eval batch size (default 32).

    Returns:
        dict mapping feature_name → TSS drop (higher = more important).
    """
    model.eval()
    n_samples   = min(n_batches * batch_size, len(test_ds))
    indices     = np.arange(n_samples)

    # Collect baseline predictions on a fixed subset
    X_list, y_list = [], []
    for i in range(0, n_samples, batch_size):
        batch_idx = indices[i : i + batch_size]
        xs = torch.stack([test_ds[int(j)][0] for j in batch_idx])
        ys = torch.stack([test_ds[int(j)][1] for j in batch_idx])
        X_list.append(xs)
        y_list.append(ys)

    X_full = torch.cat(X_list)          # [n_samples, 360, 14]
    y_full = torch.cat(y_list).numpy()  # [n_samples]

    # Baseline TSS
    baseline_probs = []
    with torch.no_grad():
        for i in range(0, n_samples, batch_size):
            x_batch = X_full[i : i + batch_size].to(device)
            logits  = model(x_batch)
            probs   = torch.sigmoid(logits).squeeze(-1)
            baseline_probs.append(probs.cpu().numpy())
    baseline_probs = np.concatenate(baseline_probs)
    baseline_pred  = (baseline_probs >= threshold).astype(int)
    baseline_tss   = compute_metrics(y_full, baseline_pred)["tss"]

    logger.info(f"Feature importance baseline TSS: {baseline_tss:.4f} on {n_samples} samples")

    # Permute each feature
    importance: dict[str, float] = {}
    for feat_idx, feat_name in enumerate(feature_cols):
        X_permuted = X_full.clone()
        # Shuffle values for this feature across all samples
        perm = torch.randperm(n_samples)
        X_permuted[:, :, feat_idx] = X_permuted[perm, :, feat_idx]

        perm_probs = []
        with torch.no_grad():
            for i in range(0, n_samples, batch_size):
                x_batch = X_permuted[i : i + batch_size].to(device)
                logits  = model(x_batch)
                probs   = torch.sigmoid(logits).squeeze(-1)
                perm_probs.append(probs.cpu().numpy())
        perm_probs = np.concatenate(perm_probs)
        perm_pred  = (perm_probs >= threshold).astype(int)
        perm_tss   = compute_metrics(y_full, perm_pred)["tss"]

        tss_drop = baseline_tss - perm_tss
        importance[feat_name] = round(float(tss_drop), 4)
        logger.info(f"  {feat_name:<30s}: TSS drop = {tss_drop:+.4f}")

    return dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))


# ──────────────────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(description="SuryaNet PatchTST Training")
    parser.add_argument("--batch-size",       type=int,   default=32,   help="Batch size (default 32; use 64 if memory allows)")
    parser.add_argument("--max-epochs",       type=int,   default=20,   help="Max epochs (default 20)")
    parser.add_argument("--num-workers",      type=int,   default=2,    help="DataLoader workers (default 2)")
    parser.add_argument("--lr",               type=float, default=1e-4, help="Learning rate (default 1e-4)")
    parser.add_argument("--steps-per-epoch",  type=int,   default=5000, help="Max train steps per epoch (default 5000)")
    parser.add_argument("--val-steps",        type=int,   default=2000, help="Max val steps per epoch (default 2000)")
    parser.add_argument("--skip-feat-imp",    action="store_true",      help="Skip feature importance (faster run)")
    args = parser.parse_args()

    print_banner("SuryaNet Sprint 4: PatchTST Solar Flare Forecasting")
    print(f"  Train parquet:      {TRAIN_PARQUET}")
    print(f"  Validation parquet: {VAL_PARQUET}")
    print(f"  Test parquet:       {TEST_PARQUET}")
    print(f"  Batch size:         {args.batch_size}")
    print(f"  Max epochs:         {args.max_epochs}")
    print(f"  Steps per epoch:    {args.steps_per_epoch:,}")
    print(f"  Val steps:          {args.val_steps:,}")
    print(f"  Workers:            {args.num_workers}")

    # ── 1. Load datasets (STRICT split isolation) ─────────────────────────────
    print_banner("Loading Datasets")
    train_ds = SolarFlareWindowDataset(TRAIN_PARQUET, split_name="train")
    val_ds   = SolarFlareWindowDataset(VAL_PARQUET,   split_name="validation")
    test_ds  = SolarFlareWindowDataset(TEST_PARQUET,  split_name="test")

    feature_cols = train_ds.feature_cols
    pos_rate     = float(train_ds.get_labels().mean())
    logger.info(f"Training set positive rate: {pos_rate:.4f} ({100*pos_rate:.2f}%)")

    # ── 2. DataLoaders ────────────────────────────────────────────────────────
    print_banner("Building DataLoaders")
    batch_size = args.batch_size   # Default 32 (safer for MPS fragmentation)

    train_loader = make_train_loader(train_ds, batch_size=batch_size, num_workers=args.num_workers)
    val_loader   = make_eval_loader(val_ds,    batch_size=batch_size, num_workers=args.num_workers, shuffle=True)
    test_loader  = make_eval_loader(test_ds,   batch_size=batch_size, num_workers=args.num_workers, shuffle=False)
    logger.info(f"DataLoaders built | batch_size={batch_size}")
    logger.info(f"Train batches available: {len(train_loader):,} (capped at {args.steps_per_epoch:,}/epoch)")
    logger.info(f"Val   batches available: {len(val_loader):,} (capped at {args.val_steps:,}/epoch)")
    logger.info(f"Test  batches:           {len(test_loader):,}")

    # ── 3. Model ──────────────────────────────────────────────────────────────
    print_banner("Initializing PatchTST Model (CLS Token)")
    model = PatchTST()

    # ── 4. Training ───────────────────────────────────────────────────────────
    print_banner("Training")
    trainer = Trainer(
        model            = model,
        train_loader     = train_loader,
        val_loader       = val_loader,
        pos_rate         = pos_rate,
        max_epochs       = args.max_epochs,
        patience         = 3,
        lr               = args.lr,
        checkpoint_dir   = MODEL_DIR,
        tb_log_dir       = TB_LOG_DIR,
        steps_per_epoch  = args.steps_per_epoch,
        val_steps        = args.val_steps,
    )

    try:
        history = trainer.fit()
    except RuntimeError as e:
        if "out of memory" in str(e).lower() or "mps" in str(e).lower():
            logger.warning(f"OOM detected: {e}. Retrying with batch_size=16, num_workers=0, CPU.")
            batch_size   = 16
            train_loader = make_train_loader(train_ds, batch_size=batch_size, num_workers=0)
            val_loader   = make_eval_loader(val_ds,    batch_size=batch_size, num_workers=0, shuffle=True)
            test_loader  = make_eval_loader(test_ds,   batch_size=batch_size, num_workers=0, shuffle=False)
            model   = PatchTST()
            trainer = Trainer(
                model            = model,
                train_loader     = train_loader,
                val_loader       = val_loader,
                pos_rate         = pos_rate,
                max_epochs       = args.max_epochs,
                patience         = 3,
                lr               = args.lr,
                checkpoint_dir   = MODEL_DIR,
                tb_log_dir       = TB_LOG_DIR,
                steps_per_epoch  = args.steps_per_epoch,
                val_steps        = args.val_steps,
            )
            trainer.device = torch.device("cpu")
            trainer.model.to(trainer.device)
            history = trainer.fit()
        else:
            raise

    with open(HISTORY_PATH, "w") as f:
        json.dump(json_safe(history), f, indent=2)
    logger.info(f"Saved training history → {HISTORY_PATH}")

    # ── 5. Test Evaluation ────────────────────────────────────────────────────
    print_banner("Test Set Evaluation (Best Checkpoint)")
    hard_metrics, prob_metrics, all_probs, all_labels = trainer.evaluate_test(test_loader)
    print_metrics("PatchTST Test Set", hard_metrics, prob_metrics)
    print(f"\n  Classification threshold: {trainer.best_threshold:.3f} (tuned on val TSS)")
    print(f"  TSS Assessment: {tss_tier(hard_metrics['tss'])}")

    full_metrics = {**json_safe(hard_metrics), **json_safe(prob_metrics),
                    "threshold": trainer.best_threshold}
    with open(TEST_METRICS_PATH, "w") as f:
        json.dump(full_metrics, f, indent=2)
    logger.info(f"Saved test metrics → {TEST_METRICS_PATH}")

    # ── 6. Calibration Data ───────────────────────────────────────────────────
    print_banner("Saving Calibration Data")
    np.save(os.path.join(CALIB_DIR, "probs.npy"),  all_probs)
    np.save(os.path.join(CALIB_DIR, "labels.npy"), all_labels)
    logger.info(f"Saved calibration arrays → {CALIB_DIR}/ (N={len(all_probs):,})")

    # ── 7. Monte Carlo Dropout Uncertainty ───────────────────────────────────
    print_banner("Monte Carlo Dropout Uncertainty Check")
    device   = trainer.device
    sample_X, _ = next(iter(test_loader))
    sample_X = sample_X[:32].to(device)
    unc      = predict_with_uncertainty(model, sample_X, n_samples=50)
    mean_std = unc["std_prob"].mean().item()
    if mean_std > 0:
        print(f"  ✅ MC Dropout uncertainty std = {mean_std:.4f}  (>0 confirmed)")
    else:
        print("  ❌ WARNING: MC Dropout std = 0. Dropout may be inactive.")

    # ── 8. Attention Maps ────────────────────────────────────────────────────
    print_banner("Attention Map Extraction (First Positive Flare Event)")
    pos_indices = np.where(test_ds.get_labels() == 1)[0]

    if len(pos_indices) == 0:
        logger.warning("No positive flare events in test set. Skipping attention maps.")
    else:
        first_pos_idx = int(pos_indices[0])
        X_pos, _ = test_ds[first_pos_idx]
        X_pos    = X_pos.unsqueeze(0).to(device)   # [1, 360, 14]

        model.eval()
        attn_maps = extract_attention_maps(model, X_pos)

        for li, attn in enumerate(attn_maps):
            # attn: [1, n_heads, 45, 45]
            attn_np = attn.squeeze(0).cpu().numpy()   # [n_heads, 45, 45]
            fname   = os.path.join(ATTN_DIR, f"flare_event_layer{li+1}.npy")
            np.save(fname, attn_np)

            # CLS row: attention from CLS token to each patch (most interpretable)
            cls_row = attn_np[:, 0, 1:]   # [n_heads, 44]
            peak_patch = int(cls_row.mean(axis=0).argmax())
            peak_time  = peak_patch * 8    # stride=8 minutes
            logger.info(
                f"Layer {li+1}: saved {fname} | shape={attn_np.shape} | "
                f"Peak CLS→patch at t-{360 - peak_time}min before event"
            )

        print(f"  ✅ Saved {len(attn_maps)} attention maps → {ATTN_DIR}/")
        print(f"     Test window index: {first_pos_idx}")
        print(f"     Attention shape per layer: [n_heads=8, n_tokens=45, n_tokens=45]")
        print(f"     CLS row (index 0) = model attention to each of 44 patch tokens")

    # ── 9. Feature Importance ────────────────────────────────────────────────
    if not args.skip_feat_imp:
        print_banner("Permutation Feature Importance")
        importance = compute_feature_importance(
            model        = model,
            test_ds      = test_ds,
            feature_cols = feature_cols,
            device       = device,
            threshold    = trainer.best_threshold,
            n_batches    = 200,
            batch_size   = batch_size,
        )

        # Save JSON
        imp_path = os.path.join(FEAT_IMP_DIR, "permutation_importance.json")
        with open(imp_path, "w") as f:
            json.dump(importance, f, indent=2)
        logger.info(f"Saved feature importance → {imp_path}")

        print("\n  Permutation Feature Importance (TSS drop, ranked):")
        print(f"  {'Feature':<32} TSS Drop")
        print(f"  {'-'*45}")
        for feat, drop in importance.items():
            bar = "█" * max(0, int(drop * 50))
            print(f"  {feat:<32} {drop:+.4f}  {bar}")
    else:
        logger.info("Feature importance skipped (--skip-feat-imp).")

    # ── 10. Final Summary ─────────────────────────────────────────────────────
    print_banner("Sprint 4 Complete")
    best_epoch = max(history, key=lambda r: r["val_tss"])
    tss = hard_metrics["tss"]
    print(f"  Best epoch:          {best_epoch['epoch']} (val TSS={best_epoch['val_tss']:.4f})")
    print(f"  Test TSS:            {tss:.4f}  →  {tss_tier(tss)}")
    print(f"  Test ROC-AUC:        {prob_metrics.get('roc_auc', float('nan')):.4f}")
    print(f"  Test PR-AUC:         {prob_metrics.get('pr_auc', float('nan')):.4f}")
    print(f"  Test Brier Score:    {prob_metrics.get('brier_score', float('nan')):.4f}")
    print(f"  Threshold (val opt): {trainer.best_threshold:.3f}")
    print()
    print(f"  Checkpoints:         {MODEL_DIR}/patchtst_best.pt")
    print(f"  Training history:    {HISTORY_PATH}")
    print(f"  Test metrics:        {TEST_METRICS_PATH}")
    print(f"  Calibration data:    {CALIB_DIR}/")
    print(f"  Attention maps:      {ATTN_DIR}/")
    print(f"  Feature importance:  {FEAT_IMP_DIR}/")
    print(f"  TensorBoard:         tensorboard --logdir {TB_LOG_DIR}")
    print("=" * 60)

    if tss <= 0.0:
        logger.error(f"Test TSS={tss:.4f} ≤ 0. Does not meet minimum success criterion.")
        sys.exit(1)


if __name__ == "__main__":
    main()
