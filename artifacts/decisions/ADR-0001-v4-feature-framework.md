# ADR-0001 — Version 4 feature framework: stateless features, framework-enforced isolation

Date: 2026-07-05 · Status: Accepted · Sprint: 29 (Phase 2)

## Context
Sprint 28 (`artifacts/sprint28/02_FEATURE_PIPELINE_V4.md`, `03_DATASET_PIPELINE_V4.md` §6) requires a feature pipeline that is modular, deterministic, provenance-aware, train-only fitting, and inference-safe. Version 3's failure history (test-leaked thresholds, `artifacts/sprint22_5/FINAL_VERDICT.md`) motivates structural enforcement over convention.

## Decision
Features are STATELESS classes (no `fit` method — the framework rejects any feature exposing one) that declare `requires` columns; the framework passes each feature ONLY its declared columns and forbids label columns (`target_6hr_binary`, `target_6hr_class`) in `requires`. The single fitted transform (robust median/IQR scaling) lives exclusively in `app/services/ml/dataset_v4/scaling.py` with a `fit()` that raises unless `split_name == "train"`. Every computation emits a provenance record including a SHA-256 of the feature's source code.

## Consequences
Label leakage via features becomes a structural impossibility rather than a review item; feature-code drift is detectable from manifests; the cost is that any future feature genuinely needing fitted state must move that state into the dataset layer. Enforced by `tests/test_features_v4_framework.py` (9 contract tests) and `tests/test_dataset_v4_infrastructure.py` (13 tests).
