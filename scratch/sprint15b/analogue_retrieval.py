"""
scratch/sprint15b/analogue_retrieval.py

Task: Historical Analogue Retrieval.
Extracts model embeddings, builds a historical database from the training set,
and retrieves the Top 5 most similar historical windows for selected test samples.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader, Subset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from utils import get_device, load_model, load_datasets, get_loaders

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Train parquet path for dataset loading
TRAIN_PARQUET = "artifacts/sprint14c/s2_train.parquet"

def extract_embeddings(model, loader, device, limit=None):
    model.eval()
    embeddings = []
    targets = []
    indices = []
    
    count = 0
    with torch.no_grad():
        for batch_idx, (inputs, batch_targets) in enumerate(loader):
            x_g, x_s, x_h, m_s, m_h = [x.to(device) for x in inputs]
            
            # Step-by-step model execution to get fused_flat
            with torch.amp.autocast(device_type=device.type, enabled=True, dtype=torch.bfloat16):
                # 1. GOES Branch
                g = model.patch_embed_goes(x_g)
                cls_g = model.cls_token_goes.expand(x_g.size(0), -1, -1)
                g = torch.cat([cls_g, g], dim=1)
                g = model.pos_enc_goes(g)
                for layer in model.encoder_goes:
                    g, _ = layer(g)
                g = model.norm_goes(g)
                q_g = model.pool_query_goes.expand(x_g.size(0), -1, -1)
                e_goes, _ = model.pool_attn_goes(q_g, g, g)
                e_goes = e_goes.squeeze(1)

                # 2. SoLEXS Branch
                if x_s is None:
                    e_solexs = model.missing_token_solexs.expand(x_g.size(0), -1)
                else:
                    s = model.patch_embed_solexs(x_s)
                    cls_s = model.cls_token_solexs.expand(x_g.size(0), -1, -1)
                    s = torch.cat([cls_s, s], dim=1)
                    s = model.pos_enc_solexs(s)
                    for layer in model.encoder_solexs:
                        s, _ = layer(s)
                    s = model.norm_solexs(s)
                    q_s = model.pool_query_solexs.expand(x_g.size(0), -1, -1)
                    e_solexs_raw, _ = model.pool_attn_solexs(q_s, s, s)
                    e_solexs_raw = e_solexs_raw.squeeze(1)
                    missing_t_s = model.missing_token_solexs.expand(x_g.size(0), -1)
                    e_solexs = e_solexs_raw * m_s + missing_t_s * (1.0 - m_s)

                # 3. HEL1OS Branch
                if x_h is None:
                    e_hel1os = model.missing_token_hel1os.expand(x_g.size(0), -1)
                else:
                    h = model.patch_embed_hel1os(x_h)
                    cls_h = model.cls_token_hel1os.expand(x_g.size(0), -1, -1)
                    h = torch.cat([cls_h, h], dim=1)
                    h = model.pos_enc_hel1os(h)
                    for layer in model.encoder_hel1os:
                        h, _ = layer(h)
                    h = model.norm_hel1os(h)
                    q_h = model.pool_query_hel1os.expand(x_g.size(0), -1, -1)
                    e_hel1os_raw, _ = model.pool_attn_hel1os(q_h, h, h)
                    e_hel1os_raw = e_hel1os_raw.squeeze(1)
                    missing_t_h = model.missing_token_hel1os.expand(x_g.size(0), -1)
                    e_hel1os = e_hel1os_raw * m_h + missing_t_h * (1.0 - m_h)

                # 4. Projections & Fusion
                e_goes_proj = e_goes
                e_solexs_proj = model.proj_solexs(e_solexs)
                e_hel1os_proj = model.proj_hel1os(e_hel1os)

                E = torch.stack([e_goes_proj, e_solexs_proj, e_hel1os_proj], dim=1)
                E_fused, _ = model.fusion_attn(E, E, E)
                fused_flat = E_fused.flatten(start_dim=1)  # [B, 384]

            embeddings.append(fused_flat.float().cpu().numpy())
            targets.append(batch_targets.numpy())
            
            # Record global indices
            start_idx = batch_idx * loader.batch_size
            end_idx = start_idx + x_g.size(0)
            indices.extend(list(range(start_idx, end_idx)))
            
            count += x_g.size(0)
            if limit is not None and count >= limit:
                break
                
    return np.concatenate(embeddings), np.concatenate(targets), np.array(indices)

def main():
    device = get_device()
    logger.info("Loading model and datasets...")
    model = load_model(device)
    val_ds, test_ds = load_datasets()
    
    # Load training set
    from app.services.ml.dataset_v3 import SolarFlareMultiWindowDataset
    logger.info("Loading training dataset for analogue database...")
    train_ds = SolarFlareMultiWindowDataset(TRAIN_PARQUET, seq_len=360, split_name="s2_train")
    
    # Select 30,000 random training samples for database efficiency
    np.random.seed(42)
    db_size = 30000
    db_indices = np.random.choice(len(train_ds), db_size, replace=False)
    db_subset = Subset(train_ds, db_indices)
    db_loader = DataLoader(db_subset, batch_size=256, shuffle=False, num_workers=0, pin_memory=False)
    
    logger.info("Extracting embeddings for historical database (30,000 training windows)...")
    db_embeddings, db_targets, _ = extract_embeddings(model, db_loader, device)
    
    # Normalize database embeddings for cosine similarity
    db_norms = np.linalg.norm(db_embeddings, axis=1, keepdims=True)
    db_embeddings_normed = db_embeddings / (db_norms + 1e-9)
    
    # Let's select a set of test samples to run retrieval for
    # We will retrieve for:
    # 1. 20 representative test samples (let's say indices 10000, 20000, 30000, etc.)
    # 2. Selected failure cases or casebook cases
    np.random.seed(42)
    test_indices = np.random.choice(len(test_ds), 200, replace=False)
    test_subset = Subset(test_ds, test_indices)
    test_loader = DataLoader(test_subset, batch_size=64, shuffle=False, num_workers=0, pin_memory=False)
    
    logger.info("Extracting embeddings for test queries (200 test windows)...")
    test_embeddings, test_targets_sel, test_global_indices = extract_embeddings(model, test_loader, device)
    
    # Normalize query embeddings
    test_norms = np.linalg.norm(test_embeddings, axis=1, keepdims=True)
    test_embeddings_normed = test_embeddings / (test_norms + 1e-9)
    
    # Compute similarity matrix: shape [200, 30000]
    logger.info("Computing similarity matrix and retrieving nearest analogues...")
    similarity_matrix = np.matmul(test_embeddings_normed, db_embeddings_normed.T)
    
    # Load timestamps
    df_test = pd.read_parquet("artifacts/sprint14c/s2_test.parquet", columns=["timestamp"])
    timestamps_test = df_test["timestamp"].values[360:]
    df_train = pd.read_parquet("artifacts/sprint14c/s2_train.parquet", columns=["timestamp"])
    timestamps_train = df_train["timestamp"].values[360:]
    
    analogue_results = {}
    for i, test_idx in enumerate(test_global_indices):
        query_timestamp = str(timestamps_test[test_idx])
        query_target = int(test_targets_sel[i])
        
        # Get Top 5 analogues
        sims = similarity_matrix[i]
        top_5_idx_local = np.argsort(sims)[::-1][:5]
        
        analogues = []
        for idx_local in top_5_idx_local:
            train_global_idx = db_indices[idx_local]
            similarity = float(sims[idx_local])
            outcome = int(db_targets[idx_local])
            timestamp_analogue = str(timestamps_train[train_global_idx])
            
            analogues.append({
                "historical_timestamp": timestamp_analogue,
                "historical_train_index": int(train_global_idx),
                "similarity_score": similarity,
                "outcome": outcome
            })
            
        analogue_results[int(test_idx)] = {
            "query_timestamp": query_timestamp,
            "query_target": query_target,
            "analogues": analogues
        }
        
    os.makedirs("artifacts/sprint15b", exist_ok=True)
    with open("analogue_retrieval.json", "w") as f:
        json.dump(analogue_results, f, indent=2)
    with open("artifacts/sprint15b/analogue_retrieval.json", "w") as f:
        json.dump(analogue_results, f, indent=2)
        
    logger.info("Task 8 completed successfully.")
    print("ANALOGUE_RETRIEVAL: PASS")

if __name__ == "__main__":
    main()
