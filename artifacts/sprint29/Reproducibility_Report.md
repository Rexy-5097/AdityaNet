<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 29 determinism verification results. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 29 — Reproducibility Report

**Within-platform determinism is verified for every Sprint 29 component; cross-platform verification was not possible (single Apple M4 machine available) and inherits the documented Metal Performance Shaders caveat.**

## Within-platform results (this session, Apple M4, Python 3.14 system / 3.12 venv)

| Component | Verification | Result |
|-----------|-------------|--------|
| Feature framework | `test_determinism_identical_output_across_runs` — identical outputs across two computations | PASS |
| GOES physics features (synthetic) | `test_determinism_all_three` — byte-equal arrays across two runs | PASS |
| GOES physics features (real data) | Validation script computed the full feature set twice on the real 36-hour X9.0 slice; byte-identical | PASS (`goes_physics_validation.json` `determinism_real_slice: true`) |
| Evaluation harness | `test_bootstrap_reproducibility_same_seed` — identical confidence intervals from two fresh evaluators (fixed seed 20260704) | PASS |
| CI reproducibility gate | The determinism test subset executed twice back-to-back in gate 5 | PASS both runs (3 passed / 3 passed) |
| Robust scaler | `test_scaler_roundtrip_through_params` — transform identical after serialize/deserialize of fitted parameters | PASS |
| Manifest self-hash | Canonical-JSON SHA-256, order-independent (`sort_keys`), tamper-detected | PASS (`test_manifest_detects_tamper`) |

## Cross-platform status

NOT AVAILABLE this session — one machine (Apple M4, Metal Performance Shaders). The standing repository finding applies: model inference differs across platforms by up to 9.76e-4 (`scientific_validation_report.md` §3), which is why archived prediction arrays remain canonical and why the Sprint 29 features are pure NumPy/pandas computations (no torch, no device dependence) — the three physics features and all dataset infrastructure are expected platform-independent by construction, but that expectation is `NOT PROVEN` until a second platform executes the suite. The `.github/workflows/ci.yml` mirror will provide exactly that (Ubuntu runner) once a push is exercised.

## Determinism-relevant design choices

Features are stateless (no fitted state, enforced by the framework's no-fit rule); the only fitted transform (robust scaler) serializes its parameters into the dataset manifest for exact replay; all randomized procedures (bootstrap) use fixed recorded seeds; feature provenance manifests include per-feature code SHA-256 so any code drift is detectable.
