<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Sprint 26 blocker — protocol-scope decision required (pause condition 3). -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-04 -->

# Sprint 26 — Blocker Report

**Blocker type: protocol-scope decision (pause condition 3), not a fingerprint failure and not a hardware error.** Phase 1 passed and the training pipeline faithfully reproduces the frozen Version 1 baseline, but executing the full pre-registered campaign as written is a 13-to-40-hour compute effort on the available hardware, and the frozen protocol forbids me from reducing its scope. How to proceed requires your decision.

## What is verified and working

- **Phase 1 fingerprint verification: PASS** (11 of 11, `artifacts/sprint26/phase1_fingerprints.json`).
- **Pipeline validated:** the faithful driver (`scripts/sprint26/train_driver.py`) reproduces the frozen baseline — validation True Skill Score 0.568 at epoch 1 versus the frozen 0.5667 (`artifacts/sprint26/logs/B0_s42.log`, this session).
- **Version 3 integrity: CONFIRMED** — all frozen artifacts byte-identical after all activity this session.

## The blocker, precisely

- **Measured throughput:** ~256 seconds per epoch at the protocol's 5,000 steps per epoch (`OBSERVED`, `artifacts/sprint26/logs/B0_s42.log`).
- **Frozen-log expectation:** 4.6 seconds per epoch (`artifacts/training_history.json`) — the basis for the Sprint 25 compute budget's ~21-seconds-per-run estimate (`artifacts/sprint25/05_compute_budget.md`). The measured value is ~55× larger.
- **Consequence:** one run costs ~15–25 minutes (training) plus ~5–7 minutes (evaluation); the 35-run campaign (7 configurations × 5 seeds) costs an estimated 13–17 hours sequentially, up to ~40 hours including the uncapped E2 configuration.
- **Parallel mitigation failed:** five concurrent runs produced no completed epoch in nine minutes due to external-SSD ("T7 Shield") input/output contention (`OBSERVED`).

## Why I did not resolve it myself

The frozen Sprint 25 protocol and this sprint's brief both require exact execution — no deviation, no additions, no removals, all five seeds, all six ablations. Every available response to the throughput constraint conflicts with that:
1. **Proceed as written over many hours or days** — respects the protocol but exceeds a single autonomous session and requires sustained babysat background execution.
2. **Reduce scope** (fewer seeds, fewer steps per epoch, or a subset of ablations) — forbidden by the frozen protocol; I will not silently deviate.
3. **Move to faster hardware** (local SSD instead of external, or a CUDA GPU) — outside this session's resources.

Choosing among these is a decision outside the protocol's scope. The brief instructs me to ask once and end the turn.

## The decision I need from you

Which of the following should Sprint 26 do?
- **(1) Proceed exactly as written**, accepting a multi-session, multi-hour execution — I will run the 35 runs in small sequential background batches over subsequent turns and report progress.
- **(2) Authorize a specific reduced protocol** — for example, 1 seed per configuration first (7 runs, ~2.5 hours) to get directional results, or a reduced steps-per-epoch that still reproduces the baseline (the diagnostic reached validation True Skill Score 0.59 at 800 steps per epoch). If so, state the exact reduction; I will treat your instruction as the amended protocol.
- **(3) Relocate the datasets to local storage / different hardware** before proceeding, if available on your side.

I have left the one clean B0 seed-42 run training in the background; it will complete a faithful single-seed baseline regardless of your choice.

## What is NOT the blocker

This is not a Phase 1 failure (Phase 1 passed) and not a hardware error mid-run (no run crashed; the pipeline works and reproduces the baseline). It is purely a wall-clock-versus-protocol-scope decision that is yours to make.

## Update — user chose "relocate to faster hardware"; local-storage relocation tested and found insufficient

`OBSERVED` — Acting on the decision, the three research parquets were copied to local internal storage (`/private/tmp/claude-501/adityanet_local`) and one clean training epoch was measured reading from there: 1,500 steps in 84.5 seconds ≈ 21 optimizer steps per second, versus ~19.5 steps per second from the external SSD. The difference is negligible.

`INFERRED` — The throughput bottleneck is **compute** (Metal Performance Shaders forward/backward plus CPU data collation over RAM-resident feature arrays), **not** external-SSD input/output — because the dataset is loaded into memory at startup, per-step data access is RAM-speed regardless of the source disk. Relocating datasets to local SSD therefore fixes only the one-time startup load and the parallel input/output thrash, not the ~250-seconds-per-epoch training cost.

`NOT PROVEN` — Whether a CUDA GPU would close the gap; none was available this session. The effective "faster hardware" is a CUDA machine, which is on the user's side. The dataset relocation I could perform has been done and does not suffice.

**Consequence:** the actionable relocation (to local SSD) is complete and insufficient; the campaign still requires either a CUDA machine (user-provided) or a multi-hour-to-multi-day run on the current Metal Performance Shaders device. Because the user's choice was explicitly "relocate to faster hardware" rather than "proceed as written," Sprint 26 is paused here, awaiting CUDA-class hardware, rather than grinding through 13–40 hours on Metal Performance Shaders.

## Baseline result obtained before pausing

`OBSERVED` — One complete faithful Version 1 reproduction was trained (seed 42, full protocol): best validation True Skill Score **0.6053** at epoch 8 (`artifacts/sprint26/runs/B0_s42/best.pt`), against the frozen 0.5936. The pipeline reproduces the frozen baseline; only the campaign's scale is blocked.
