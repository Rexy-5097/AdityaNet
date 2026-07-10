<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 29 F0/F1 experiment readiness classification. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-05 -->

# Sprint 29 — Readiness Report (F0 and F1)

**F0 is READY in full. F1 is NOT READY, with exactly three named gaps — two scheduled Sprint 30 work items excluded from this sprint's scope by design, and one environment item (remote push unverified).** Machine-readable version: `artifacts/sprint29/readiness_items.json`, produced by the Phase 5 checker this session.

## Shared preconditions (8/8 READY)

| Precondition | Status |
|---|---|
| Frozen Sprint 24 harness fingerprint identical to the Sprint 26 record | READY |
| Harness constants (block length 2880, bootstrap seed 20260704, episode gap 60) | READY |
| F0/F1 configs pre-registered, span-consistent, identical pre-registration blocks | READY |
| Seeds [42, 43, 44] with the 5-seed escalation rule (range > 0.015) | READY |
| `artifacts/research/train.parquet` present | READY |
| `artifacts/research/validation.parquet` present | READY |
| `artifacts/research/test.parquet` present | READY |
| Sprint 25 frozen training-protocol values embedded in the F1 config | READY |

## F0 preconditions (3/3 READY)

| Precondition | Status |
|---|---|
| Frozen V1 checkpoint (`artifacts/sprint26a/runs/Baseline/best.pt`, validation True Skill Score 0.6053 at epoch 8) | READY |
| Reference evaluation on the V1 span (policy True Skill Score 0.3940, `artifacts/sprint26a/runs/Baseline/eval.json`) | READY |
| Validated evaluation runner pattern (`scripts/sprint26a/eval_run.py`) | READY |

## F1 preconditions (3/6 READY)

| Precondition | Status |
|---|---|
| Three GOES physics features implemented and unit-tested (12/12) | READY |
| Physics validated on real data (77 X-class events: 94% pre-peak temperature rise, 99% positive derivative) | READY |
| Version 4 dataset infrastructure tested (13/13) | READY |
| F1 dataset: V1-era splits rebuilt through the V4 pipeline with the 17-feature set | NOT READY — scheduled Sprint 30; this sprint's Phase 4 scope explicitly excluded running the pipeline against real data |
| Training driver parameterized for a 17-feature input width | NOT READY — scheduled Sprint 30; `PatchTST` already accepts `n_features` (`app/services/ml/model.py`), but the driver wiring and a 17-column feature manifest are unbuilt and untested |
| Git remote reachable for run-provenance push | NOT READY — remote `https://github.com/Rexy-5097/AdityaNet.git` is configured and local commits exist, but no push was exercised this session, so network/credential reachability is unverified |

## What Sprint 30 must do before F1 runs

Build the F1 dataset through the V4 pipeline (features → manifest → train-only scaler), parameterize the training driver for the 17-feature width, verify one smoke epoch reproduces sane validation behavior, then execute F0-re-evaluation and F1 across the three pre-registered seeds. Nothing in the pre-registration may change; the configs in `artifacts/sprint29/experiments/` are the binding record.
