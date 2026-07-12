<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 32 Phase 1 — F3 late-fusion architecture specification (TDD). -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-12 -->

# Sprint 32 — Architecture Report (F3 late fusion)

**F3 is `LateFusionPatchTST` (`app/services/ml/model_f3.py`): two independent, architecturally identical PatchTST encoders — one on the 17 GOES features, one on the 19 Aditya-L1 channels (15 engineered features + 4 availability/staleness disclosure channels) — whose pooled CLS embeddings are concatenated and passed through a single linear fusion head. No parameter and no activation crosses between streams before the fusion point; this is proven, not asserted, by perturbation tests (`tests/test_model_f3.py`, 11 tests, all OBSERVED PASS). Total trainable parameters: 1,661,185 — 1.915× the single-encoder Sprint 31 F2 model (867,457). Written test-first: the 11 contract tests were committed and passing before this report.**

## Requirement-by-requirement conformance (OBSERVED via `tests/test_model_f3.py`)

| Phase 1 requirement | Implementation | Test |
|---------------------|----------------|------|
| Separate encoder for GOES features | `goes_encoder = _StreamEncoder(17)` | `test_two_separate_encoders_disjoint_params` |
| Separate encoder for Aditya-L1 features | `aditya_encoder = _StreamEncoder(19)` | same |
| Independent normalization per stream | each encoder owns its PatchEmbedding projection, positional encoding, per-layer LayerNorms, and final LayerNorm — no shared normalization parameters | `test_two_separate_encoders_disjoint_params` (asserts distinct norm weights) |
| Fusion only after both latent embeddings produced | `forward` calls `forward_streams` → concatenates the two [B,128] pooled CLS vectors → single `fusion_head` Linear(256,1) | `test_fusion_is_after_pooling`, `test_fusion_depends_on_both_streams` |
| No information crosses streams before fusion | GOES/Aditya inputs sliced by fixed index 17; encoders never see each other's channels | `test_goes_encoder_sees_only_goes_channels`, `test_aditya_encoder_sees_only_aditya_channels` (perturbing one stream's inputs leaves the other's embedding bit-identical) |
| Availability masks propagated identically to Sprint 31 | the 4 disclosure channels (indices 32–35) are input channels routed into the Aditya encoder — exactly as F2 fed them to its single encoder | `test_disclosure_channels_feed_aditya_stream` |
| Deterministic under seed control | identical seed → identical weights → identical output | `test_determinism_under_seed` |

## Layer shapes (per stream; both identical except input width)

```
Input (GOES)   [B, 360, 17]          Input (Aditya) [B, 360, 19]
  PatchEmbedding: unfold len16/stride8 → 44 patches; Linear(16·F, 128)
  → [B, 44, 128]
  prepend CLS   → [B, 45, 128]
  + sinusoidal positional encoding (fixed, non-learnable)
  4 × CustomEncoderLayer (pre-LN; 8 heads; FFN 128→512→128; dropout 0.2)
  final LayerNorm; take CLS token (index 0)
  → pooled embedding [B, 128]
Fusion:  concat([goes_emb 128, aditya_emb 128]) = [B, 256]
         fusion_head Linear(256, 1) → raw logit [B, 1]
```

Encoder hyperparameters are the frozen single-encoder PatchTST values, reused unchanged: embed_dim 128, 8 heads, 4 layers, FFN 512, dropout 0.2, patch_len 16, stride 8, 44 patches + CLS = 45 tokens. The building blocks (`PatchEmbedding`, `PositionalEncoding`, `CustomEncoderLayer`) are imported from `app/services/ml/model.py` — F3 introduces no new layer types, only a second encoder instance and the fusion head.

## Fusion mechanism

Concatenation of the two pooled CLS embeddings followed by one linear layer — the standard "late fusion" of the F3 row in `04_FAIR_ADITYA_EXPERIMENT.md` and `05_VERSION4_DECISION_TREE.md` ("per-timestep-mask late-fusion architecture"). It is deliberately **not** token-level cross-attention: that is the downstream Path D architecture ("GOES patch tokens attending to SoLEXS/HEL1OS patch tokens before pooling"), to be built only if F3 beats F2. F3 tests exactly one hypothesis — whether keeping the streams in separate encoders until after pooling beats F2's single-encoder concatenation-at-input.

## Parameter budget (OBSERVED)

| Model | Trainable params | Ratio vs F2 |
|-------|------------------|-------------|
| F2 single-encoder PatchTST (36 features) | 867,457 | 1.000× |
| **F3 LateFusionPatchTST** | **1,661,185** | **1.915×** |
| ├ GOES encoder (17ch) | 828,416 | |
| ├ Aditya encoder (19ch) | 832,512 | |
| └ fusion head (Linear 256→1) | 257 | |

The near-doubling is expected: the transformer body (four encoder layers, the dominant cost) is duplicated, once per stream; the two bodies differ only in their patch-embedding input width (17 vs 19 channels), and the fusion head is negligible (257 params). F3 remains far under the 10,000,000-parameter global cap enforced in `LateFusionPatchTST.__init__`.

## Flagged implementation decisions (conservative interpretations, none blocking)

1. **"Independent normalization per stream"** — interpreted as *each stream normalizes within its own encoder with no shared normalization statistics or parameters*, satisfied by giving each stream a complete independent encoder (its own patch projection and all LayerNorms). No extra input-normalization layer was added: the dataset already applies train-only robust per-feature scaling, so a second input normalization would be redundant and unspecified. The alternative (an explicit per-stream input `LayerNorm`) was rejected as unrequested scope.
2. **"Availability masks propagated identically to Sprint 31" vs the `03_DATASET_PIPELINE_V4.md` §3 "window missing-token"** — Phase 1 says *identically to Sprint 31*, and Sprint 31 (F2) propagated availability purely as input channels (no learnable window-missing-token blend). F3 follows that: the 4 disclosure channels are Aditya-stream inputs. A window-level missing-token would in any case be dead code on this data — the S2 span has no fully-absent Aditya windows (availability_fraction ∈ [0.697, 0.805], Sprint 31 stratification). The Phase 1 "identically to Sprint 31" clause resolves the surface tension with §3; recorded here for traceability.
3. **Fixed split index (17)** — the GOES/Aditya boundary is the fixed dataset layout (`feature_columns_36.json`), hard-coded as `GOES_DIM=17`; the model asserts the 36-channel input width at construction.

## Future Extensions (noted, NOT built — scope discipline per the brief)

- A generalized N-instrument fusion module (a list of encoders + a fusion head sized to their count) would subsume both F2-concat and F3-late-fusion, and would be the natural home for the Path D cross-attention variant. It is deliberately not built: F3 needs exactly two streams, and `05_VERSION4_DECISION_TREE.md` only justifies the next architecture (Path D) conditionally on F3 > F2. Building the general framework now would be speculative scope.
- The fusion head is a single linear layer; a small MLP or a gated/attention fusion over the two embeddings is a cheap future variant, but unspecified here and therefore not built.
