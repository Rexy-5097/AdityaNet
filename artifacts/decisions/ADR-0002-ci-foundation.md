# ADR-0002 — CI foundation: local gate runner + hosted mirror; frozen artifacts lint-exempt

Date: 2026-07-05 · Status: Accepted · Sprint: 29 (Phase 1)

## Context
Sprint 28 (`artifacts/sprint28/06_IMPLEMENTATION_ROADMAP.md` Sprint 29 entry gates; `07_EXTERNAL_REVIEW.md` Reviewer-5 resolution) requires git, continuous integration, and tests before any Version 4 pipeline code. Discovery during implementation: the repository was ALREADY under git with remote `https://github.com/Rexy-5097/AdityaNet.git` (commits since 2026-07-01) — prior "no git" records were stale inheritances from `MIGRATION_REPORT.md`.

## Decision
Six-gate local CI (`scripts/ci/run_ci.sh`): ruff lint (E9, F rules; scoped to new V4 code and tests), format check (advisory), full pytest suite, deployed-policy provenance validation, determinism tests executed twice, and the AgentOS validator at 100/100. Hosted mirror (`.github/workflows/ci.yml`) runs the data-independent subset on Ubuntu. Frozen, fingerprint-pinned files (the Sprint 24 harness `scripts/sprint24/eval_framework.py`) receive documented per-file lint exemptions in `ruff.toml` instead of edits. Branch strategy: trunk-based on `main`, adopting the pre-existing configuration (Sprint 28 specified git + remote but no branch strategy — flagged decision).

## Consequences
Every commit is gate-checked without ever modifying fingerprint-pinned artifacts; formatting normalization of historical sprint scripts is deliberately deferred (advisory gate) to avoid churning files referenced by frozen documentation; the hosted mirror will additionally provide free cross-platform determinism coverage once a push is exercised.
