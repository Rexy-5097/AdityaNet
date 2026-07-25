"""
app/services/ml/model.py

PatchTST architecture for SuryaNet solar flare binary forecasting.

Design (CLS-token variant, multivariate-patch):
  - Input:      [batch, seq_len=360, n_features=14]
  - Patching:   Overlapping patches: patch_len=16, stride=8 → 44 patches
  - Per patch:  Flatten [16 × 14 = 224] → Linear → 128-d embedding
  - CLS token:  Prepend learnable CLS → 45 tokens total
  - Transformer: 4 encoder layers, 8 heads, dim_feedforward=512, dropout=0.2
  - Head:       CLS token output (index 0) → Linear(128, 1) → logit

  Model outputs RAW LOGITS. Sigmoid is applied at inference only.

Parameter constraint: < 10,000,000 parameters (asserted at init).

MC Dropout uncertainty: keep dropout active at inference via model.train().
Attention maps: extractable via extract_attention_maps() for interpretability.
"""

import math
import logging
import torch
import torch.nn as nn
import torch.nn.functional as F

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────
SEQ_LEN      = 360
PATCH_LEN    = 16
STRIDE       = 8
N_FEATURES   = 14    # from feature_columns.json
N_PATCHES    = (SEQ_LEN - PATCH_LEN) // STRIDE + 1   # = 44
N_TOKENS     = N_PATCHES + 1                           # = 45 (44 patches + CLS)
PATCH_DIM    = PATCH_LEN * N_FEATURES                 # = 224
EMBED_DIM    = 128
N_HEADS      = 8
N_LAYERS     = 4
FF_DIM       = 512
DROPOUT      = 0.2
MAX_PARAMS   = 10_000_000


# ──────────────────────────────────────────────────────────────────────────────
# Sinusoidal Positional Encoding (for N_TOKENS = 45 positions)
# ──────────────────────────────────────────────────────────────────────────────
class PositionalEncoding(nn.Module):
    """Fixed sinusoidal PE for N_TOKENS positions (CLS + 44 patches)."""

    def __init__(self, d_model: int, max_len: int = N_TOKENS, dropout: float = DROPOUT):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, n_tokens, embed_dim]  (n_tokens = 45)
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)


# ──────────────────────────────────────────────────────────────────────────────
# Patch Embedding
# ──────────────────────────────────────────────────────────────────────────────
class PatchEmbedding(nn.Module):
    """
    Extracts overlapping patches from a multivariate time series and
    projects each patch to embed_dim via a linear layer.

    Input:  [batch, seq_len, n_features]
    Output: [batch, n_patches, embed_dim]  (CLS prepended separately in PatchTST)
    """

    def __init__(
        self,
        seq_len: int    = SEQ_LEN,
        patch_len: int  = PATCH_LEN,
        stride: int     = STRIDE,
        n_features: int = N_FEATURES,
        embed_dim: int  = EMBED_DIM,
    ):
        super().__init__()
        self.patch_len  = patch_len
        self.stride     = stride
        self.n_patches  = (seq_len - patch_len) // stride + 1   # 44
        self.patch_dim  = patch_len * n_features                 # 224

        self.projection = nn.Linear(self.patch_dim, embed_dim, bias=True)
        nn.init.xavier_uniform_(self.projection.weight)
        nn.init.zeros_(self.projection.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, T, F]  T=360, F=14
        B, T, F = x.shape

        # Unfold along time dimension → [B, n_patches, F, patch_len]
        x = x.unfold(dimension=1, size=self.patch_len, step=self.stride)

        # Rearrange: [B, n_patches, patch_len, F]
        x = x.permute(0, 1, 3, 2)

        # Flatten patch_len × F → patch_dim: [B, n_patches, 224]
        x = x.reshape(B, self.n_patches, -1)

        return self.projection(x)   # [B, n_patches, 128]


# ──────────────────────────────────────────────────────────────────────────────
# Custom Encoder Layer (with accessible attention weights)
# ──────────────────────────────────────────────────────────────────────────────
class CustomEncoderLayer(nn.Module):
    """
    Custom Transformer Encoder Layer that properly exposes attention weights.

    PyTorch's built-in TransformerEncoderLayer does not reliably expose
    per-head attention weights (fast-path disables weight computation).
    This custom implementation bypasses that limitation by calling
    nn.MultiheadAttention directly with need_weights=True.

    Architecture: Pre-LN (LayerNorm before sublayer) for training stability.
    """

    def __init__(self, d_model: int, nhead: int, dim_feedforward: int, dropout: float):
        super().__init__()
        self.self_attn = nn.MultiheadAttention(
            embed_dim=d_model,
            num_heads=nhead,
            dropout=dropout,
            batch_first=True,
        )
        self.ff_linear1 = nn.Linear(d_model, dim_feedforward)
        self.ff_linear2 = nn.Linear(dim_feedforward, d_model)

        self.norm1   = nn.LayerNorm(d_model)
        self.norm2   = nn.LayerNorm(d_model)
        self.dropout = nn.Dropout(dropout)
        self.act     = nn.GELU()

    def forward(
        self,
        x: torch.Tensor,
        return_attn: bool = False,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        """
        Args:
            x:           [batch, seq_len, d_model]
            return_attn: If True, return per-head attention weights.

        Returns:
            (output [batch, seq_len, d_model],
             attn_weights [batch, n_heads, seq_len, seq_len] or None)
        """
        # Pre-LN self-attention
        residual = x
        x_norm   = self.norm1(x)

        # need_weights=True, average_attn_weights=False → per-head weights
        attn_out, attn_weights = self.self_attn(
            x_norm, x_norm, x_norm,
            need_weights=return_attn,
            average_attn_weights=False,
        )
        x = residual + self.dropout(attn_out)

        # Pre-LN feed-forward
        residual = x
        x_norm   = self.norm2(x)
        ff_out   = self.ff_linear2(self.dropout(self.act(self.ff_linear1(x_norm))))
        x        = residual + self.dropout(ff_out)

        return x, (attn_weights if return_attn else None)


# ──────────────────────────────────────────────────────────────────────────────
# PatchTST Model (CLS-token classification head)
# ──────────────────────────────────────────────────────────────────────────────
class PatchTST(nn.Module):
    """
    PatchTST for binary solar flare classification with CLS token.

    Forward pass returns RAW LOGIT of shape [batch, 1].
    Apply sigmoid(logit) for probability at inference time.

    Architecture:
        Input [B, 360, 14]
        ↓
        PatchEmbedding → [B, 44, 128]
        ↓
        Prepend CLS token → [B, 45, 128]
        ↓
        + PositionalEncoding
        ↓
        4× CustomEncoderLayer
        ↓
        CLS output at index 0 → [B, 128]
        ↓
        Linear(128, 1) → logit [B, 1]

    Args:
        seq_len:         Input sequence length (default 360).
        patch_len:       Patch size in time steps (default 16).
        stride:          Patch stride (default 8 → 44 overlapping patches).
        n_features:      Number of input features (default 14).
        embed_dim:       Transformer embedding dimension (default 128).
        n_heads:         Number of attention heads (default 8).
        n_layers:        Number of encoder layers (default 4).
        dim_feedforward: FFN inner dimension (default 512).
        dropout:         Dropout rate (default 0.2).
    """

    def __init__(
        self,
        seq_len: int         = SEQ_LEN,
        patch_len: int       = PATCH_LEN,
        stride: int          = STRIDE,
        n_features: int      = N_FEATURES,
        embed_dim: int       = EMBED_DIM,
        n_heads: int         = N_HEADS,
        n_layers: int        = N_LAYERS,
        dim_feedforward: int = FF_DIM,
        dropout: float       = DROPOUT,
    ):
        super().__init__()
        self.n_layers  = n_layers
        self.embed_dim = embed_dim

        # Learnable CLS token [1, 1, embed_dim]
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        nn.init.trunc_normal_(self.cls_token, std=0.02)

        self.patch_embed = PatchEmbedding(seq_len, patch_len, stride, n_features, embed_dim)
        self.pos_enc     = PositionalEncoding(embed_dim, self.patch_embed.n_patches + 1, dropout)

        self.encoder_layers = nn.ModuleList([
            CustomEncoderLayer(embed_dim, n_heads, dim_feedforward, dropout)
            for _ in range(n_layers)
        ])

        self.norm = nn.LayerNorm(embed_dim)

        # Classification head — outputs RAW LOGIT, no sigmoid
        self.head = nn.Linear(embed_dim, 1)
        nn.init.xavier_uniform_(self.head.weight)
        nn.init.zeros_(self.head.bias)

        # Enforce parameter budget
        n_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        assert n_params < MAX_PARAMS, (
            f"Model has {n_params:,} parameters, exceeding the {MAX_PARAMS:,} cap. "
            "Reduce embed_dim, n_layers, or dim_feedforward."
        )
        logger.info(
            f"PatchTST initialized | params={n_params:,} | "
            f"n_patches={self.patch_embed.n_patches} | n_tokens={self.patch_embed.n_patches+1} "
            f"(+CLS) | embed_dim={embed_dim}"
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        """
        Args:
            x: [batch, seq_len, n_features]
        Returns:
            logit: [batch, 1]  — apply sigmoid(logit) for probability at inference
        """
        B = x.size(0)

        # Patch embedding: [B, 44, 128]
        x = self.patch_embed(x)

        # Prepend CLS token: [B, 45, 128]
        cls = self.cls_token.expand(B, -1, -1)
        x   = torch.cat([cls, x], dim=1)

        # Positional encoding
        x = self.pos_enc(x)

        # Transformer encoder layers
        for layer in self.encoder_layers:
            x, _ = layer(x, return_attn=False)

        # Extract CLS token output at index 0
        x = self.norm(x)
        cls_out = x[:, 0, :]        # [B, embed_dim]

        return self.head(cls_out)   # [B, 1]  — raw logit

    def forward_with_attention(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, list[torch.Tensor]]:
        """
        Forward pass returning attention weights from all encoder layers.

        Returns:
            logit:      [batch, 1]
            attn_maps:  list of [batch, n_heads, n_tokens, n_tokens] per layer
        """
        B = x.size(0)

        x = self.patch_embed(x)
        cls = self.cls_token.expand(B, -1, -1)
        x   = torch.cat([cls, x], dim=1)
        x   = self.pos_enc(x)

        attn_maps = []
        for layer in self.encoder_layers:
            x, attn = layer(x, return_attn=True)
            attn_maps.append(attn)   # [B, n_heads, 45, 45]

        x = self.norm(x)
        cls_out = x[:, 0, :]
        return self.head(cls_out), attn_maps


# ──────────────────────────────────────────────────────────────────────────────
# Monte Carlo Dropout Uncertainty
# ──────────────────────────────────────────────────────────────────────────────
@torch.no_grad()
def predict_with_uncertainty(
    model: PatchTST,
    x: torch.Tensor,
    n_samples: int = 50,
) -> dict:
    """
    Monte Carlo Dropout uncertainty estimation.

    Activates dropout (model.train() mode) during inference and performs
    n_samples stochastic forward passes to estimate epistemic uncertainty.

    Args:
        model:     PatchTST instance.
        x:         Input tensor [batch, seq_len, n_features].
        n_samples: Number of stochastic forward passes (default 50).

    Returns:
        dict:
            mean_prob: [batch] — mean predicted probability
            std_prob:  [batch] — std of predicted probability (epistemic uncertainty)
            samples:   [n_samples, batch] — all forward pass probabilities
    """
    model.train()   # activate dropout
    probs = []
    for _ in range(n_samples):
        logit = model(x)
        prob  = torch.sigmoid(logit).squeeze(-1)
        probs.append(prob.detach().cpu())
    model.eval()

    probs_tensor = torch.stack(probs)   # [n_samples, batch]
    return {
        "mean_prob": probs_tensor.mean(dim=0),
        "std_prob":  probs_tensor.std(dim=0),
        "samples":   probs_tensor,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Attention Map Extraction
# ──────────────────────────────────────────────────────────────────────────────
@torch.no_grad()
def extract_attention_maps(
    model: PatchTST,
    x: torch.Tensor,
) -> list[torch.Tensor]:
    """
    Extract per-head attention weights from all encoder layers for one input.

    Args:
        model: PatchTST instance.
        x:     Input tensor [1, seq_len, n_features] (single sample).

    Returns:
        List of attention tensors, one per encoder layer.
        Each tensor: [1, n_heads, n_tokens, n_tokens]  (n_tokens = 45)
        Row 0 = CLS attention over all other tokens (most informative for viz).
    """
    model.eval()
    _, attn_maps = model.forward_with_attention(x)
    return attn_maps
