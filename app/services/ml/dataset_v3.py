"""
app/services/ml/dataset_v3.py

Memory-efficient sliding window dataset for Version 3 Multi-Instrument Late Fusion PatchTST.
Uses memory-mapped numpy arrays to avoid loading whole parquets into memory.
"""

import os
import json
import logging
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler

logger = logging.getLogger(__name__)

SEQ_LEN = 360
TARGET_COL = "target_6hr_binary"

class SolarFlareMultiWindowDataset(Dataset):
    """
    Sliding window dataset for GOES + SoLEXS + HEL1OS inputs with lazy loading.
    """

    def __init__(
        self,
        parquet_path: str,
        seq_len: int = SEQ_LEN,
        split_name: str = "unknown",
        use_mmap: bool = False,
    ):
        self.seq_len = seq_len
        self.split_name = split_name
        self.use_mmap = use_mmap

        # Load feature columns manifest
        with open("artifacts/feature_columns_v3.json") as f:
            v3_cols = json.load(f)
            
        self.goes_cols = v3_cols["goes"]
        self.solexs_cols = v3_cols["solexs"]
        self.hel1os_cols = v3_cols["hel1os"]
        
        cache_dir = "artifacts/sprint14c/cache"
        os.makedirs(cache_dir, exist_ok=True)
        
        # Generate cache names
        base_name = os.path.basename(parquet_path).replace(".parquet", "")
        prefix = f"{base_name}_{split_name}"
        
        cache_files = {
            "goes": os.path.join(cache_dir, f"{prefix}_goes.npy"),
            "solexs": os.path.join(cache_dir, f"{prefix}_solexs.npy"),
            "hel1os": os.path.join(cache_dir, f"{prefix}_hel1os.npy"),
            "mask_solexs": os.path.join(cache_dir, f"{prefix}_mask_solexs.npy"),
            "mask_hel1os": os.path.join(cache_dir, f"{prefix}_mask_hel1os.npy"),
            "labels": os.path.join(cache_dir, f"{prefix}_labels.npy"),
        }
        
        all_cached = all(os.path.exists(path) for path in cache_files.values())
        
        if not all_cached:
            logger.info(f"[{split_name}] Cache missing/incomplete. Loading parquet from {parquet_path}...")
            all_cols = self.goes_cols + self.solexs_cols + self.hel1os_cols + [TARGET_COL, "mask_solexs", "mask_hel1os"]
            df = pd.read_parquet(parquet_path, columns=all_cols)
            df = df.fillna(0.0)
            
            # Save cache
            np.save(cache_files["goes"], df[self.goes_cols].values.astype(np.float32))
            np.save(cache_files["solexs"], df[self.solexs_cols].values.astype(np.float32))
            np.save(cache_files["hel1os"], df[self.hel1os_cols].values.astype(np.float32))
            np.save(cache_files["mask_solexs"], df["mask_solexs"].values.astype(np.float32))
            np.save(cache_files["mask_hel1os"], df["mask_hel1os"].values.astype(np.float32))
            np.save(cache_files["labels"], df[TARGET_COL].values.astype(np.float32))
            
            del df
            import gc
            gc.collect()
            
        # Load arrays
        mmap_mode = "r" if use_mmap else None
        self.features_goes = np.load(cache_files["goes"], mmap_mode=mmap_mode)
        self.features_solexs = np.load(cache_files["solexs"], mmap_mode=mmap_mode)
        self.features_hel1os = np.load(cache_files["hel1os"], mmap_mode=mmap_mode)
        self.mask_solexs = np.load(cache_files["mask_solexs"], mmap_mode=mmap_mode)
        self.mask_hel1os = np.load(cache_files["mask_hel1os"], mmap_mode=mmap_mode)
        self.labels = np.load(cache_files["labels"], mmap_mode=mmap_mode)
        
        self.n_samples = len(self.labels) - self.seq_len
        if self.n_samples <= 0:
            raise ValueError(f"[{split_name}] Dataset too small for seq_len={seq_len}")

        pos = int(self.labels[self.seq_len:].sum())
        neg = self.n_samples - pos
        logger.info(
            f"[{split_name}] Loaded (mmap={use_mmap}) {self.n_samples:,} windows | "
            f"GOES={len(self.goes_cols)} | SoLEXS={len(self.solexs_cols)} | HEL1OS={len(self.hel1os_cols)} | "
            f"pos={pos:,} ({100*pos/self.n_samples:.2f}%) | neg={neg:,}"
        )

    def __len__(self) -> int:
        return self.n_samples

    def __getitem__(self, idx: int) -> tuple[tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor], torch.Tensor]:
        x_g = self.features_goes[idx : idx + self.seq_len]
        x_s = self.features_solexs[idx : idx + self.seq_len]
        x_h = self.features_hel1os[idx : idx + self.seq_len]
        
        m_s = self.mask_solexs[idx + self.seq_len]
        m_h = self.mask_hel1os[idx + self.seq_len]
        y = self.labels[idx + self.seq_len]
        
        return (
            torch.from_numpy(x_g),
            torch.from_numpy(x_s),
            torch.from_numpy(x_h),
            torch.tensor([m_s], dtype=torch.float32),
            torch.tensor([m_h], dtype=torch.float32)
        ), torch.tensor(y, dtype=torch.float32)

    def get_labels(self) -> np.ndarray:
        return self.labels[self.seq_len:]

def make_train_loader_v3(
    dataset: SolarFlareMultiWindowDataset,
    batch_size: int = 64,
    num_workers: int = 2,
) -> DataLoader:
    labels = dataset.get_labels()
    n_pos = int(labels.sum())
    n_neg = len(labels) - n_pos

    if n_pos == 0:
        raise ValueError("Training set contains zero positive flare windows.")

    weight_pos = 1.0 / n_pos
    weight_neg = 1.0 / n_neg
    sample_weights = np.where(labels == 1, weight_pos, weight_neg).astype(np.float64)

    sampler = WeightedRandomSampler(
        weights=torch.from_numpy(sample_weights),
        num_samples=len(dataset),
        replacement=True,
    )

    return DataLoader(
        dataset,
        batch_size=batch_size,
        sampler=sampler,
        num_workers=num_workers,
        pin_memory=False,
    )
