"""
app/services/ml/dataset.py

Memory-efficient sliding window dataset for SuryaNet PatchTST.

Design:
  - Pre-loads each parquet split as a numpy float32 array once at __init__.
  - Sliding window generation is on-the-fly via integer slicing (zero I/O per sample).
  - STRICT split isolation: train/val/test parquets are NEVER concatenated.
  - Provides WeightedRandomSampler factory for training DataLoader.

Memory budget:
  - Train  (~5.1M rows × 14 features × float32) ≈ 280 MB — well within 16GB M4.
  - Val    (~1.5M rows × 14 features × float32) ≈  84 MB.
  - Test   (~1.8M rows × 14 features × float32) ≈  98 MB.
"""

import json
import os
import logging
import numpy as np
import pandas as pd
import torch
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
FEATURE_COLUMNS_PATH = os.path.join("artifacts", "feature_columns.json")
SEQ_LEN = 360          # 360-minute input window
HORIZON = 360          # 6-hour forecast horizon (not used for indexing target here;
                       # target_6hr_binary is pre-computed in parquet)
TARGET_COL = "target_6hr_binary"


def _load_feature_columns() -> list[str]:
    with open(FEATURE_COLUMNS_PATH) as f:
        return json.load(f)


# ──────────────────────────────────────────────────────────────────────────────
# Dataset
# ──────────────────────────────────────────────────────────────────────────────
class SolarFlareWindowDataset(Dataset):
    """
    Sliding window dataset over a SINGLE parquet split.

    Args:
        parquet_path:   Absolute or relative path to the split parquet file.
        seq_len:        Input sequence length in minutes (default 360).
        feature_cols:   List of feature column names to use.
        split_name:     Human-readable split label for logging.

    Returns (per __getitem__):
        X: torch.float32 tensor of shape [seq_len, n_features]
        y: torch.float32 scalar tensor of shape []
    """

    def __init__(
        self,
        parquet_path: str,
        seq_len: int = SEQ_LEN,
        feature_cols: list[str] | None = None,
        split_name: str = "unknown",
    ):
        self.seq_len = seq_len
        self.split_name = split_name

        if feature_cols is None:
            feature_cols = _load_feature_columns()
        self.feature_cols = feature_cols

        logger.info(f"[{split_name}] Loading parquet from {parquet_path}...")
        df = pd.read_parquet(parquet_path, columns=self.feature_cols + [TARGET_COL])

        # Fill any residual NaNs with 0 (should be minimal after feature engineering)
        df = df.fillna(0.0)

        # Pre-cast to float32 immediately to save RAM
        self.features = df[self.feature_cols].values.astype(np.float32)
        self.labels   = df[TARGET_COL].values.astype(np.float32)

        # Number of valid windows
        self.n_samples = len(self.features) - self.seq_len
        if self.n_samples <= 0:
            raise ValueError(
                f"[{split_name}] Dataset too small for seq_len={seq_len}: "
                f"only {len(self.features)} rows available."
            )

        pos = int(self.labels[self.seq_len:].sum())
        neg = self.n_samples - pos
        logger.info(
            f"[{split_name}] Loaded {self.n_samples:,} windows | "
            f"features={len(self.feature_cols)} | pos={pos:,} ({100*pos/self.n_samples:.2f}%) | neg={neg:,}"
        )

    def __len__(self) -> int:
        return self.n_samples

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor]:
        x = self.features[idx : idx + self.seq_len]          # [seq_len, n_features]
        y = self.labels[idx + self.seq_len]                   # scalar (label at end of window)
        return torch.from_numpy(x), torch.tensor(y, dtype=torch.float32)

    def get_labels(self) -> np.ndarray:
        """Return the target labels for all valid windows (used by WeightedRandomSampler)."""
        return self.labels[self.seq_len:]


# ──────────────────────────────────────────────────────────────────────────────
# DataLoader factories
# ──────────────────────────────────────────────────────────────────────────────
def make_train_loader(
    dataset: SolarFlareWindowDataset,
    batch_size: int = 64,
    num_workers: int = 2,
) -> DataLoader:
    """
    Training DataLoader with WeightedRandomSampler.

    WeightedRandomSampler over-samples rare positive flare windows so each
    training batch contains a balanced mix of flare / no-flare windows.
    This is combined with Focal Loss for a dual class-balancing strategy.
    """
    labels = dataset.get_labels()
    n_pos  = int(labels.sum())
    n_neg  = len(labels) - n_pos

    if n_pos == 0:
        raise ValueError("Training set contains zero positive flare windows.")

    # Weight each sample inversely proportional to its class frequency
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
        sampler=sampler,            # replaces shuffle=True
        num_workers=num_workers,
        prefetch_factor=2 if num_workers > 0 else None,
        pin_memory=False,           # MPS doesn't benefit from pinned memory
        persistent_workers=num_workers > 0,
    )


def make_eval_loader(
    dataset: SolarFlareWindowDataset,
    batch_size: int = 128,
    num_workers: int = 2,
    shuffle: bool = True,
) -> DataLoader:
    """
    Validation / Test DataLoader.

    shuffle=True (default) ensures positive examples are distributed across
    batches when using a steps cap — sequential ordering would otherwise place
    all positives in later batches and produce val_ROC=nan.
    Set shuffle=False only for final ordered test-set evaluation.
    """
    return DataLoader(
        dataset,
        batch_size=batch_size,
        shuffle=shuffle,
        num_workers=num_workers,
        prefetch_factor=2 if num_workers > 0 else None,
        pin_memory=False,
        persistent_workers=num_workers > 0,
    )
