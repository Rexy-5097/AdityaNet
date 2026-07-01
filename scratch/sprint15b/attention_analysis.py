"""
scratch/sprint15b/attention_analysis.py

Task 3: Attention Analysis.
Computes attention rollout, entropy, concentration, and consistency for GOES, SoLEXS, and HEL1OS encoders,
comparing True Positives (TP) vs. False Positives (FP).
"""

import os
import sys
import json
import logging
import numpy as np
import torch
from torch.utils.data import DataLoader

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_device, load_model, load_datasets, get_calibrators_and_threshold

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

def compute_entropy(matrix):
    # matrix shape: [N_tokens, N_tokens]
    entropy = - np.sum(matrix * np.log(matrix + 1e-9), axis=-1)
    return np.mean(entropy)

def compute_concentration(matrix, k=5):
    # matrix shape: [N_tokens, N_tokens]
    sorted_weights = np.sort(matrix, axis=-1)[:, ::-1]
    top_k_sum = np.sum(sorted_weights[:, :k], axis=-1)
    return np.mean(top_k_sum)

def compute_rollout(layers_attn):
    # layers_attn: list of numpy arrays, each of shape [num_heads, 45, 45]
    # We first average over heads for each layer
    rollout = np.eye(45, dtype=np.float32)
    for attn in layers_attn:
        # Average over heads: [45, 45]
        mean_attn = np.mean(attn, axis=0)
        # Add residual connection: A_tilde = 0.5 * mean_attn + 0.5 * I
        A_tilde = 0.5 * mean_attn + 0.5 * np.eye(45, dtype=np.float32)
        # Re-normalize to sum to 1.0 (just to handle precision errors)
        row_sums = A_tilde.sum(axis=-1, keepdims=True)
        A_tilde = A_tilde / (row_sums + 1e-9)
        # Multiply: Rollout = A_tilde * Rollout
        rollout = np.matmul(A_tilde, rollout)
    return rollout

def compute_cross_head_consistency(layers_attn):
    # Compute cross-head consistency of the CLS token attention in the final layer
    # attn shape: [num_heads, 45, 45]
    final_layer_attn = layers_attn[-1]
    num_heads = final_layer_attn.shape[0]
    cls_attns = final_layer_attn[:, 0, :]  # [num_heads, 45]
    
    # Normalize rows
    norms = np.linalg.norm(cls_attns, axis=-1, keepdims=True)
    normed_cls = cls_attns / (norms + 1e-9)
    
    # Compute pair-wise cosine similarity
    similarities = []
    for i in range(num_heads):
        for j in range(i + 1, num_heads):
            sim = np.dot(normed_cls[i], normed_cls[j])
            similarities.append(sim)
            
    return float(np.mean(similarities)) if similarities else 1.0

def extract_branch_attention(model, x_g, x_s, x_h, m_s, m_h, device):
    """
    Runs the model encoders step-by-step to capture layer-by-layer attention weights.
    Returns:
        goes_attn: list of [num_heads, 45, 45] arrays
        solexs_attn: list of [num_heads, 45, 45] arrays (or None if masked)
        hel1os_attn: list of [num_heads, 45, 45] arrays (or None if masked)
    """
    B = x_g.size(0)
    assert B == 1, "Batch size must be 1 for detailed attention extraction"
    
    # GOES branch
    g = model.patch_embed_goes(x_g)
    cls_g = model.cls_token_goes.expand(B, -1, -1)
    g = torch.cat([cls_g, g], dim=1)
    g = model.pos_enc_goes(g)
    
    goes_attn = []
    for layer in model.encoder_goes:
        g, attn = layer(g, return_attn=True)
        goes_attn.append(attn.cpu().numpy()[0])  # Shape [num_heads, 45, 45]
        
    # SoLEXS branch
    solexs_attn = []
    if x_s is not None and m_s[0].item() == 1.0:
        s = model.patch_embed_solexs(x_s)
        cls_s = model.cls_token_solexs.expand(B, -1, -1)
        s = torch.cat([cls_s, s], dim=1)
        s = model.pos_enc_solexs(s)
        for layer in model.encoder_solexs:
            s, attn = layer(s, return_attn=True)
            solexs_attn.append(attn.cpu().numpy()[0])
    else:
        solexs_attn = None
        
    # HEL1OS branch
    hel1os_attn = []
    if x_h is not None and m_h[0].item() == 1.0:
        h = model.patch_embed_hel1os(x_h)
        cls_h = model.cls_token_hel1os.expand(B, -1, -1)
        h = torch.cat([cls_h, h], dim=1)
        h = model.pos_enc_hel1os(h)
        for layer in model.encoder_hel1os:
            h, attn = layer(h, return_attn=True)
            hel1os_attn.append(attn.cpu().numpy()[0])
    else:
        hel1os_attn = None
        
    return goes_attn, solexs_attn, hel1os_attn

def analyze_branch(attn_list):
    """
    Computes rollout, CLS distribution, average entropy, average concentration, consistency.
    """
    # 1. Rollout
    rollout = compute_rollout(attn_list)
    cls_dist = rollout[0, :].tolist()
    
    # 2. Entropy and Concentration (averaged over all layers)
    entropies = []
    concentrations = []
    for attn in attn_list:
        mean_attn = np.mean(attn, axis=0)
        entropies.append(compute_entropy(mean_attn))
        concentrations.append(compute_concentration(mean_attn))
        
    avg_entropy = float(np.mean(entropies))
    avg_concentration = float(np.mean(concentrations))
    
    # 3. Consistency
    consistency = compute_cross_head_consistency(attn_list)
    
    return {
        "rollout_cls_distribution": cls_dist,
        "average_attention_entropy": avg_entropy,
        "attention_concentration": avg_concentration,
        "attention_consistency": consistency
    }

def main():
    device = get_device()
    logger.info("Loading model and datasets...")
    model = load_model(device)
    val_ds, test_ds = load_datasets()
    
    val_loader = DataLoader(val_ds, batch_size=128, shuffle=False, num_workers=0, pin_memory=False)
    logger.info("Fitting calibrators and getting validation threshold...")
    evaluator, best_th = get_calibrators_and_threshold(model, val_loader, device)
    
    # Run test loader to get TPs and FPs indices
    logger.info("Evaluating test set to identify TP and FP samples...")
    test_loader = DataLoader(test_ds, batch_size=128, shuffle=False, num_workers=0, pin_memory=False)
    test_probs = []
    test_targets = []
    test_mask_s = []
    test_mask_h = []
    with torch.no_grad():
        for inputs, targets in test_loader:
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            with torch.amp.autocast(device_type=device.type, enabled=True, dtype=torch.bfloat16):
                logits = model(x_g, x_s, x_h, m_s, m_h)
            probs = torch.sigmoid(logits).squeeze(-1).float().cpu().numpy()
            test_probs.append(probs)
            test_targets.append(targets.numpy())
            test_mask_s.append(m_s.cpu().numpy().squeeze(-1))
            test_mask_h.append(m_h.cpu().numpy().squeeze(-1))
            
    test_probs = np.concatenate(test_probs)
    test_targets = np.concatenate(test_targets)
    test_mask_s = np.concatenate(test_mask_s)
    test_mask_h = np.concatenate(test_mask_h)
    
    test_logits = np.log(test_probs / (1.0 - test_probs + 1e-9))
    cal_probs = evaluator.calibrate_probabilities(test_logits, method="isotonic")
    
    preds = (cal_probs >= best_th).astype(int)
    
    # Find TP and FP indices
    tp_indices = np.where((test_targets == 1) & (preds == 1))[0]
    fp_indices = np.where((test_targets == 0) & (preds == 1))[0]
    
    logger.info(f"Found {len(tp_indices)} TPs and {len(fp_indices)} FPs in test set.")
    
    # We will sample up to 100 TPs and 100 FPs to compute average statistics quickly
    np.random.seed(42)
    sample_size = 100
    sampled_tps = np.random.choice(tp_indices, min(sample_size, len(tp_indices)), replace=False)
    sampled_fps = np.random.choice(fp_indices, min(sample_size, len(fp_indices)), replace=False)
    
    results = {
        "GOES": {"TP": [], "FP": []},
        "SoLEXS": {"TP": [], "FP": []},
        "HEL1OS": {"TP": [], "FP": []}
    }
    
    def process_group(indices, label):
        logger.info(f"Processing group: {label} (count={len(indices)})...")
        for i in indices:
            inputs, _ = test_ds[i]
            x_g, x_s, x_h, m_s, m_h = [torch.from_numpy(x).unsqueeze(0).to(device) if isinstance(x, np.ndarray) else x.unsqueeze(0).to(device) for x in inputs]
            
            with torch.no_grad():
                g_attn, s_attn, h_attn = extract_branch_attention(model, x_g, x_s, x_h, m_s, m_h, device)
                
            # Process GOES
            results["GOES"][label].append(analyze_branch(g_attn))
            
            # Process SoLEXS
            if s_attn is not None:
                results["SoLEXS"][label].append(analyze_branch(s_attn))
                
            # Process HEL1OS
            if h_attn is not None:
                results["HEL1OS"][label].append(analyze_branch(h_attn))
                
    process_group(sampled_tps, "TP")
    process_group(sampled_fps, "FP")
    
    # Average the stats over samples in each group
    final_stats = {}
    for branch in ["GOES", "SoLEXS", "HEL1OS"]:
        final_stats[branch] = {}
        for label in ["TP", "FP"]:
            group_list = results[branch][label]
            if not group_list:
                final_stats[branch][label] = "N/A (No active samples)"
                continue
                
            rollout_dists = [g["rollout_cls_distribution"] for g in group_list]
            avg_rollout = np.mean(rollout_dists, axis=0).tolist()
            avg_entropy = float(np.mean([g["average_attention_entropy"] for g in group_list]))
            avg_concentration = float(np.mean([g["attention_concentration"] for g in group_list]))
            avg_consistency = float(np.mean([g["attention_consistency"] for g in group_list]))
            
            final_stats[branch][label] = {
                "average_attention_entropy": avg_entropy,
                "attention_concentration": avg_concentration,
                "attention_consistency": avg_consistency,
                "rollout_cls_distribution": avg_rollout
            }
            
    os.makedirs("artifacts/sprint15b", exist_ok=True)
    with open("attention_statistics.json", "w") as f:
        json.dump(final_stats, f, indent=2)
    with open("artifacts/sprint15b/attention_statistics.json", "w") as f:
        json.dump(final_stats, f, indent=2)
        
    logger.info("Task 3 completed successfully.")
    print("ATTENTION_ANALYSIS: PASS")

if __name__ == "__main__":
    main()
