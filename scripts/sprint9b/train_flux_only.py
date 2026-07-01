"""
scripts/sprint9b/train_flux_only.py

Sprint 9B: Controlled Retraining Feasibility Study
Experiment A: Flux-Only Retraining

Machine Safety Constraints:
- Apple Silicon M4 MacBook Air, 16 GB unified memory
- num_workers = 0, pin_memory = False
- Batch size = 32
- Lazy window loading via SolarFlareWindowDataset
- Explicit gc.collect() after validation
- torch.mps.empty_cache() after epoch
"""

import os
import sys
import json
import logging
import gc
import time
import pickle
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from sklearn.isotonic import IsotonicRegression

# Ensure project root is in python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.services.ml.dataset import SolarFlareWindowDataset, make_train_loader, make_eval_loader
from app.services.ml.model import PatchTST
from app.services.ml.trainer import FocalLoss
from app.services.ml.metrics import compute_metrics, compute_prob_metrics
from app.services.ml.inference import CalibratorWrapper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Paths
TRAIN_PARQUET = os.path.join("artifacts", "research", "train.parquet")
VAL_PARQUET   = os.path.join("artifacts", "research", "validation.parquet")
OUTPUT_DIR    = os.path.join("artifacts", "sprint9b")

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Save paths
BEST_CKPT_PATH   = os.path.join(OUTPUT_DIR, "best_flux_only.pt")
LAST_CKPT_PATH   = os.path.join(OUTPUT_DIR, "suryanet_flux_only.pt")
CALIBRATOR_PATH  = os.path.join(OUTPUT_DIR, "calibrator_flux_only.pkl")
LOG_PATH         = os.path.join(OUTPUT_DIR, "training_log_flux_only.json")

# Hyperparameters
SEQ_LEN = 360
BATCH_SIZE = 32
MAX_EPOCHS = 15
PATIENCE = 4
LR = 1e-4
WEIGHT_DECAY = 1e-4
CLIP_NORM = 1.0
STEPS_PER_EPOCH = 5000
VAL_STEPS = 2000

# Fixed threshold for metrics evaluation during training
FIXED_THRESHOLD = 0.50

def get_memory_usage_gb() -> float:
    try:
        import subprocess
        pid = os.getpid()
        out = subprocess.check_output(["ps", "-o", "rss=", "-p", str(pid)])
        rss_kb = int(out.strip())
        return rss_kb / (1024 * 1024)
    except Exception:
        import resource
        # ru_maxrss is in bytes on macOS
        return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024 * 1024 * 1024)

def main():
    logger.info("Initializing Sprint 9B Experiment A: Flux-Only Retraining")
    
    device = torch.device("mps") if torch.backends.mps.is_available() else torch.device("cpu")
    logger.info(f"Using device: {device}")

    # Define features: drop minutes_since_last_flare
    with open(os.path.join("artifacts", "feature_columns.json"), "r") as f:
        all_features = json.load(f)
    
    feature_cols = [col for col in all_features if col != "minutes_since_last_flare"]
    logger.info(f"Flux-only feature set ({len(feature_cols)} features): {feature_cols}")

    # Load datasets (strict split isolation, never load test split here)
    logger.info("Loading training dataset...")
    train_ds = SolarFlareWindowDataset(TRAIN_PARQUET, seq_len=SEQ_LEN, feature_cols=feature_cols, split_name="train_flux")
    pos_rate = float(train_ds.get_labels().mean())
    
    logger.info("Loading validation dataset...")
    val_ds = SolarFlareWindowDataset(VAL_PARQUET, seq_len=SEQ_LEN, feature_cols=feature_cols, split_name="val_flux")

    # DataLoaders (num_workers=0, pin_memory=False)
    train_loader = make_train_loader(train_ds, batch_size=BATCH_SIZE, num_workers=0)
    val_loader = make_eval_loader(val_ds, batch_size=BATCH_SIZE, num_workers=0, shuffle=True)

    # Initialize PatchTST Model
    model = PatchTST(seq_len=SEQ_LEN, n_features=len(feature_cols))
    model.to(device)

    # Loss, Optimizer, Scheduler
    criterion = FocalLoss(gamma=2.0, alpha=0.25)
    optimizer = optim.AdamW(model.parameters(), lr=LR, weight_decay=WEIGHT_DECAY)
    scheduler = optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=MAX_EPOCHS)

    best_tss = -float("inf")
    patience_counter = 0
    training_log = []

    # Training Loop
    for epoch in range(1, MAX_EPOCHS + 1):
        t0 = time.time()
        
        # Train phase
        model.train()
        total_loss = 0.0
        n_train_batches = 0
        
        for X, y in train_loader:
            X, y = X.to(device), y.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(X)
            loss = criterion(logits, y)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), CLIP_NORM)
            optimizer.step()
            
            total_loss += loss.item()
            n_train_batches += 1
            if n_train_batches >= STEPS_PER_EPOCH:
                break
        
        avg_train_loss = total_loss / max(n_train_batches, 1)
        
        # Validation phase
        model.eval()
        val_probs = []
        val_labels = []
        n_val_batches = 0
        
        with torch.no_grad():
            for X, y in val_loader:
                X, y = X.to(device), y.to(device)
                logits = model(X)
                probs = torch.sigmoid(logits).squeeze(-1)
                val_probs.append(probs.cpu().numpy())
                val_labels.append(y.cpu().numpy())
                n_val_batches += 1
                if n_val_batches >= VAL_STEPS:
                    break
        
        val_probs = np.concatenate(val_probs)
        val_labels = np.concatenate(val_labels)
        
        # Evaluate metrics using FIXED threshold of 0.50
        val_preds = (val_probs >= FIXED_THRESHOLD).astype(int)
        metrics = compute_metrics(val_labels, val_preds)
        val_tss = metrics["tss"]
        val_f1 = metrics["f1"]
        val_precision = metrics["precision"]
        val_recall = metrics["recall"]
        
        # Scheduler step
        scheduler.step()
        
        # Garbage Collection and MPS Empty Cache
        del val_probs, val_labels, val_preds
        gc.collect()
        if device.type == "mps":
            torch.mps.empty_cache()
            
        elapsed = time.time() - t0
        mem_gb = get_memory_usage_gb()
        
        log_record = {
            "epoch": epoch,
            "train_loss": round(avg_train_loss, 6),
            "val_tss": round(val_tss, 4),
            "val_f1": round(val_f1, 4),
            "val_precision": round(val_precision, 4),
            "val_recall": round(val_recall, 4),
            "memory_gb": round(mem_gb, 4),
        }
        training_log.append(log_record)
        
        logger.info(
            f"Epoch {epoch:02d}/{MAX_EPOCHS} | Train Loss={avg_train_loss:.4f} | "
            f"Val TSS={val_tss:.4f} | Val F1={val_f1:.4f} | RAM={mem_gb:.2f} GB | {elapsed:.1f}s"
        )
        
        # Save last checkpoint
        torch.save({"epoch": epoch, "model": model.state_dict()}, LAST_CKPT_PATH)
        
        # Early stopping & best checkpoint
        if val_tss > best_tss:
            best_tss = val_tss
            patience_counter = 0
            torch.save({"epoch": epoch, "model": model.state_dict()}, BEST_CKPT_PATH)
            logger.info(f"  --> Saved new best validation checkpoint (TSS={best_tss:.4f})")
        else:
            patience_counter += 1
            if patience_counter >= PATIENCE:
                logger.info(f"Early stopping at epoch {epoch}. Best Val TSS: {best_tss:.4f}")
                break

    # Save training history log
    with open(LOG_PATH, "w") as f:
        json.dump(training_log, f, indent=2)
    logger.info(f"Saved training log to {LOG_PATH}")

    # Post-Training Calibration: Fit Isotonic Regression on validation split
    logger.info("Performing post-training calibration...")
    checkpoint = torch.load(BEST_CKPT_PATH, map_location=device, weights_only=True)
    model.load_state_dict(checkpoint["model"])
    model.eval()

    # Re-evaluate validation set sequentially for calibration fitting (no shuffle, entire validation dataset)
    val_cal_loader = make_eval_loader(val_ds, batch_size=BATCH_SIZE, num_workers=0, shuffle=False)
    
    val_probs_all = []
    val_labels_all = []
    with torch.no_grad():
        for X, y in val_cal_loader:
            X = X.to(device)
            logits = model(X)
            probs = torch.sigmoid(logits).squeeze(-1)
            val_probs_all.append(probs.cpu().numpy())
            val_labels_all.append(y.numpy())

    val_probs_all = np.concatenate(val_probs_all)
    val_labels_all = np.concatenate(val_labels_all)

    # Fit Isotonic Regression (production calibrator method)
    logger.info("Fitting Isotonic Regression calibrator on validation predictions...")
    isotonic_calib = IsotonicRegression(out_of_bounds="clip")
    isotonic_calib.fit(val_probs_all, val_labels_all)

    # Save calibrator wrapper
    calibrator = CalibratorWrapper("isotonic", isotonic_calib)
    with open(CALIBRATOR_PATH, "wb") as f:
        pickle.dump(calibrator, f)
    logger.info(f"Saved calibrated Isotonic calibrator to {CALIBRATOR_PATH}")
    logger.info("Flux-only retraining training pipeline finished successfully.")

if __name__ == "__main__":
    main()
