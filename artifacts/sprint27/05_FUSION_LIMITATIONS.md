<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 27 fusion mechanism analysis. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 27 — Fusion Limitations (Q5)

**The current fusion strategy is NOT the primary limiting factor for Aditya-L1 utility; data and feature quality are.** The evidence ordering is decisive: the inputs carry approximately zero measurable conditional information before any fusion occurs (conditional mutual information 0.0 given a 5-feature GOES history baseline, `artifacts/aditya_l1/incremental_information_audit.json`; 12 of 22 input columns are duplicates and none is normalized, `01_ADITYA_FEATURE_AUDIT.md`; the official-target evidence corpus contains zero M/X events, `artifacts/aditya_l1/target_relationship_audit.json`). No fusion mechanism can fuse information absent from its inputs, so replacing the fusion layer before fixing features and evidence would optimize the wrong stage. That said, the current implementation has two specific, citable limitations that will matter *once* the inputs carry signal, and one targeted alternative is justified below against a named limitation — not by any general claim of superiority.

## What the current mechanism is (exact)

Each instrument's 45-token encoded sequence is reduced by attention pooling to a **single vector** (`app/services/ml/model_v3.py:294-296` GOES, `:314-316` SoLEXS, `:341-343` HEL1OS); SoLEXS/HEL1OS vectors are linearly projected 160→128 (`:357-358`); the three 128-dim vectors are stacked as a 3-token sequence and mixed by **one 4-head self-attention layer** (`fusion_attn`, defined `:225`, applied `:359-363`); the result is flattened to 384 dimensions and mapped to the logit by a single linear layer (`:366-369`). Missing instruments are handled by convexly blending the pooled vector with a learnable missing token using the **window-scalar** mask (`:322-323`, `:349-350`).

## Specific limitations of this implementation

1. **Temporal axis destroyed before fusion (the substantive one).** Pooling each instrument to one vector *before* any cross-instrument interaction means the fusion layer sees three timeless summaries. But the physically expected cross-instrument signal is *temporal*: the Neupert effect is a lagged integral relationship between hard-X-ray and soft-X-ray light curves (Neupert 1968; see `04_SOLAR_PHYSICS_RECOMMENDATIONS.md` G3), and the repository's own cross-instrument audit found the informative alignment at a **−5 minute offset** (`artifacts/aditya_l1/cross_instrument_confirmation_audit.json`, median_best_offset −5.0 for HEL1OS CdTe groups). A 3×3 attention over pooled vectors cannot represent "HEL1OS led GOES by five minutes." This is a representational impossibility, not a capacity shortfall.
2. **Near-zero fusion capacity.** With exactly 3 tokens, `fusion_attn` reduces to learning a 3×3 mixing pattern plus value projections — the fusion stage contributes almost no expressive power on top of the concatenation that follows it (the flattened 384-vector into a linear head would capture most of the same function class). Not the bottleneck today, but worth naming: the "cross-attention fusion" label overstates what `:359-363` computes.
3. **Mask granularity (inherited, not a fusion defect per se).** The missing-token blend acts per window because `app/services/ml/dataset_v3.py:110-111` collapses per-minute masks to the label-minute scalar; intra-window gaps arrive as zero-fill the fusion stage cannot see (`01_ADITYA_FEATURE_AUDIT.md` loss points 3–4). Fixing this is a dataset-loader change, not a fusion redesign.

## Alternatives evaluated against the named limitations

| Alternative | Does it address a named limitation? | Assessment |
|-------------|-------------------------------------|------------|
| Late fusion (current) | — | Keeps instruments independent until one vector each; adequate for amplitude-level signals, cannot represent lagged cross-instrument structure (limitation 1) |
| **Token-level cross-attention** (GOES patch tokens attend to SoLEXS/HEL1OS patch tokens *before* pooling) | **Yes — limitation 1**: preserves the temporal axis on both sides, so a lagged relation such as the −5 minute HEL1OS lead or a Neupert integral kernel is representable as an attention pattern across time-indexed patches | The one justified alternative; recommended as campaign arm C6, *contingent on features first carrying signal* |
| Hierarchical fusion (fuse SoLEXS+HEL1OS, then with GOES) | No — reorders the same pooled-vector bottleneck; no named limitation addressed | Not recommended |
| Modality-specific encoders | Already present (`model_v3.py:184-222`) | Not an alternative |
| Uncertainty-aware fusion (weight instruments by data-quality/uncertainty) | Partially — limitation 3's *symptom*, but the mask information it would need is exactly what the loader currently discards; fix the per-timestep mask first, after which the missing-token mechanism plus attention already provides input-dependent weighting | Premature; revisit only if per-timestep masking proves insufficient |

## Recommendation

Order of operations, justified by the evidence chain: (1) fix inputs — deduplicate, log-scale, engineer the physics features (`04_SOLAR_PHYSICS_RECOMMENDATIONS.md` G2–G4, G7); (2) fix mask granularity in the loader (per-timestep availability channels; `dataset_v3.py:110-111`); (3) only if a fused model with fixed inputs then underperforms a feature-level baseline, test token-level cross-attention (campaign arm C6) — the single alternative with a named limitation (temporal-axis destruction) and a named property that addresses it (time-indexed cross-instrument attention). Adopting a new fusion family before steps 1–2 would be optimizing the layer the evidence says is not binding.
