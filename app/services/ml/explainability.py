"""
app/services/ml/explainability.py

Sprint 5.5 — Explainability Layer

Extracts and interprets CLS attention maps from PatchTST.

For each prediction, returns the top-3 attended time-series patches mapped
back to wall-clock timestamps and enriched with physical context from the
original GOES telemetry:
  - long_flux value
  - flux_gradient (dFlux/dt)
  - rolling_variance (30-min window)

Architecture reminder:
  - 44 patch tokens + 1 CLS token = 45 tokens total
  - Each patch covers 16 minutes of data at stride 8
  - Patch k starts at time index: k * stride = k * 8
  - Patch k ends   at time index: k * stride + patch_len - 1 = k * 8 + 15
"""

import logging
import numpy as np
import pandas as pd
import torch

from app.services.ml.model import PatchTST, extract_attention_maps

logger = logging.getLogger(__name__)

# PatchTST architecture constants (must match model.py)
PATCH_LEN = 16
STRIDE    = 8
N_PATCHES = 44
N_TOKENS  = 45  # CLS + 44 patches


def _get_patch_center_idx(patch_idx: int) -> int:
    """Return the center time-step index of patch k in the 360-step input window."""
    start = patch_idx * STRIDE
    end   = start + PATCH_LEN - 1
    return (start + end) // 2


def _aggregate_attention_maps(attn_maps: list[torch.Tensor]) -> np.ndarray:
    """
    Aggregate per-head, per-layer attention maps to a single patch
    importance vector of shape [N_PATCHES].

    Strategy:
      1. For each layer: average attention weights across all heads → [n_tokens, n_tokens]
      2. Extract CLS row (row 0): attention from CLS to all other tokens → [n_tokens]
      3. Drop CLS-to-CLS entry (index 0) → [N_PATCHES]
      4. Average across all 4 layers → [N_PATCHES]
      5. Normalise to sum to 1 (relative attention share).
    """
    layer_vectors = []
    for layer_attn in attn_maps:
        # layer_attn: [1, n_heads, n_tokens, n_tokens]  (batch=1)
        attn_np = layer_attn.squeeze(0).detach().cpu().numpy()   # [n_heads, n_tokens, n_tokens]
        head_avg = attn_np.mean(axis=0)                           # [n_tokens, n_tokens]
        cls_row  = head_avg[0, :]                                 # [n_tokens] – CLS → everything
        patch_attn = cls_row[1:]                                  # [N_PATCHES] – drop CLS→CLS
        layer_vectors.append(patch_attn)

    # Average over layers
    mean_attn = np.mean(layer_vectors, axis=0)   # [N_PATCHES]

    # Normalise
    total = mean_attn.sum()
    if total > 1e-9:
        mean_attn = mean_attn / total
    return mean_attn  # [N_PATCHES]


def _compute_physical_context(
    df_input: pd.DataFrame,
    patch_center_idx: int,
) -> dict:
    """
    Compute physical context features at the patch center time step.

    Args:
        df_input:         Original 360-row input DataFrame (sorted by timestamp).
                          Must contain 'timestamp', 'long_flux' columns.
        patch_center_idx: Center time-step index within the 360-step window.

    Returns:
        dict with flux_value, flux_gradient (W/m²/min), rolling_variance
    """
    idx = min(patch_center_idx, len(df_input) - 1)

    flux_val = float(df_input["long_flux"].iloc[idx])

    # Gradient: finite difference over ±4 minutes (8 steps)
    idx_lo = max(0, idx - 4)
    idx_hi = min(len(df_input) - 1, idx + 4)
    dt = idx_hi - idx_lo  # in minutes
    if dt > 0:
        gradient = float(
            (df_input["long_flux"].iloc[idx_hi] - df_input["long_flux"].iloc[idx_lo]) / dt
        )
    else:
        gradient = 0.0

    # Rolling variance: 30-min window centred on idx
    win_lo = max(0, idx - 15)
    win_hi = min(len(df_input) - 1, idx + 15)
    variance = float(df_input["long_flux"].iloc[win_lo:win_hi + 1].var())

    return {
        "flux_value_W_m2":        round(flux_val, 12),
        "flux_gradient_W_m2_min": round(gradient, 14),
        "rolling_variance_30min": round(variance, 14) if not np.isnan(variance) else 0.0,
    }


def get_top_attention_patches(
    model: PatchTST,
    x: torch.Tensor,
    df_input: pd.DataFrame,
    top_k: int = 3,
) -> list[dict]:
    """
    Extract the top-k most attended patches for a single prediction window.

    Args:
        model:    PatchTST instance (will be set to eval mode).
        x:        Input tensor of shape [1, 360, n_features].
        df_input: Original 360-row DataFrame aligned with x (sorted, reset index).
                  Must have 'timestamp' and 'long_flux' columns.
        top_k:    Number of top patches to return (default 3).

    Returns:
        List of dicts, each containing:
          {
            "rank":             int,         # 1 = most attended
            "patch_index":      int,         # 0-based patch index
            "timestamp":        str,         # ISO 8601 timestamp of patch centre
            "attention_share":  float,       # fraction of total attention
            "physical_context": dict
          }
    """
    model.eval()

    with torch.no_grad():
        attn_maps = extract_attention_maps(model, x)

    patch_importance = _aggregate_attention_maps(attn_maps)   # [44]
    top_indices = np.argsort(patch_importance)[::-1][:top_k]

    results = []
    for rank, patch_idx in enumerate(top_indices, start=1):
        center_idx    = _get_patch_center_idx(int(patch_idx))
        # Clamp to valid range (edge patches may push centre out of bounds)
        center_idx    = min(center_idx, len(df_input) - 1)
        ts            = df_input["timestamp"].iloc[center_idx]
        ts_str        = str(ts) if not isinstance(ts, str) else ts
        attn_share    = float(patch_importance[patch_idx])
        phys          = _compute_physical_context(df_input, center_idx)

        results.append({
            "rank":             rank,
            "patch_index":      int(patch_idx),
            "timestamp":        ts_str,
            "attention_share":  round(attn_share, 6),
            "physical_context": phys,
        })

    logger.debug(f"Top-{top_k} patches: {[r['patch_index'] for r in results]}")
    return results
