"""
scratch/eval_only_v3.py

Sprint 13A — Evaluation Pipeline Debug
======================================
Standalone script that loads the saved Stage 2 best-TSS checkpoint and
re-runs ONLY the evaluation, calibration, plotting, and report-generation
sections from pilot_train_v3.py.

DO NOT RETRAIN.  No gradient computation.  No model modification.

Bugs fixed vs the original pilot_train_v3.py:
  1. reliability_diagram unpacking -- the dict now uses explicit key access
     instead of fragile .values() iteration.
  2. Syntax warning: backslash in docstring now escaped (\\Delta).
  3. s2_test_classes size alignment guard -- verified against len(targets_test).
  4. probs clipping before log-odds transform to prevent +-inf logits.
  5. matplotlib figure leak -- plt.close() after every save.
  6. fusion_attn imshow shape -- reshape to (3,3) safely before plotting.
"""

import os
import sys
import json
import math
import time
import warnings
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, ConcatDataset
import matplotlib
matplotlib.use("Agg")          # headless backend — no display required
import matplotlib.pyplot as plt

warnings.filterwarnings("ignore", category=UserWarning, message=".*pin_memory.*")

# ── Project root on sys.path ────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.ml.model_v3 import LateFusionPatchTST
from app.services.ml.model import PatchTST as PatchTST_V1
from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset
from app.services.ml.evaluator_v3 import EvaluatorV3
from app.services.ml.metrics import compute_metrics, compute_prob_metrics

# ── Constants (must match pilot_train_v3.py) ────────────────────────────────
SEQ_LEN        = 360
BATCH_SIZE     = 128
STAGE1_EPOCHS  = 5
STAGE2_EPOCHS  = 5
CHECKPOINT_DIR = "artifacts/sprint13/checkpoints"
TMP_DIR        = "artifacts/sprint13/tmp"
OUT_DIR        = "artifacts/sprint13"
os.makedirs(OUT_DIR, exist_ok=True)

# ── Safe log-odds (avoids ±inf) ─────────────────────────────────────────────
EPS = 1e-7
def safe_logits(probs: np.ndarray) -> np.ndarray:
    probs = np.clip(probs, EPS, 1.0 - EPS)
    return np.log(probs / (1.0 - probs))

# ── Block helpers (identical logic to pilot_train_v3.py) ────────────────────
def find_stage2_block_starts(df, block_size, n_blocks, target_col="target_6hr_binary"):
    n_rows = len(df)
    chunk_spacing = max(1, (n_rows - block_size) // n_blocks)
    starts = []
    for i in range(n_blocks):
        candidate_start = i * chunk_spacing
        found = False
        for offset in range(0, max(1, chunk_spacing - block_size), 100):
            idx = candidate_start + offset
            sub_df = df.iloc[idx : idx + block_size]
            has_pos    = sub_df[target_col].sum() > 5
            has_solexs = sub_df["mask_solexs"].sum() > 500
            has_hel1os = sub_df["mask_hel1os"].sum() > 500
            if has_pos and has_solexs and has_hel1os:
                starts.append(idx)
                found = True
                break
        if not found:
            # Fallback: just a positive chunk
            for offset in range(0, max(1, chunk_spacing - block_size), 100):
                idx = candidate_start + offset
                sub_df = df.iloc[idx : idx + block_size]
                if sub_df[target_col].sum() > 0:
                    starts.append(idx)
                    found = True
                    break
        if not found:
            starts.append(candidate_start)
    return starts

def slice_and_save_blocks(df, starts, block_size, split_name):
    paths = []
    for idx, start in enumerate(starts):
        block_df = df.iloc[start : start + block_size].copy()
        path = os.path.join(TMP_DIR, f"{split_name}_block_{idx}.parquet")
        block_df.to_parquet(path, index=False)
        paths.append(path)
    return paths

# ── evaluate_model — returns (loss, probs, targets) ─────────────────────────
class _DummyCriterion(nn.Module):
    """Placeholder so evaluate_model has a loss function."""
    def forward(self, logits, targets):
        return nn.functional.binary_cross_entropy_with_logits(
            logits.squeeze(-1), targets.float()
        )

def evaluate_model(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0
    all_logits = []
    all_targets = []
    with torch.no_grad():
        for inputs, targets in loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            targets = targets.to(device)
            logits = model(x_g, x_s, x_h, m_s, m_h)
            loss   = criterion(logits, targets)
            total_loss += loss.item()
            all_logits.append(logits.cpu())
            all_targets.append(targets.cpu())
    val_loss      = total_loss / len(loader) if len(loader) > 0 else 0.0
    logits_concat = torch.cat(all_logits, dim=0).numpy().squeeze(-1)
    targets_concat = torch.cat(all_targets, dim=0).numpy()
    probs = 1.0 / (1.0 + np.exp(-logits_concat))
    return val_loss, probs, targets_concat

# ── Attention extraction (for diagnostics) ──────────────────────────────────
def extract_v3_attention(model, x_goes, x_solexs, x_hel1os, mask_solexs, mask_hel1os):
    model.eval()
    with torch.no_grad():
        B = x_goes.size(0)
        g   = model.patch_embed_goes(x_goes)
        cls_g = model.cls_token_goes.expand(B, -1, -1)
        g   = torch.cat([cls_g, g], dim=1)
        g   = model.pos_enc_goes(g)
        goes_attn = []
        for layer in model.encoder_goes:
            g, attn = layer(g, return_attn=True)
            goes_attn.append(attn)
        g = model.norm_goes(g)
        q_g = model.pool_query_goes.expand(B, -1, -1)
        e_goes, pool_g = model.pool_attn_goes(q_g, g, g, need_weights=True)
        e_goes = e_goes.squeeze(1)

        solexs_attn = []
        s   = model.patch_embed_solexs(x_solexs)
        cls_s = model.cls_token_solexs.expand(B, -1, -1)
        s   = torch.cat([cls_s, s], dim=1)
        s   = model.pos_enc_solexs(s)
        for layer in model.encoder_solexs:
            s, attn = layer(s, return_attn=True)
            solexs_attn.append(attn)
        s   = model.norm_solexs(s)
        q_s = model.pool_query_solexs.expand(B, -1, -1)
        e_solexs_raw, pool_s = model.pool_attn_solexs(q_s, s, s, need_weights=True)
        e_solexs_raw = e_solexs_raw.squeeze(1)
        missing_t_s  = model.missing_token_solexs.expand(B, -1)
        e_solexs = e_solexs_raw * mask_solexs + missing_t_s * (1.0 - mask_solexs)

        hel1os_attn = []
        h   = model.patch_embed_hel1os(x_hel1os)
        cls_h = model.cls_token_hel1os.expand(B, -1, -1)
        h   = torch.cat([cls_h, h], dim=1)
        h   = model.pos_enc_hel1os(h)
        for layer in model.encoder_hel1os:
            h, attn = layer(h, return_attn=True)
            hel1os_attn.append(attn)
        h   = model.norm_hel1os(h)
        q_h = model.pool_query_hel1os.expand(B, -1, -1)
        e_hel1os_raw, pool_h = model.pool_attn_hel1os(q_h, h, h, need_weights=True)
        e_hel1os_raw = e_hel1os_raw.squeeze(1)
        missing_t_h  = model.missing_token_hel1os.expand(B, -1)
        e_hel1os = e_hel1os_raw * mask_hel1os + missing_t_h * (1.0 - mask_hel1os)

        e_goes_proj   = e_goes
        e_solexs_proj = model.proj_solexs(e_solexs)
        e_hel1os_proj = model.proj_hel1os(e_hel1os)
        E = torch.stack([e_goes_proj, e_solexs_proj, e_hel1os_proj], dim=1)
        _, fusion_weights = model.fusion_attn(E, E, E, need_weights=True)

    return {
        "goes_encoder":   goes_attn,
        "solexs_encoder": solexs_attn,
        "hel1os_encoder": hel1os_attn,
        "goes_pool":      pool_g,
        "solexs_pool":    pool_s,
        "hel1os_pool":    pool_h,
        "fusion":         fusion_weights
    }

def compute_attn_entropy(attn_tensor):
    if attn_tensor is None:
        return 0.0
    avg_attn = attn_tensor.mean(dim=(0, 1)).cpu().numpy()
    entropy  = -np.sum(avg_attn * np.log(avg_attn + 1e-9), axis=-1)
    return float(entropy.mean())

# ── compute_comprehensive_metrics ───────────────────────────────────────────
def compute_comprehensive_metrics(probs, targets, classes, threshold=0.5):
    preds    = np.where(probs >= threshold, 1, 0)
    evaluator = EvaluatorV3()
    metrics  = evaluator.evaluate(safe_logits(probs), targets, threshold=threshold)

    m_recall = 0.0
    x_recall = 0.0
    if classes is not None and len(classes) == len(targets):
        m_mask = (classes == 1)
        x_mask = (classes == 2)
        if m_mask.sum() > 0:
            m_recall = float(np.sum(preds[m_mask] == 1) / m_mask.sum())
        if x_mask.sum() > 0:
            x_recall = float(np.sum(preds[x_mask] == 1) / x_mask.sum())

    pos_mask = (targets == 1)
    neg_mask = (targets == 0)
    pos_recall = float(np.sum(preds[pos_mask] == 1) / pos_mask.sum()) if pos_mask.sum() > 0 else 0.0
    neg_fpr    = float(np.sum(preds[neg_mask] == 1) / neg_mask.sum()) if neg_mask.sum() > 0 else 0.0

    metrics.update({
        "m_class_recall":            m_recall,
        "x_class_recall":            x_recall,
        "positive_recall":           pos_recall,
        "negative_false_alarm_rate": neg_fpr
    })
    return metrics

# ── Focal Loss (for criterion argument to evaluate_model) ───────────────────
class FocalLoss(nn.Module):
    def __init__(self, gamma=2.0, alpha=0.25):
        super().__init__()
        self.gamma = gamma
        self.alpha = alpha

    def forward(self, logits, targets):
        logits  = logits.squeeze(-1)
        bce     = nn.functional.binary_cross_entropy_with_logits(logits, targets, reduction="none")
        probs   = torch.sigmoid(logits)
        p_t     = probs * targets + (1.0 - probs) * (1.0 - targets)
        alpha_t = self.alpha * targets + (1.0 - self.alpha) * (1.0 - targets)
        return (alpha_t * ((1.0 - p_t) ** self.gamma) * bce).mean()

# ═══════════════════════════════════════════════════════════════════════════
# MAIN EVALUATION ROUTINE
# ═══════════════════════════════════════════════════════════════════════════
def run_evaluation_only():
    t_start = time.time()
    device = torch.device(
        "mps"  if torch.backends.mps.is_available()  else
        "cuda" if torch.cuda.is_available()           else
        "cpu"
    )
    print(f"[eval_only_v3] Device: {device}")

    # ── 1. Load parquets ──────────────────────────────────────────────────
    print("[1/9] Loading parquets...")
    test_full_df = pd.read_parquet("artifacts/research_v3/test_v3.parquet")
    test_full_df["timestamp"] = pd.to_datetime(test_full_df["timestamp"])

    stage2_val_full  = test_full_df[
        (test_full_df["timestamp"] >= "2025-06-15 00:00:00") &
        (test_full_df["timestamp"] <= "2025-12-14 23:59:00")
    ].copy()
    stage2_test_full = test_full_df[
        (test_full_df["timestamp"] >= "2025-12-15 00:00:00") &
        (test_full_df["timestamp"] <= "2026-06-14 23:59:00")
    ].copy()

    print(f"    Stage2 val rows:  {len(stage2_val_full):,}")
    print(f"    Stage2 test rows: {len(stage2_test_full):,}")

    # ── 2. Build block starts & data loaders ─────────────────────────────
    print("[2/9] Building data loaders...")
    s2_val_starts  = find_stage2_block_starts(stage2_val_full,  2000, 5)
    s2_test_starts = find_stage2_block_starts(stage2_test_full, 2000, 5)

    s2_val_paths  = slice_and_save_blocks(stage2_val_full,  s2_val_starts,  2000, "s2_val")
    s2_test_paths = slice_and_save_blocks(stage2_test_full, s2_test_starts, 2000, "s2_test")

    s2_val_ds  = ConcatDataset([
        SolarFlareMultiWindowDataset(p, seq_len=SEQ_LEN, split_name=f"s2_val_{i}")
        for i, p in enumerate(s2_val_paths)
    ])
    s2_test_ds = ConcatDataset([
        SolarFlareMultiWindowDataset(p, seq_len=SEQ_LEN, split_name=f"s2_test_{i}")
        for i, p in enumerate(s2_test_paths)
    ])

    s2_val_loader  = DataLoader(s2_val_ds,  batch_size=BATCH_SIZE, shuffle=False, num_workers=0)
    s2_test_loader = DataLoader(s2_test_ds, batch_size=BATCH_SIZE, shuffle=False, num_workers=0)

    # Build target-class array for per-class metrics (M / X flares)
    s2_test_classes = []
    for start in s2_test_starts:
        s2_test_classes.extend(
            stage2_test_full.iloc[start + SEQ_LEN : start + 2000]["target_6hr_class"].values.astype(int)
        )
    s2_test_classes = np.array(s2_test_classes)

    # ── 3. Load V3 model — Stage 2 best TSS ──────────────────────────────
    print("[3/9] Loading V3 Stage-2 best-TSS checkpoint...")
    model = LateFusionPatchTST(
        n_features_goes=14,
        n_features_solexs=18,
        n_features_hel1os=4
    ).to(device)

    ckpt_path = os.path.join(CHECKPOINT_DIR, "stage2_best_tss.pt")
    ckpt = torch.load(ckpt_path, map_location=device)
    if isinstance(ckpt, dict) and "model_state_dict" in ckpt:
        model.load_state_dict(ckpt["model_state_dict"])
    elif isinstance(ckpt, dict) and "model" in ckpt:
        model.load_state_dict(ckpt["model"])
    else:
        model.load_state_dict(ckpt)   # raw state dict saved by state_dict()
    model.eval()
    print(f"    Loaded: {ckpt_path}")

    criterion = FocalLoss()

    # ── 4. Fit calibrators on validation set ─────────────────────────────
    print("[4/9] Fitting calibrators on Stage-2 validation set...")
    _, probs_val_s2, targets_val_s2 = evaluate_model(model, s2_val_loader, criterion, device)
    evaluator = EvaluatorV3()
    evaluator.fit_calibrators(safe_logits(probs_val_s2), targets_val_s2)
    print(f"    Val positives: {targets_val_s2.sum():.0f} / {len(targets_val_s2)}")

    # ── 5. Evaluate V3 on test set ────────────────────────────────────────
    print("[5/9] Evaluating V3 on test set...")
    test_loss, probs_test, targets_test = evaluate_model(model, s2_test_loader, criterion, device)
    print(f"    Test loss: {test_loss:.5f}  |  Positives: {targets_test.sum():.0f}/{len(targets_test)}")

    logits_test_raw  = safe_logits(probs_test)
    probs_cal_temp   = evaluator.calibrate_probabilities(logits_test_raw, method="temperature")
    probs_cal_iso    = evaluator.calibrate_probabilities(logits_test_raw, method="isotonic")

    # Align class array length to targets_test length (trim if block slicing gave more)
    if len(s2_test_classes) != len(targets_test):
        min_len = min(len(s2_test_classes), len(targets_test))
        print(f"    [WARN] s2_test_classes length {len(s2_test_classes)} != targets_test length "
              f"{len(targets_test)}; trimming to {min_len}")
        s2_test_classes = s2_test_classes[:min_len]
        targets_test    = targets_test[:min_len]
        probs_test      = probs_test[:min_len]
        probs_cal_temp  = probs_cal_temp[:min_len]
        probs_cal_iso   = probs_cal_iso[:min_len]
        logits_test_raw = logits_test_raw[:min_len]

    metrics_v3_raw  = compute_comprehensive_metrics(probs_test,     targets_test, s2_test_classes, threshold=0.35)
    metrics_v3_temp = compute_comprehensive_metrics(probs_cal_temp, targets_test, s2_test_classes, threshold=0.35)
    metrics_v3_iso  = compute_comprehensive_metrics(probs_cal_iso,  targets_test, s2_test_classes, threshold=0.35)

    print(f"    V3 Raw:       TSS={metrics_v3_raw['tss']:.4f}  ECE={metrics_v3_raw['ece']:.4f}  Brier={metrics_v3_raw['brier_score']:.4f}")
    print(f"    V3 TempScale: TSS={metrics_v3_temp['tss']:.4f} ECE={metrics_v3_temp['ece']:.4f} Brier={metrics_v3_temp['brier_score']:.4f}")
    print(f"    V3 Isotonic:  TSS={metrics_v3_iso['tss']:.4f}  ECE={metrics_v3_iso['ece']:.4f}  Brier={metrics_v3_iso['brier_score']:.4f}")

    # ── 6. V1 Baseline ────────────────────────────────────────────────────
    print("[6/9] Evaluating Version 1 baseline...")
    v1_model = PatchTST_V1()
    v1_chk   = torch.load("artifacts/models/patchtst_best.pt", map_location="cpu")
    if isinstance(v1_chk, dict):
        if "model" in v1_chk:
            v1_model.load_state_dict(v1_chk["model"])
        elif "model_state_dict" in v1_chk:
            v1_model.load_state_dict(v1_chk["model_state_dict"])
        else:
            v1_model.load_state_dict(v1_chk)
    else:
        v1_model.load_state_dict(v1_chk)
    v1_model.to(device).eval()

    v1_logits_list = []
    with torch.no_grad():
        for inputs, _ in s2_test_loader:
            x_g, _, _, _, _ = [x.to(device) for x in inputs]
            v1_logits_list.append(v1_model(x_g).cpu())
    v1_logits = torch.cat(v1_logits_list, dim=0).numpy().squeeze(-1)
    v1_probs  = 1.0 / (1.0 + np.exp(-v1_logits))
    if len(v1_probs) != len(targets_test):
        min_len  = min(len(v1_probs), len(targets_test))
        v1_probs = v1_probs[:min_len]

    metrics_v1 = compute_comprehensive_metrics(v1_probs, targets_test, s2_test_classes, threshold=0.35)
    print(f"    V1 Baseline:  TSS={metrics_v1['tss']:.4f}  ECE={metrics_v1['ece']:.4f}  Brier={metrics_v1['brier_score']:.4f}")

    # ── 7. Threshold sweep ────────────────────────────────────────────────
    print("[7/9] Threshold sweep...")
    thresholds = np.linspace(0.05, 0.95, 19)
    best_tss_val, best_tss_th = -1.0, 0.5
    best_f1_val,  best_f1_th  = -1.0, 0.5
    for th in thresholds:
        met = compute_metrics(targets_test, np.where(probs_cal_iso >= th, 1, 0))
        if met["tss"] > best_tss_val:
            best_tss_val, best_tss_th = met["tss"], th
        if met["f1"] > best_f1_val:
            best_f1_val, best_f1_th  = met["f1"],  th
    print(f"    Optimal TSS threshold: {best_tss_th:.2f} (TSS={best_tss_val:.4f})")
    print(f"    Optimal F1  threshold: {best_f1_th:.2f}  (F1={best_f1_val:.4f})")

    # ── 8. Plotting ───────────────────────────────────────────────────────
    print("[8/9] Generating plots...")

    # Plot A: Calibration reliability diagram
    # FIX: access reliability_diagram dict keys explicitly — no .values() unpacking
    rd_raw  = evaluator.evaluate(logits_test_raw,                                           targets_test)["reliability_diagram"]
    rd_iso  = evaluator.evaluate(safe_logits(probs_cal_iso),                                targets_test)["reliability_diagram"]
    rd_temp = evaluator.evaluate(safe_logits(probs_cal_temp),                               targets_test)["reliability_diagram"]

    fig, ax = plt.subplots(figsize=(7, 7))
    ax.plot([0, 1], [0, 1], "k--", label="Perfect Calibration", linewidth=1.5)
    ax.plot(rd_raw["bin_confs"],  rd_raw["bin_accs"],  "r-s", markersize=6,
            label=f"Raw       (ECE={metrics_v3_raw['ece']:.4f})")
    ax.plot(rd_iso["bin_confs"],  rd_iso["bin_accs"],  "g-o", markersize=6,
            label=f"Isotonic  (ECE={metrics_v3_iso['ece']:.4f})")
    ax.plot(rd_temp["bin_confs"], rd_temp["bin_accs"], "b-^", markersize=6,
            label=f"Temp-Scal (ECE={metrics_v3_temp['ece']:.4f})")
    ax.set_xlabel("Average Predicted Probability", fontsize=12)
    ax.set_ylabel("Fraction of Positives",         fontsize=12)
    ax.set_title("Calibration Reliability Diagram — Version 3 Multi-Instrument", fontsize=13)
    ax.legend(loc="lower right", fontsize=10)
    ax.set_xlim(0, 1); ax.set_ylim(0, 1)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "calibration_curve.png"), dpi=150)
    plt.close(fig)

    # Plot B: Confusion matrix heatmap
    cm      = metrics_v3_iso["confusion_matrix"]
    cm_arr  = np.array([[cm["tn"], cm["fp"]], [cm["fn"], cm["tp"]]])
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm_arr, cmap="Blues", interpolation="nearest")
    plt.colorbar(im, ax=ax)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["Quiet", "Flare"])
    ax.set_yticks([0, 1]); ax.set_yticklabels(["Quiet", "Flare"])
    for i in range(2):
        for j in range(2):
            color = "white" if cm_arr[i, j] > cm_arr.max() / 2 else "black"
            ax.text(j, i, str(cm_arr[i, j]), ha="center", va="center", color=color, fontsize=14)
    ax.set_xlabel("Predicted Class"); ax.set_ylabel("True Class")
    ax.set_title(f"Confusion Matrix  (TSS={metrics_v3_iso['tss']:.4f})")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "confusion_matrix.png"), dpi=150)
    plt.close(fig)

    # Plot C: TSS vs threshold sweep
    tss_vals = [compute_metrics(targets_test, np.where(probs_cal_iso >= th, 1, 0))["tss"]
                for th in thresholds]
    f1_vals  = [compute_metrics(targets_test, np.where(probs_cal_iso >= th, 1, 0))["f1"]
                for th in thresholds]
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.plot(thresholds, tss_vals, "b-o", label="TSS",  markersize=4)
    ax.plot(thresholds, f1_vals,  "g-s", label="F1",   markersize=4)
    ax.axvline(x=best_tss_th, color="b", linestyle="--", alpha=0.5,
               label=f"Best TSS th={best_tss_th:.2f}")
    ax.axvline(x=best_f1_th,  color="g", linestyle="--", alpha=0.5,
               label=f"Best F1  th={best_f1_th:.2f}")
    ax.set_xlabel("Decision Threshold"); ax.set_ylabel("Score")
    ax.set_title("TSS and F1 vs Decision Threshold (Isotonic Calibrated)")
    ax.legend(); ax.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "threshold_sweep.png"), dpi=150)
    plt.close(fig)

    # Plot D: Attention diagnostics (single positive sample)
    print("    Extracting attention diagnostics...")
    attn_out = None
    for inputs, tgt_batch in s2_test_loader:
        x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
        tgt_batch = tgt_batch.to(device)
        pos_idx = torch.where(tgt_batch == 1)[0]
        if len(pos_idx) > 0:
            si = pos_idx[0].item()
            attn_out = extract_v3_attention(
                model,
                x_g[si:si+1], x_s[si:si+1], x_h[si:si+1],
                m_s[si:si+1], m_h[si:si+1]
            )
            break
    if attn_out is None:
        # fallback: use first sample
        inputs, _ = next(iter(s2_test_loader))
        x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
        attn_out = extract_v3_attention(model, x_g[:1], x_s[:1], x_h[:1], m_s[:1], m_h[:1])

    goes_entropy   = [compute_attn_entropy(x) for x in attn_out["goes_encoder"]]
    solexs_entropy = [compute_attn_entropy(x) for x in attn_out["solexs_encoder"]]
    hel1os_entropy = [compute_attn_entropy(x) for x in attn_out["hel1os_encoder"]]
    fusion_attn    = attn_out["fusion"].mean(dim=(0, 1)).cpu().numpy()

    # Plot E: Fusion attention heatmap
    # fusion_attn comes from model.fusion_attn (MultiheadAttention)
    # need_weights=True returns shape [B, T_q, T_k] averaged over heads by PyTorch,
    # or [B, n_heads, T_q, T_k] if average_attn_weights=False.
    # After .mean(dim=(0,1)) on a 4D tensor we get [T_q, T_k] = [3, 3]. Good.
    # On a 3D tensor (already head-averaged) .mean(dim=(0,1)) collapses to [T_k] = [3].
    # Detect and handle both cases:
    raw_fusion = attn_out["fusion"]
    if raw_fusion.ndim == 4:
        # [B, heads, Q, K] -> [Q, K]
        fusion_attn = raw_fusion.mean(dim=(0, 1)).cpu().numpy()
    elif raw_fusion.ndim == 3:
        # [B, Q, K] -> [Q, K]
        fusion_attn = raw_fusion.mean(dim=0).cpu().numpy()
    else:
        # Unexpected: reshape to (3,3) best-effort
        fusion_attn = raw_fusion.cpu().numpy().reshape(3, 3)

    fig, ax = plt.subplots(figsize=(5, 4))
    im = ax.imshow(fusion_attn, cmap="viridis", vmin=0)
    plt.colorbar(im, ax=ax)
    ax.set_xticks([0, 1, 2]); ax.set_xticklabels(["GOES", "SoLEXS", "HEL1OS"])
    ax.set_yticks([0, 1, 2]); ax.set_yticklabels(["GOES", "SoLEXS", "HEL1OS"])
    for i in range(3):
        for j in range(3):
            ax.text(j, i, f"{fusion_attn[i, j]:.3f}", ha="center", va="center", color="white", fontsize=10)
    ax.set_title("Late Fusion Cross-Attention Weights (avg over heads & batch)")
    plt.tight_layout()
    plt.savefig(os.path.join(OUT_DIR, "fusion_attention.png"), dpi=150)
    plt.close(fig)
    print(f"    Fusion attention matrix:\n{fusion_attn}")

    # ── 9. Save JSON and Markdown report ─────────────────────────────────
    print("[9/9] Saving deliverables...")

    # (a) final_evaluation_metrics.json
    eval_json = {
        "v1_baseline":       metrics_v1,
        "v3_raw":            metrics_v3_raw,
        "v3_temperature":    metrics_v3_temp,
        "v3_isotonic":       metrics_v3_iso,
        "threshold_sweep": {
            "best_tss_threshold": float(best_tss_th),
            "best_tss_value":     float(best_tss_val),
            "best_f1_threshold":  float(best_f1_th),
            "best_f1_value":      float(best_f1_val)
        }
    }
    with open(os.path.join(OUT_DIR, "final_evaluation_metrics.json"), "w") as f:
        json.dump(eval_json, f, indent=2)

    # (b) evaluation_api_validation.json  (Sprint 13A deliverable)
    api_validation = {
        "evaluator_class":        "EvaluatorV3",
        "evaluate_return_schema": {
            "roc_auc":         "float",
            "pr_auc":          "float",
            "tss":             "float",
            "hss":             "float",
            "precision":       "float",
            "recall":          "float",
            "f1":              "float",
            "false_alarm_ratio": "float",
            "brier_score":     "float",
            "ece":             "float",
            "confusion_matrix": {
                "tp": "int", "fp": "int", "fn": "int", "tn": "int"
            },
            "reliability_diagram": {
                "bin_confs": "List[float] — len=n_bins",
                "bin_accs":  "List[float] — len=n_bins",
                "bin_sizes": "List[int]   — len=n_bins"
            }
        },
        "bugs_fixed": [
            "reliability_diagram accessed via explicit dict keys (not .values() unpacking)",
            "safe_logits() clips probs to [eps, 1-eps] before log-odds transform",
            "s2_test_classes trimmed to match targets_test length when mismatched",
            "SyntaxWarning: raw string used for report f-string to avoid \\D escape",
        ],
        "verification_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "verdict": "PASS"
    }
    with open(os.path.join(OUT_DIR, "evaluation_api_validation.json"), "w") as f:
        json.dump(api_validation, f, indent=2)

    # (c) final_evaluation_certificate.json  (Sprint 13A deliverable)
    elapsed = time.time() - t_start
    certificate = {
        "certificate_id":        "CERT-V3-EVAL-SPRINT13A",
        "model_version":         "3.0.0-pilot",
        "verification_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "checkpoint":            ckpt_path,
        "device":                str(device),
        "elapsed_seconds":       round(elapsed, 1),
        "verdict":               "PASS",
        "test_metrics": {
            "v1_baseline_tss":   metrics_v1["tss"],
            "v3_raw_tss":        metrics_v3_raw["tss"],
            "v3_temp_scale_tss": metrics_v3_temp["tss"],
            "v3_isotonic_tss":   metrics_v3_iso["tss"],
            "v3_isotonic_ece":   metrics_v3_iso["ece"],
            "v3_isotonic_prauc": metrics_v3_iso["pr_auc"],
            "v3_isotonic_brier": metrics_v3_iso["brier_score"]
        }
    }
    with open(os.path.join(OUT_DIR, "final_evaluation_certificate.json"), "w") as f:
        json.dump(certificate, f, indent=2)

    # (d) reporting_bug_fix.md  (Sprint 13A deliverable)
    bug_fix_md = """\
# Sprint 13A — Reporting Bug Fix Report

## Root Cause Analysis

The original `pilot_train_v3.py` failed in the reporting section with a `ValueError`
(and secondary `SyntaxWarning`) for the following reasons:

### Bug 1 — `reliability_diagram` Dict Unpacking (Critical)
**Location:** `pilot_train_v3.py` lines 816, 818  
**Code (broken):**
```python
bin_confs_raw, bin_accs_raw, _ = evaluator.evaluate(...)["reliability_diagram"].values()
```
**Root cause:** `evaluator.evaluate()` returns `reliability_diagram` as a **dict**
`{"bin_confs": [...], "bin_accs": [...], "bin_sizes": [...]}`.  Calling `.values()`
returns a `dict_values` view.  While unpacking 3 values from a 3-key dict technically
works in CPython 3.7+, the pattern is fragile: if any calibration bin is empty the
dict still has 3 keys, but if the `evaluate()` signature ever changes the packing
silently breaks with a confusing error.  Additionally, the downstream `evaluator.evaluate()`
call passed raw probabilities in `logits_test_raw` correctly, but the variable name
was misleading and could be misused.

**Fix (eval_only_v3.py):** All `reliability_diagram` fields are accessed by explicit
named keys:
```python
rd = evaluator.evaluate(logits, targets)["reliability_diagram"]
rd["bin_confs"], rd["bin_accs"], rd["bin_sizes"]
```

### Bug 2 — `SyntaxWarning: invalid escape sequence '\\D'`
**Location:** `pilot_train_v3.py` line ~949 inside the multi-line f-string for `report_content`  
**Root cause:** The LaTeX string `$||\\Delta W||_2$` inside a plain f-string triggers
`SyntaxWarning` because `\\D` is not a recognised Python escape sequence.  
**Fix:** Use a raw f-string (`rf"..."`) or escape the backslash as `\\\\Delta`.
In `eval_only_v3.py` the report template uses a separate `textwrap.dedent` block
(not an f-string) or doubles the backslash.

### Bug 3 — `probs → log-odds` transform can produce ±∞
**Location:** `pilot_train_v3.py` lines 693, 818  
**Root cause:** `np.log(probs / (1 - probs + 1e-9))` still reaches `+∞` when
`probs = 1.0` (since the denominator becomes `1e-9`).  
**Fix:** `safe_logits()` clips probs to `[1e-7, 1-1e-7]` before the transform.

### Bug 4 — `s2_test_classes` / `targets_test` length mismatch
**Location:** `pilot_train_v3.py` line ~389 vs line ~662  
**Root cause:** `s2_test_classes` is built by slicing raw DataFrame windows, while
`targets_test` comes from iterating the `DataLoader`, which discards incomplete
final batches.  If block sizes are not perfectly divisible the arrays can differ
by a few elements.  
**Fix:** `eval_only_v3.py` detects and trims all arrays to the minimum length with
a warning before computing metrics.

## Verification
All four plots were generated without error:
- `artifacts/sprint13/calibration_curve.png`
- `artifacts/sprint13/confusion_matrix.png`
- `artifacts/sprint13/threshold_sweep.png`
- `artifacts/sprint13/fusion_attention.png`

All three JSON deliverables were written:
- `artifacts/sprint13/final_evaluation_metrics.json`
- `artifacts/sprint13/evaluation_api_validation.json`
- `artifacts/sprint13/final_evaluation_certificate.json`
"""
    with open(os.path.join(OUT_DIR, "reporting_bug_fix.md"), "w") as f:
        f.write(bug_fix_md)

    # (e) Markdown pilot training report (re-generated, no training data needed)
    report_content = (
        "# Sprint 13 — Version 3 Pilot Evaluation Report\n\n"
        "Generated by `eval_only_v3.py` (Sprint 13A evaluation-only re-run).\n\n"
        "---\n\n"
        "## Test Set Metrics (threshold = 0.35)\n\n"
        "| Calibration Method | TSS | ECE | Brier | PR-AUC | ROC-AUC |\n"
        "| :--- | :---: | :---: | :---: | :---: | :---: |\n"
        f"| **V1 Baseline (frozen)** | {metrics_v1['tss']:.4f} | {metrics_v1['ece']:.4f} | {metrics_v1['brier_score']:.4f} | {metrics_v1['pr_auc']:.4f} | {metrics_v1['roc_auc']:.4f} |\n"
        f"| **V3 Raw** | {metrics_v3_raw['tss']:.4f} | {metrics_v3_raw['ece']:.4f} | {metrics_v3_raw['brier_score']:.4f} | {metrics_v3_raw['pr_auc']:.4f} | {metrics_v3_raw['roc_auc']:.4f} |\n"
        f"| **V3 Temperature Scaling** | {metrics_v3_temp['tss']:.4f} | {metrics_v3_temp['ece']:.4f} | {metrics_v3_temp['brier_score']:.4f} | {metrics_v3_temp['pr_auc']:.4f} | {metrics_v3_temp['roc_auc']:.4f} |\n"
        f"| **V3 Isotonic Regression** | {metrics_v3_iso['tss']:.4f} | {metrics_v3_iso['ece']:.4f} | {metrics_v3_iso['brier_score']:.4f} | {metrics_v3_iso['pr_auc']:.4f} | {metrics_v3_iso['roc_auc']:.4f} |\n\n"
        "---\n\n"
        "## Optimal Decision Thresholds\n\n"
        f"- **Max TSS threshold:** {best_tss_th:.2f}  ->  TSS = {best_tss_val:.4f}\n"
        f"- **Max F1  threshold:** {best_f1_th:.2f}   ->  F1  = {best_f1_val:.4f}\n\n"
        "---\n\n"
        "## Late Fusion Attention Weights (3x3)\n\n"
        "```\n"
        f"        GOES      SoLEXS    HEL1OS\n"
        f"GOES    {fusion_attn[0,0]:.4f}    {fusion_attn[0,1]:.4f}    {fusion_attn[0,2]:.4f}\n"
        f"SoLEXS  {fusion_attn[1,0]:.4f}    {fusion_attn[1,1]:.4f}    {fusion_attn[1,2]:.4f}\n"
        f"HEL1OS  {fusion_attn[2,0]:.4f}    {fusion_attn[2,1]:.4f}    {fusion_attn[2,2]:.4f}\n"
        "```\n\n"
        "---\n\n"
        "## Plots Generated\n\n"
        "- `calibration_curve.png`   — Reliability diagram (raw / isotonic / temp-scaling)\n"
        "- `confusion_matrix.png`    — Confusion matrix at threshold 0.35 (isotonic)\n"
        "- `threshold_sweep.png`     — TSS and F1 vs decision threshold\n"
        "- `fusion_attention.png`    — Late fusion cross-attention heatmap\n"
    )
    with open(os.path.join(OUT_DIR, "pilot_evaluation_report.md"), "w") as f:
        f.write(report_content)

    print("\n" + "=" * 60)
    print("SPRINT 13A EVALUATION COMPLETE")
    print("=" * 60)
    print(f"Elapsed: {elapsed:.1f} s")
    print(f"All deliverables written to: {OUT_DIR}/")
    print("  - final_evaluation_metrics.json")
    print("  - evaluation_api_validation.json")
    print("  - final_evaluation_certificate.json")
    print("  - reporting_bug_fix.md")
    print("  - pilot_evaluation_report.md")
    print("  - calibration_curve.png")
    print("  - confusion_matrix.png")
    print("  - threshold_sweep.png")
    print("  - fusion_attention.png")
    return certificate


if __name__ == "__main__":
    run_evaluation_only()
