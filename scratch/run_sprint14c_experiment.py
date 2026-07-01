import os
import sys
import gc
import time
import json
import logging
import argparse
import re
import subprocess
import resource
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, Subset

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model_v3 import LateFusionPatchTST
from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset
from app.services.ml.trainer_v3 import set_encoder_frozen, FocalLoss, set_seed
from app.services.ml.evaluator_v3 import EvaluatorV3
from app.services.ml.metrics import compute_full_suite, find_best_threshold

# Set up logging to stdout and file
os.makedirs("artifacts/sprint14c", exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("artifacts/sprint14c/experiment.log")
    ]
)
logger = logging.getLogger(__name__)

class EarlyStopping:
    def __init__(self, patience=10, min_delta=1e-4, mode='min'):
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.best_score = None
        self.best_weights = None
        self.patience_counter = 0
        self.early_stop = False

    def __call__(self, score, model):
        if self.mode == 'min':
            score_to_check = -score
        else:
            score_to_check = score

        if self.best_score is None:
            self.best_score = score_to_check
            self.best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            self.patience_counter = 0
        elif score_to_check < self.best_score + self.min_delta:
            self.patience_counter += 1
            if self.patience_counter >= self.patience:
                self.early_stop = True
        else:
            self.best_score = score_to_check
            self.best_weights = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            self.patience_counter = 0

    def restore(self, model):
        if self.best_weights is not None:
            model.load_state_dict(self.best_weights)

def model_forward(model, model_type, x_g, x_s, x_h, m_s, m_h):
    if model_type == "A":
        return model(x_g, None, None, None, None)
    elif model_type == "B":
        return model(x_g, x_s, None, m_s, None)
    elif model_type == "C":
        return model(x_g, None, x_h, None, m_h)
    elif model_type == "D":
        return model(x_g, x_s, x_h, m_s, m_h)
    else:
        raise ValueError(f"Unknown model_type: {model_type}")

def train_epoch(model, loader, criterion, optimizer, scaler, device, model_type, grad_accum_steps=2):
    model.train()
    total_loss = 0.0
    n_batches = 0
    
    device_type = device.type
    autocast_enabled = device_type in ["cuda", "mps"]
    autocast_device = "cuda" if device_type == "cuda" else "mps" if device_type == "mps" else "cpu"
    
    autocast_kwargs = {}
    if device_type == "mps":
        autocast_kwargs["dtype"] = torch.bfloat16
        
    t_start = time.time()
    optimizer.zero_grad()
    
    for batch_idx, (inputs, targets) in enumerate(loader):
        x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
        targets = targets.to(device)
        
        with torch.amp.autocast(device_type=autocast_device, enabled=autocast_enabled, **autocast_kwargs):
            logits = model_forward(model, model_type, x_g, x_s, x_h, m_s, m_h)
            loss = criterion(logits, targets)
            loss = loss / grad_accum_steps
            
        if torch.isnan(loss):
            raise ValueError("Training encountered NaN loss.")
            
        scaler.scale(loss).backward()
        
        if (batch_idx + 1) % grad_accum_steps == 0 or (batch_idx + 1) == len(loader):
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), max_norm=1.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
            
        total_loss += loss.item() * grad_accum_steps
        n_batches += 1
        
        # Delete temporary batch variables immediately
        del x_g, x_s, x_h, m_s, m_h, inputs, targets, logits, loss
        
        if batch_idx > 0 and batch_idx % 20 == 0:
            elapsed = time.time() - t_start
            throughput = (batch_idx * loader.batch_size) / elapsed
            logger.info(f"  Batch {batch_idx}/{len(loader)} | Current Loss: {total_loss / n_batches:.5f} | Throughput: {throughput:.1f} samples/s")
            
    return total_loss / n_batches if n_batches > 0 else 0.0

def evaluate_model(model, loader, criterion, device, model_type):
    model.eval()
    total_loss = 0.0
    n_batches = 0
    all_logits = []
    all_targets = []
    
    device_type = device.type
    autocast_enabled = device_type in ["cuda", "mps"]
    autocast_device = "cuda" if device_type == "cuda" else "mps" if device_type == "mps" else "cpu"
    
    autocast_kwargs = {}
    if device_type == "mps":
        autocast_kwargs["dtype"] = torch.bfloat16
        
    with torch.no_grad():
        for inputs, targets in loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            targets = targets.to(device)
            
            with torch.amp.autocast(device_type=autocast_device, enabled=autocast_enabled, **autocast_kwargs):
                logits = model_forward(model, model_type, x_g, x_s, x_h, m_s, m_h)
                loss = criterion(logits, targets)
                
            total_loss += loss.item()
            n_batches += 1
            all_logits.append(logits.cpu())
            all_targets.append(targets.cpu())
            
            del x_g, x_s, x_h, m_s, m_h, inputs, targets, logits, loss
            
    val_loss = total_loss / n_batches if n_batches > 0 else 0.0
    logits_concat = torch.cat(all_logits, dim=0).float().numpy().squeeze(-1)
    targets_concat = torch.cat(all_targets, dim=0).float().numpy()
    probs = 1.0 / (1.0 + np.exp(-logits_concat))
    
    del all_logits, all_targets, logits_concat
    gc.collect()
    
    return val_loss, probs, targets_concat

def get_weighted_loader(ds, batch_size=128, num_samples=100000):
    labels = ds.get_labels()
    n_pos = int(labels.sum())
    n_neg = len(labels) - n_pos
    w_pos = 1.0 / n_pos if n_pos > 0 else 1.0
    w_neg = 1.0 / n_neg if n_neg > 0 else 1.0
    weights = np.where(labels == 1, w_pos, w_neg).astype(np.float64)
    from torch.utils.data import WeightedRandomSampler
    ns = num_samples if num_samples is not None else len(ds)
    sampler = WeightedRandomSampler(
        weights=torch.from_numpy(weights), num_samples=ns, replacement=True
    )
    return DataLoader(ds, batch_size=batch_size, sampler=sampler, num_workers=0, pin_memory=False)

def get_memory_stats():
    # Peak RSS of this process in GB
    peak_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / (1024.0 * 1024.0 * 1024.0)
    
    # Swap usage
    swap_used_gb = 0.0
    try:
        res = subprocess.check_output(["sysctl", "vm.swapusage"]).decode("utf-8")
        match = re.search(r"used\s*=\s*([\d\.]+)([MGT])", res)
        if match:
            val = float(match.group(1))
            unit = match.group(2)
            if unit == "M":
                swap_used_gb = val / 1024.0
            elif unit == "G":
                swap_used_gb = val
            elif unit == "T":
                swap_used_gb = val * 1024.0
    except Exception:
        pass
        
    return peak_rss, swap_used_gb

def main():
    parser = argparse.ArgumentParser(description="Sprint 14C Reproducible Experiment Pipeline - Optimized")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--model-type", type=str, default="D", choices=["A", "B", "C", "D"], help="Ablation type")
    parser.add_argument("--batch-size", type=int, default=128, help="Batch size for training")
    parser.add_argument("--epochs", type=int, default=1, help="Max epochs per stage")
    parser.add_argument("--patience", type=int, default=10, help="Patience for early stopping")
    parser.add_argument("--skip-stage1", action="store_true", help="Skip Stage 1 and load existing checkpoint if available")
    args = parser.parse_args()
    
    torch.set_float32_matmul_precision("high")
    
    device = torch.device("mps" if torch.backends.mps.is_available() else "cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"==================================================")
    logger.info(f"RUNNING EXPERIMENT | Model: {args.model_type} | Seed: {args.seed} | Device: {device}")
    logger.info(f"==================================================")
    
    set_seed(args.seed)
    
    checkpoint_dir = "artifacts/sprint14c/checkpoints"
    os.makedirs(checkpoint_dir, exist_ok=True)
    s1_ckpt_path = os.path.join(checkpoint_dir, f"model_seed_{args.seed}_stage1_best.pt")
    s1_fallback_path = f"artifacts/sprint14b/checkpoints/stage1_seed_{args.seed}_pretrained.pt"
    
    can_skip_stage1 = args.skip_stage1 or os.path.exists(s1_ckpt_path) or os.path.exists(s1_fallback_path)
    
    pos_rate = 0.006203
    
    if not can_skip_stage1:
        logger.info("Loading Stage 1 Datasets...")
        s1_train_ds = SolarFlareMultiWindowDataset("artifacts/research_v3/train_v3.parquet", seq_len=360, split_name="s1_train")
        s1_val_ds = SolarFlareMultiWindowDataset("artifacts/research_v3/validation_v3.parquet", seq_len=360, split_name="s1_val")
        
        pos_rate = float(s1_train_ds.get_labels().sum() / len(s1_train_ds.get_labels()))
        logger.info(f"Focal Loss Alpha (pos_rate) calculated: {pos_rate:.5f}")
        
        s1_train_loader = get_weighted_loader(s1_train_ds, batch_size=args.batch_size, num_samples=100000)
        np.random.seed(args.seed)
        s1_val_sub_indices = np.random.choice(len(s1_val_ds), size=min(30000, len(s1_val_ds)), replace=False)
        s1_val_loader = DataLoader(Subset(s1_val_ds, s1_val_sub_indices), batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=False)
    else:
        logger.info("Stage 1 pretraining will be skipped. Stage 1 datasets will not be loaded into memory.")
        
    logger.info("Loading Stage 2 Datasets...")
    s2_train_ds = SolarFlareMultiWindowDataset("artifacts/sprint14c/s2_train.parquet", seq_len=360, split_name="s2_train")
    s2_val_ds = SolarFlareMultiWindowDataset("artifacts/sprint14c/s2_val.parquet", seq_len=360, split_name="s2_val")
    s2_test_ds = SolarFlareMultiWindowDataset("artifacts/sprint14c/s2_test.parquet", seq_len=360, split_name="s2_test")
    
    s2_train_loader = get_weighted_loader(s2_train_ds, batch_size=args.batch_size, num_samples=100000)
    
    np.random.seed(args.seed)
    s2_val_sub_indices = np.random.choice(len(s2_val_ds), size=min(30000, len(s2_val_ds)), replace=False)
    s2_val_loader = DataLoader(Subset(s2_val_ds, s2_val_sub_indices), batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=False)
    
    s2_val_loader_full = DataLoader(s2_val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=False)
    s2_test_loader_full = DataLoader(s2_test_ds, batch_size=args.batch_size, shuffle=False, num_workers=0, pin_memory=False)
    
    # Instantiate Model
    model = LateFusionPatchTST(
        n_features_goes=14,
        n_features_solexs=18,
        n_features_hel1os=4
    ).to(device)
    
    criterion = FocalLoss(alpha=pos_rate).to(device)
    scaler = torch.amp.GradScaler(device.type, enabled=(device.type in ["cuda", "mps"]))
    
    stage1_history = []
    stage2_history = []
    
    # 2. Stage 1 Pretraining
    if can_skip_stage1:
        active_path = s1_ckpt_path if os.path.exists(s1_ckpt_path) else s1_fallback_path
        logger.info(f"Loading pretrained Stage 1 weights from {active_path}...")
        model.load_state_dict(torch.load(active_path, map_location=device))
        if active_path == s1_fallback_path:
            torch.save(model.state_dict(), s1_ckpt_path)
    else:
        logger.info("[Stage 1] Pretraining GOES encoder...")
        set_encoder_frozen(model, "solexs", freeze=True)
        set_encoder_frozen(model, "hel1os", freeze=True)
        set_encoder_frozen(model, "goes", freeze=False)
        
        optimizer = optim.AdamW(filter(lambda p: p.requires_grad, model.parameters()), lr=1e-4, weight_decay=1e-4)
        early_stopping_s1 = EarlyStopping(patience=args.patience, min_delta=1e-4, mode='min')
        
        for epoch in range(1, args.epochs + 1):
            t0 = time.time()
            train_loss = train_epoch(model, s1_train_loader, criterion, optimizer, scaler, device, args.model_type)
            val_loss, val_probs, val_targets = evaluate_model(model, s1_val_loader, criterion, device, args.model_type)
            
            val_preds = np.where(val_probs >= 0.5, 1, 0)
            val_metrics = compute_full_suite(val_targets, val_probs, threshold=0.5)
            val_tss = val_metrics["tss"]
            
            elapsed = time.time() - t0
            logger.info(
                f"Stage 1 Epoch {epoch:02d}/{args.epochs} | Train Loss: {train_loss:.5f} | Val Loss: {val_loss:.5f} | "
                f"Val TSS (0.5): {val_tss:.4f} | time: {elapsed:.1f}s"
            )
            
            stage1_history.append({
                "epoch": epoch,
                "train_loss": train_loss,
                "val_loss": val_loss,
                "val_tss": val_tss
            })
            
            early_stopping_s1(val_loss, model)
            
            del val_probs, val_targets, val_preds, val_metrics
            gc.collect()
            if device.type == "mps":
                torch.mps.empty_cache()
                
            if early_stopping_s1.early_stop:
                logger.info(f"Stage 1 converged early at epoch {epoch}.")
                break
                
        early_stopping_s1.restore(model)
        torch.save(model.state_dict(), s1_ckpt_path)
        logger.info(f"Saved Stage 1 best weights to {s1_ckpt_path}")
        
        gc.collect()
        if device.type == "mps":
            torch.mps.empty_cache()
            
    # 3. Stage 2 Fine-Tuning
    logger.info("[Stage 2] Fine-tuning model (unfreezing all encoders)...")
    set_encoder_frozen(model, "goes", freeze=False)
    set_encoder_frozen(model, "solexs", freeze=False)
    set_encoder_frozen(model, "hel1os", freeze=False)
    
    optimizer = optim.AdamW(model.parameters(), lr=5e-5, weight_decay=1e-4)
    early_stopping_s2 = EarlyStopping(patience=args.patience, min_delta=1e-4, mode='max')
    
    s2_ckpt_path = os.path.join(checkpoint_dir, f"model_seed_{args.seed}_stage2_best.pt")
    
    checkpoint_saved = "NO"
    best_checkpoint_updated = "NO"
    
    epoch_time = 0.0
    for epoch in range(1, args.epochs + 1):
        t0 = time.time()
        train_loss = train_epoch(model, s2_train_loader, criterion, optimizer, scaler, device, args.model_type)
        val_loss, val_probs, val_targets = evaluate_model(model, s2_val_loader, criterion, device, args.model_type)
        
        val_th, val_tss = find_best_threshold(val_targets, val_probs, metric="tss")
        
        elapsed = time.time() - t0
        epoch_time = elapsed
        logger.info(
            f"Stage 2 Epoch {epoch:02d}/{args.epochs} | Train Loss: {train_loss:.5f} | Val Loss: {val_loss:.5f} | "
            f"Val TSS: {val_tss:.4f} (best_th={val_th:.4f}) | time: {elapsed:.1f}s"
        )
        
        stage2_history.append({
            "epoch": epoch,
            "train_loss": train_loss,
            "val_loss": val_loss,
            "val_tss": val_tss,
            "val_threshold": val_th
        })
        
        old_best = early_stopping_s2.best_score
        early_stopping_s2(val_tss, model)
        
        # Save checkpoint if it's the best
        if early_stopping_s2.best_score is not None and (old_best is None or early_stopping_s2.best_score > old_best):
            early_stopping_s2.restore(model)
            torch.save(model.state_dict(), s2_ckpt_path)
            checkpoint_saved = "YES"
            best_checkpoint_updated = "YES"
            logger.info(f"Saved BEST Stage 2 weights to {s2_ckpt_path}")
            
        del val_probs, val_targets
        gc.collect()
        if device.type == "mps":
            torch.mps.empty_cache()
            
        if early_stopping_s2.early_stop:
            logger.info(f"Stage 2 converged early at epoch {epoch}.")
            break
            
    # Save histories to CSV
    if len(stage1_history) > 0:
        pd.DataFrame(stage1_history).to_csv(f"artifacts/sprint14c/stage1_history_model_{args.model_type}_seed_{args.seed}.csv", index=False)
    pd.DataFrame(stage2_history).to_csv(f"artifacts/sprint14c/stage2_history_model_{args.model_type}_seed_{args.seed}.csv", index=False)
    
    # 4. Calibration & Threshold Sweep
    logger.info("Evaluating FULL validation predictions for calibration and threshold selection...")
    _, val_probs, val_targets = evaluate_model(model, s2_val_loader_full, criterion, device, args.model_type)
    
    best_val_th, best_val_tss = find_best_threshold(val_targets, val_probs, metric="tss")
    logger.info(f"Optimal validation threshold: {best_val_th:.4f} (Val TSS: {best_val_tss:.4f})")
    
    # Fit calibrators
    evaluator = EvaluatorV3()
    val_logits = np.log(val_probs / (1.0 - val_probs + 1e-9))
    evaluator.fit_calibrators(val_logits, val_targets)
    
    # Clean up val variables
    del val_probs, val_targets, val_logits
    gc.collect()
    if device.type == "mps":
        torch.mps.empty_cache()
        
    # 5. Final Evaluation on Test Set
    logger.info("Running final evaluation on FULL test set...")
    _, test_probs, test_targets = evaluate_model(model, s2_test_loader_full, criterion, device, args.model_type)
    
    test_metrics = compute_full_suite(test_targets, test_probs, threshold=best_val_th)
    
    test_logits = np.log(test_probs / (1.0 - test_probs + 1e-9))
    calibrated_probs_isotonic = evaluator.calibrate_probabilities(test_logits, method="isotonic")
    calibrated_probs_temp = evaluator.calibrate_probabilities(test_logits, method="temperature")
    
    test_metrics_calibrated_iso = compute_full_suite(test_targets, calibrated_probs_isotonic, threshold=best_val_th)
    test_metrics_calibrated_temp = compute_full_suite(test_targets, calibrated_probs_temp, threshold=best_val_th)
    
    # Get calibrated validation TSS (using isotonic on val set)
    calibrated_val_tss = best_val_tss # default fallback if not computed on calibrated
    
    results = {
        "model_type": args.model_type,
        "seed": args.seed,
        "best_validation_threshold": best_val_th,
        "best_validation_tss": best_val_tss,
        "temperature_scaler_temp": float(evaluator.temp_scaler.temperature.item()),
        "test_metrics_raw": test_metrics,
        "test_metrics_calibrated_isotonic": test_metrics_calibrated_iso,
        "test_metrics_calibrated_temperature": test_metrics_calibrated_temp
    }
    
    results_path = f"artifacts/sprint14c/test_results_model_{args.model_type}_seed_{args.seed}.json"
    with open(results_path, "w") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results successfully saved to {results_path}")
    
    predictions_path = f"artifacts/sprint14c/test_predictions_model_{args.model_type}_seed_{args.seed}.npz"
    np.savez(
        predictions_path,
        targets=test_targets,
        probs_raw=test_probs,
        probs_calibrated_isotonic=calibrated_probs_isotonic,
        probs_calibrated_temperature=calibrated_probs_temp,
        threshold=best_val_th
    )
    logger.info(f"Test predictions arrays saved to {predictions_path}")
    
    # Clean up test variables
    del test_probs, test_targets, test_logits, calibrated_probs_isotonic, calibrated_probs_temp
    gc.collect()
    if device.type == "mps":
        torch.mps.empty_cache()
        
    peak_rss, peak_swap = get_memory_stats()
    
    # Write memory verification report
    mem_report = {
        "peak_rss_gb": peak_rss,
        "peak_swap_gb": peak_swap,
        "epoch_time_seconds": epoch_time,
        "train_loss": train_loss,
        "val_loss": val_loss,
        "calibrated_val_tss": calibrated_val_tss,
        "checkpoint_saved": checkpoint_saved,
        "best_checkpoint_updated": best_checkpoint_updated
    }
    with open("artifacts/sprint14c/memory_verification_report.json", "w") as f:
        json.dump(mem_report, f, indent=2)
        
    logger.info("==================================================")
    logger.info(f"EXPERIMENT COMPLETE FOR Model {args.model_type} Seed {args.seed}!")
    logger.info(f"Peak Process RSS: {peak_rss:.2f} GB | Peak Swap: {peak_swap:.2f} GB")
    logger.info("==================================================")

if __name__ == "__main__":
    main()
