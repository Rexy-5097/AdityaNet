"""
app/services/ml/model_v3.py

Version 3 Late Fusion PatchTST Architecture for Multi-Instrument Solar Flare Forecasting.

Design:
  - Inputs:
      1. GOES sequence:    [batch, seq_len=360, n_features_goes=14]
      2. SoLEXS sequence:  [batch, seq_len=360, n_features_solexs=25] (optional)
      3. HEL1OS sequence:  [batch, seq_len=360, n_features_hel1os=10] (optional)
  - Asymmetrical Encoders:
      1. GOES Encoder:     embed_dim=128, n_layers=4, n_heads=8, dim_feedforward=512
      2. SoLEXS Encoder:   embed_dim=160, n_layers=5, n_heads=8, dim_feedforward=640
      3. HEL1OS Encoder:   embed_dim=160, n_layers=5, n_heads=8, dim_feedforward=640
  - Attention Pooling:
      Compresses the output [batch, 45, embed_dim] temporal sequence using a learnable
      query parameter to preserve full sequence context.
  - Learnable Missing Tokens:
      Unavailable telemetry streams are replaced by learnable tokens so that the model
      can explicitly represent missing-state parameters rather than assuming zero inputs.
  - Cross-Attention Fusion:
      Embeddings are projected to a common fusion_dim=128 and passed through a self-attention
      layer to model cross-instrument dependencies before the final classification head.
"""

import math
import logging
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Global Architectural Constants
# ──────────────────────────────────────────────────────────────────────────────
SEQ_LEN      = 360
PATCH_LEN    = 16
STRIDE       = 8
MAX_PARAMS   = 5_000_000  # Enforced parameter cap for Version 3

# ──────────────────────────────────────────────────────────────────────────────
# Sinusoidal Positional Encoding
# ──────────────────────────────────────────────────────────────────────────────
class PositionalEncoding(nn.Module):
    """Sinusoidal Positional Encoding for tokenized sequences."""

    def __init__(self, d_model: int, max_len: int, dropout: float = 0.2):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float32).unsqueeze(1)
        div_term = torch.exp(
            torch.arange(0, d_model, 2, dtype=torch.float32) * (-math.log(10000.0) / d_model)
        )
        pe[:, 0::2] = torch.sin(position * div_term)
        # Handle odd dimensions gracefully
        if d_model % 2 == 0:
            pe[:, 1::2] = torch.cos(position * div_term)
        else:
            pe[:, 1::2] = torch.cos(position * div_term[:d_model // 2])
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer("pe", pe)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, n_tokens, embed_dim]
        x = x + self.pe[:, : x.size(1), :]
        return self.dropout(x)

# ──────────────────────────────────────────────────────────────────────────────
# Patch Embedding
# ──────────────────────────────────────────────────────────────────────────────
class PatchEmbedding(nn.Module):
    """Extracts overlapping patches from time-series and projects them to embed_dim."""

    def __init__(self, seq_len: int, patch_len: int, stride: int, n_features: int, embed_dim: int):
        super().__init__()
        self.patch_len  = patch_len
        self.stride     = stride
        self.n_patches  = (seq_len - patch_len) // stride + 1
        self.patch_dim  = patch_len * n_features

        self.projection = nn.Linear(self.patch_dim, embed_dim, bias=True)
        nn.init.xavier_uniform_(self.projection.weight)
        nn.init.zeros_(self.projection.bias)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [B, T, F]
        B, T, F = x.shape

        # Unfold along time dimension → [B, n_patches, F, patch_len]
        x = x.unfold(dimension=1, size=self.patch_len, step=self.stride)

        # Rearrange: [B, n_patches, patch_len, F]
        x = x.permute(0, 1, 3, 2)

        # Flatten patch_len × F → patch_dim: [B, n_patches, patch_dim]
        x = x.reshape(B, self.n_patches, -1)

        return self.projection(x)

# ──────────────────────────────────────────────────────────────────────────────
# Custom Encoder Layer
# ──────────────────────────────────────────────────────────────────────────────
class CustomEncoderLayer(nn.Module):
    """Pre-LN Transformer Encoder Layer exposing attention weights."""

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

    def forward(self, x: torch.Tensor, return_attn: bool = False) -> tuple[torch.Tensor, torch.Tensor | None]:
        residual = x
        x_norm   = self.norm1(x)

        attn_out, attn_weights = self.self_attn(
            x_norm, x_norm, x_norm,
            need_weights=return_attn,
            average_attn_weights=False,
        )
        x = residual + self.dropout(attn_out)

        residual = x
        x_norm   = self.norm2(x)
        ff_out   = self.ff_linear2(self.dropout(self.act(self.ff_linear1(x_norm))))
        x        = residual + self.dropout(ff_out)

        return x, (attn_weights if return_attn else None)

# ──────────────────────────────────────────────────────────────────────────────
# Late Fusion PatchTST Main Architecture
# ──────────────────────────────────────────────────────────────────────────────
class LateFusionPatchTST(nn.Module):
    """
    Late Fusion PatchTST with Asymmetrical Encoders, Attention Pooling,
    Learnable Missing Tokens, and Cross-Attention Fusion.
    """

    def __init__(
        self,
        n_features_goes: int = 14,
        n_features_solexs: int = 25,
        n_features_hel1os: int = 10,
        embed_dim_goes: int = 128,
        embed_dim_solexs: int = 160,
        embed_dim_hel1os: int = 160,
        n_layers_goes: int = 4,
        n_layers_solexs: int = 5,
        n_layers_hel1os: int = 5,
        n_heads: int = 8,
        dim_feedforward_goes: int = 512,
        dim_feedforward_solexs: int = 640,
        dim_feedforward_hel1os: int = 640,
        dropout: float = 0.2,
        fusion_dim: int = 128,
    ):
        super().__init__()
        self.seq_len = SEQ_LEN
        self.patch_len = PATCH_LEN
        self.stride = STRIDE
        self.fusion_dim = fusion_dim
        
        self.n_features_goes = n_features_goes
        self.n_features_solexs = n_features_solexs
        self.n_features_hel1os = n_features_hel1os

        self.embed_dim_goes = embed_dim_goes
        self.embed_dim_solexs = embed_dim_solexs
        self.embed_dim_hel1os = embed_dim_hel1os

        # 1. Encoders and Embedding Projections
        # A. GOES Encoder
        self.cls_token_goes = nn.Parameter(torch.zeros(1, 1, embed_dim_goes))
        self.patch_embed_goes = PatchEmbedding(SEQ_LEN, PATCH_LEN, STRIDE, n_features_goes, embed_dim_goes)
        self.pos_enc_goes = PositionalEncoding(embed_dim_goes, self.patch_embed_goes.n_patches + 1, dropout)
        self.encoder_goes = nn.ModuleList([
            CustomEncoderLayer(embed_dim_goes, n_heads, dim_feedforward_goes, dropout)
            for _ in range(n_layers_goes)
        ])
        self.norm_goes = nn.LayerNorm(embed_dim_goes)
        self.pool_query_goes = nn.Parameter(torch.zeros(1, 1, embed_dim_goes))
        self.pool_attn_goes = nn.MultiheadAttention(embed_dim_goes, num_heads=4, batch_first=True)

        # B. SoLEXS Encoder
        self.cls_token_solexs = nn.Parameter(torch.zeros(1, 1, embed_dim_solexs))
        self.patch_embed_solexs = PatchEmbedding(SEQ_LEN, PATCH_LEN, STRIDE, n_features_solexs, embed_dim_solexs)
        self.pos_enc_solexs = PositionalEncoding(embed_dim_solexs, self.patch_embed_solexs.n_patches + 1, dropout)
        self.encoder_solexs = nn.ModuleList([
            CustomEncoderLayer(embed_dim_solexs, n_heads, dim_feedforward_solexs, dropout)
            for _ in range(n_layers_solexs)
        ])
        self.norm_solexs = nn.LayerNorm(embed_dim_solexs)
        self.pool_query_solexs = nn.Parameter(torch.zeros(1, 1, embed_dim_solexs))
        self.pool_attn_solexs = nn.MultiheadAttention(embed_dim_solexs, num_heads=4, batch_first=True)
        self.missing_token_solexs = nn.Parameter(torch.zeros(1, embed_dim_solexs))
        self.proj_solexs = nn.Linear(embed_dim_solexs, fusion_dim)

        # C. HEL1OS Encoder
        self.cls_token_hel1os = nn.Parameter(torch.zeros(1, 1, embed_dim_hel1os))
        self.patch_embed_hel1os = PatchEmbedding(SEQ_LEN, PATCH_LEN, STRIDE, n_features_hel1os, embed_dim_hel1os)
        self.pos_enc_hel1os = PositionalEncoding(embed_dim_hel1os, self.patch_embed_hel1os.n_patches + 1, dropout)
        self.encoder_hel1os = nn.ModuleList([
            CustomEncoderLayer(embed_dim_hel1os, n_heads, dim_feedforward_hel1os, dropout)
            for _ in range(n_layers_hel1os)
        ])
        self.norm_hel1os = nn.LayerNorm(embed_dim_hel1os)
        self.pool_query_hel1os = nn.Parameter(torch.zeros(1, 1, embed_dim_hel1os))
        self.pool_attn_hel1os = nn.MultiheadAttention(embed_dim_hel1os, num_heads=4, batch_first=True)
        self.missing_token_hel1os = nn.Parameter(torch.zeros(1, embed_dim_hel1os))
        self.proj_hel1os = nn.Linear(embed_dim_hel1os, fusion_dim)

        # 2. Cross-Attention Fusion Layer
        self.fusion_attn = nn.MultiheadAttention(embed_dim=fusion_dim, num_heads=4, batch_first=True)

        # 3. Classifier Head
        self.head = nn.Linear(3 * fusion_dim, 1)

        # Initializations
        nn.init.trunc_normal_(self.cls_token_goes, std=0.02)
        nn.init.trunc_normal_(self.cls_token_solexs, std=0.02)
        nn.init.trunc_normal_(self.cls_token_hel1os, std=0.02)
        nn.init.trunc_normal_(self.missing_token_solexs, std=0.02)
        nn.init.trunc_normal_(self.missing_token_hel1os, std=0.02)
        nn.init.trunc_normal_(self.pool_query_goes, std=0.02)
        nn.init.trunc_normal_(self.pool_query_solexs, std=0.02)
        nn.init.trunc_normal_(self.pool_query_hel1os, std=0.02)
        nn.init.xavier_uniform_(self.head.weight)
        nn.init.zeros_(self.head.bias)
        nn.init.xavier_uniform_(self.proj_solexs.weight)
        nn.init.zeros_(self.proj_solexs.bias)
        nn.init.xavier_uniform_(self.proj_hel1os.weight)
        nn.init.zeros_(self.proj_hel1os.bias)

        # Enforce parameter budget
        n_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        assert n_params < MAX_PARAMS, (
            f"V3 Model has {n_params:,} parameters, exceeding the {MAX_PARAMS:,} cap. "
            "Reduce layer counts or hidden dimensions."
        )
        logger.info(
            f"LateFusionPatchTST initialized | total_params={n_params:,} (Budget cap={MAX_PARAMS:,}) | "
            f"GOES: embed={embed_dim_goes}, layers={n_layers_goes} | "
            f"SoLEXS: embed={embed_dim_solexs}, layers={n_layers_solexs} | "
            f"HEL1OS: embed={embed_dim_hel1os}, layers={n_layers_hel1os}"
        )

    def forward(
        self,
        x_goes: torch.Tensor,
        x_solexs: torch.Tensor | None = None,
        x_hel1os: torch.Tensor | None = None,
        mask_solexs: torch.Tensor | None = None,
        mask_hel1os: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """
        Forward pass.
        
        Args:
            x_goes:      [B, seq_len=360, n_features_goes=14]
            x_solexs:    [B, seq_len=360, n_features_solexs=25] (optional)
            x_hel1os:    [B, seq_len=360, n_features_hel1os=10] (optional)
            mask_solexs: [B, 1] binary tensor indicating presence (1.0) or absence (0.0)
            mask_hel1os: [B, 1] binary tensor indicating presence (1.0) or absence (0.0)

        Returns:
            logit:       [B, 1] raw logit output
        """
        B = x_goes.size(0)

        # ──────────────────────────────────────────────────────────────────────
        # 1. GOES Branch
        # ──────────────────────────────────────────────────────────────────────
        g = self.patch_embed_goes(x_goes)
        cls_g = self.cls_token_goes.expand(B, -1, -1)
        g = torch.cat([cls_g, g], dim=1)
        g = self.pos_enc_goes(g)
        for layer in self.encoder_goes:
            g, _ = layer(g)
        g = self.norm_goes(g)
        
        # Attention Pooling
        q_g = self.pool_query_goes.expand(B, -1, -1)
        e_goes, _ = self.pool_attn_goes(q_g, g, g)
        e_goes = e_goes.squeeze(1)  # [B, embed_dim_goes=128]

        # ──────────────────────────────────────────────────────────────────────
        # 2. SoLEXS Branch
        # ──────────────────────────────────────────────────────────────────────
        if x_solexs is None:
            # Entire branch missing - use missing token directly
            e_solexs = self.missing_token_solexs.expand(B, -1)  # [B, embed_dim_solexs=160]
        else:
            s = self.patch_embed_solexs(x_solexs)
            cls_s = self.cls_token_solexs.expand(B, -1, -1)
            s = torch.cat([cls_s, s], dim=1)
            s = self.pos_enc_solexs(s)
            for layer in self.encoder_solexs:
                s, _ = layer(s)
            s = self.norm_solexs(s)
            
            # Attention Pooling
            q_s = self.pool_query_solexs.expand(B, -1, -1)
            e_solexs_raw, _ = self.pool_attn_solexs(q_s, s, s)
            e_solexs_raw = e_solexs_raw.squeeze(1)

            # Masking check
            if mask_solexs is None:
                mask_solexs = torch.ones(B, 1, dtype=x_goes.dtype, device=x_goes.device)
            
            missing_t = self.missing_token_solexs.expand(B, -1)
            e_solexs = e_solexs_raw * mask_solexs + missing_t * (1.0 - mask_solexs)

        # ──────────────────────────────────────────────────────────────────────
        # 3. HEL1OS Branch
        # ──────────────────────────────────────────────────────────────────────
        if x_hel1os is None:
            # Entire branch missing - use missing token directly
            e_hel1os = self.missing_token_hel1os.expand(B, -1)  # [B, embed_dim_hel1os=160]
        else:
            h = self.patch_embed_hel1os(x_hel1os)
            cls_h = self.cls_token_hel1os.expand(B, -1, -1)
            h = torch.cat([cls_h, h], dim=1)
            h = self.pos_enc_hel1os(h)
            for layer in self.encoder_hel1os:
                h, _ = layer(h)
            h = self.norm_hel1os(h)
            
            # Attention Pooling
            q_h = self.pool_query_hel1os.expand(B, -1, -1)
            e_hel1os_raw, _ = self.pool_attn_hel1os(q_h, h, h)
            e_hel1os_raw = e_hel1os_raw.squeeze(1)

            # Masking check
            if mask_hel1os is None:
                mask_hel1os = torch.ones(B, 1, dtype=x_goes.dtype, device=x_goes.device)
            
            missing_t = self.missing_token_hel1os.expand(B, -1)
            e_hel1os = e_hel1os_raw * mask_hel1os + missing_t * (1.0 - mask_hel1os)

        # ──────────────────────────────────────────────────────────────────────
        # 4. Projections & Fusion
        # ──────────────────────────────────────────────────────────────────────
        # Project all embeddings to fusion_dim=128
        e_goes_proj   = e_goes
        e_solexs_proj = self.proj_solexs(e_solexs)
        e_hel1os_proj = self.proj_hel1os(e_hel1os)

        # Stack into a sequence: [B, 3, 128]
        E = torch.stack([e_goes_proj, e_solexs_proj, e_hel1os_proj], dim=1)

        # Cross-Attention self-attention layer
        E_fused, _ = self.fusion_attn(E, E, E)  # [B, 3, 128]

        # Flatten representation: [B, 384]
        fused_flat = E_fused.flatten(start_dim=1)

        # Classifier
        logit = self.head(fused_flat)  # [B, 1]

        return logit
