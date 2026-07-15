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

**Post-execution re-verification (OBSERVED, after all 20 arms): INTACT.** V3 stage-2 checkpoint, V3 s2_test, the Sprint-24 harness, and the frozen pre-registration (`e140360c…`) are all byte-identical to their pre-execution state. The diagnostic wrote only under `artifacts/sprint_diagnostic/`; no frozen artifact, no Study-A (`v4-goes-final`) artifact, and no dataset was modified. Every diagnostic run recorded its subsample seed and selected-index SHA-256 for exact reproducibility.
