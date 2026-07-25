"""
app/services/ml/model_f3.py

Sprint 32 Phase 1 — F3 late-fusion architecture.

Contract (defined by tests/test_model_f3.py, written first):
  * one encoder for the 17 GOES features, a SEPARATE encoder for the 19
    Aditya-L1 channels (15 engineered features + 4 availability/staleness
    disclosure channels), each an independent copy of the frozen single-encoder
    PatchTST body (so "independent normalization per stream" holds by
    construction: nothing — patch projection, positional encoding, LayerNorms —
    is shared);
  * fusion happens ONLY after both streams are pooled to their CLS embeddings:
    the model concatenates the two [B, embed_dim] vectors and applies one linear
    head. No parameter and no activation crosses between streams before that
    point (proven by the perturbation tests);
  * the availability/staleness channels are propagated to the Aditya stream as
    input channels, identically to Sprint 31 (F2 fed them to its single encoder;
    F3 routes indices 32..35 into the Aditya encoder);
  * outputs a RAW LOGIT [B, 1]; deterministic under torch seed control.

This is the late-fusion arm of 04_FAIR_ADITYA_EXPERIMENT.md / the F3 row of
05_VERSION4_DECISION_TREE.md — pooled-embedding concatenation, NOT token-level
cross-attention (that would be the downstream Path D architecture, built only
if F3 beats F2). Scope is exactly the two-stream fusion the contract names; no
generalized N-instrument framework (see Architecture_Report.md Future
Extensions).
"""

import torch
import torch.nn as nn

from app.services.ml.model import (
    PatchEmbedding, PositionalEncoding, CustomEncoderLayer,
    EMBED_DIM, N_HEADS, N_LAYERS, FF_DIM, DROPOUT, SEQ_LEN, PATCH_LEN, STRIDE,
    MAX_PARAMS,
)

# F2 dataset layout (artifacts/research_v4/dataset_v4.1.0-s2/feature_columns_36.json):
#   [0..16]  17 GOES features (14 KEEP + goes_T_iso/EM/dT)
#   [17..31] 15 Aditya features (10 SoLEXS + 5 HEL1OS)
#   [32..35] 4 disclosure channels (solexs/hel1os available + staleness_n)
GOES_DIM = 17
ADITYA_DIM = 19          # 15 Aditya features + 4 disclosure channels
TOTAL_DIM = GOES_DIM + ADITYA_DIM   # 36


class _StreamEncoder(nn.Module):
    """One PatchTST body (no classification head): input [B, T, n_features] ->
    pooled CLS embedding [B, embed_dim]. Architecturally identical to the frozen
    single-encoder PatchTST up to the head, so each stream is a faithful,
    independent encoder."""

    def __init__(self, n_features, seq_len=SEQ_LEN, patch_len=PATCH_LEN,
                 stride=STRIDE, embed_dim=EMBED_DIM, n_heads=N_HEADS,
                 n_layers=N_LAYERS, dim_feedforward=FF_DIM, dropout=DROPOUT):
        super().__init__()
        self.embed_dim = embed_dim
        self.cls_token = nn.Parameter(torch.zeros(1, 1, embed_dim))
        nn.init.trunc_normal_(self.cls_token, std=0.02)
        self.patch_embed = PatchEmbedding(seq_len, patch_len, stride, n_features, embed_dim)
        self.pos_enc = PositionalEncoding(embed_dim, self.patch_embed.n_patches + 1, dropout)
        self.encoder_layers = nn.ModuleList([
            CustomEncoderLayer(embed_dim, n_heads, dim_feedforward, dropout)
            for _ in range(n_layers)
        ])
        self.norm = nn.LayerNorm(embed_dim)

    def forward(self, x):
        B = x.size(0)
        x = self.patch_embed(x)
        cls = self.cls_token.expand(B, -1, -1)
        x = torch.cat([cls, x], dim=1)
        x = self.pos_enc(x)
        for layer in self.encoder_layers:
            x, _ = layer(x, return_attn=False)
        x = self.norm(x)
        return x[:, 0, :]        # pooled CLS embedding [B, embed_dim]


class LateFusionPatchTST(nn.Module):
    """Two independent PatchTST encoders (GOES, Aditya-L1) fused only after
    pooling. Forward returns a RAW LOGIT [B, 1]."""

    def __init__(self, goes_dim=GOES_DIM, aditya_dim=ADITYA_DIM,
                 embed_dim=EMBED_DIM, **enc_kwargs):
        super().__init__()
        self.goes_dim = goes_dim
        self.aditya_dim = aditya_dim
        self.embed_dim = embed_dim
        self.goes_encoder = _StreamEncoder(goes_dim, embed_dim=embed_dim, **enc_kwargs)
        self.aditya_encoder = _StreamEncoder(aditya_dim, embed_dim=embed_dim, **enc_kwargs)
        # fusion: concat the two pooled embeddings -> single linear head
        self.fusion_head = nn.Linear(2 * embed_dim, 1)
        nn.init.xavier_uniform_(self.fusion_head.weight)
        nn.init.zeros_(self.fusion_head.bias)

        n_params = sum(p.numel() for p in self.parameters() if p.requires_grad)
        assert n_params < MAX_PARAMS, f"{n_params:,} params exceed cap {MAX_PARAMS:,}"

    def forward_streams(self, x):
        """Return the two pooled embeddings (eg, ea) — nothing crosses streams."""
        xg = x[..., :self.goes_dim]
        xa = x[..., self.goes_dim:]
        return self.goes_encoder(xg), self.aditya_encoder(xa)

    def forward(self, x):
        eg, ea = self.forward_streams(x)
        return self.fusion_head(torch.cat([eg, ea], dim=-1))   # [B, 1] raw logit
