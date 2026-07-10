<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 29 risks identified during implementation, with future-work register. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 29 — Risk Report

**Highest-severity item: the physics-feature coefficient provenance (R1) — the temperature inversion uses the Thomas-Starr-Crannell 1985 cubic pending verification against the White/Thomas/Schwartz 2005 tables Sprint 28 named, and the emission-measure response is an uncalibrated proxy.** Both are shape-correct and scaling-invariant, so F1's *relative* results are unaffected, but any published absolute temperature or emission-measure figure would need the verification first.

| ID | Risk | Severity | Mitigation |
|----|------|----------|------------|
| R1 | T(R) coefficients unverified against WTS2005; EM absolutely uncalibrated (flagged ambiguity, `Feature_Validation_Report.md`) | Medium (scientific publication risk; nil for F1 relative comparisons) | Population validation passed (94%/99% over 77 X-events); verify coefficients against the published tables before any absolute-value claim; parameters and code hashes recorded in provenance manifests so a coefficient swap is a tracked, single-point change |
| R2 | Remote push unexercised — local commits exist but GitHub reachability/credentials unverified; the single-SSD bus-factor risk (standing R6) is only partly retired | Medium | Exercise one push at Sprint 30 start; until then the local history at least restores revertibility |
| R3 | Historical runner scripts were lint-modified (11 unused imports removed across 5 files) | Low (behavior-neutral; verified the frozen harness and hash-pinned promotion script untouched) | Fingerprint re-checks passed post-fix; recorded in `CI_Report.md` |
| R4 | Population physics validation uses the flare catalog's peak times; catalog timing errors would blur the pre-onset windows | Low | 77-event majority criterion is robust to individual timing errors; label-audit remains an open V4 item (assumption A13) |
| R5 | The E1-style split-cut concern applies to the future F1 dataset build: the V4 rebuild must reproduce the exact frozen split boundaries or comparability to F0 breaks | Medium (Sprint 30) | `03_DATASET_PIPELINE_V4.md` §8 fixes boundaries; the manifest records source hashes and split counts; Sprint 30 must diff counts against the frozen splits before training |
| R6 | Thermal throttling on sustained M4 runs lengthens Sprint 30 training (measured drift ~170→310 s/epoch in Sprint 26A) | Low | Overnight scheduling; budget already uses measured upper bounds |

## Future Work (observations noted while implementing; not built, per scope discipline)

1. The framework's provenance manifest could feed directly into the dataset manifest's `feature_list_sha256` for end-to-end feature-code pinning — one-line integration at Sprint 30 dataset-build time.
2. `apply_gap_policy` recomputes last-observation indices per column; a vectorized multi-column variant would speed the full 6.4-million-row Stage-1 build, only worth doing if the Sprint 30 build exceeds its input/output-bound budget.
3. The population flare-event validation script generalizes trivially to M-class events and to the future SoLEXS hardness features (G2) — reuse it in Sprint 30 rather than writing a new one.
4. `PatchTST` already accepts `n_features`; the Sprint 30 driver change is likely a two-line parameterization plus a 17-column manifest file — smaller than budgeted.
5. The GitHub Actions mirror will give free cross-platform (Ubuntu) determinism coverage for the pure-NumPy components once pushes are exercised — closing the Reproducibility_Report's cross-platform gap without dedicated work.
