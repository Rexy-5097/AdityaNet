<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Provenance — frozen artifacts byte-identical before/after the diagnostic. -->
<!-- DATE: 2026-07-12 -->

# Provenance Report — Forecast Reliability Diagnostic

**Baseline (pre-execution, OBSERVED this session): all frozen artifacts INTACT.**

| Artifact | Check | Status |
|----------|-------|--------|
| Frozen pre-reg `48cbaad` | working copy SHA-256 == `git cat-file 48cbaad:…` (`e140360c…`) | BYTE-IDENTICAL |
| V3 stage-2 checkpoint | SHA-256 == `benchmark_manifest.json` | INTACT |
| V3 s2_test dataset | SHA-256 == `benchmark_manifest.json` | INTACT |
| Sprint-24 harness | SHA-256 == `phase1_fingerprints.json` | INTACT |
| `v4-goes-final` tag (Study A) | not modified | INTACT |
| F1 baseline (reused, not retrained) | present, read-only | INTACT |

The diagnostic writes only to `artifacts/sprint_diagnostic/`. It reads (never writes) the frozen datasets and harness. All training subsamples record their seed + selected-index SHA-256 (`run_meta.json:train_indices_sha256`, `train_indices.npy`) for exact reproducibility.

**Post-execution re-verification: PENDING (to be completed with the same checks after the battery finishes; this report will be updated with the post-run column).**
