<!-- VERSION STATUS: CURRENT -->
<!-- REASON: V4 phased roadmap, written at V4 planning. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-03 -->

# Version 4 — Sprint Roadmap

**Conclusion:** V4 runs in five phases over roughly ten sprints. Phase A builds the honest yardstick and restores the RED tier (no retraining, all data on disk); Phase B settles the instrument question with data engineering; Phase C bounds solar-cycle drift; Phase D — and only Phase D — touches models; Phase E takes the system to a live shadow pilot. Model work is deliberately deferred until the yardstick, the baselines, and the instrument verdict exist, because every scientific failure in V3's history came from optimizing against an unproven measurement, not from insufficient modeling.

Compute estimates are for the committed hardware (Apple M4, MPS — `context/tech_stack.md`). Problem numbers reference `VERSION4_MASTER_PLAN.md`; research questions reference `VERSION4_RESEARCH_PROGRAM.md`.

---

## Phase A — Honest Yardstick and Decision Layer (Sprints 24–25)

| Field | Content |
|-------|---------|
| Objective | One evaluation harness for everything; a RED tier that fires; baselines on the record (RQ1, RQ2, RQ5-part; problems P1–P4, P14) |
| Deliverables | `app/services/ml/episodes.py` (episode construction, episode metrics, block bootstrap) + tests; persistence and climatology baselines scored on the harness; validation MC-Dropout arrays; cost-loss frontier artifact; re-derived (or removed) uncertainty tiers; `operator_policy_v3.json` via the Sprint 23 provenance pipeline; ONE pre-registered honest test evaluation comparing {V1, persistence, climatology} at episode level |
| Dependencies | None — all inputs exist (`artifacts/research/validation.parquet`, `artifacts/calibration/probs.npy` [test predictions, reused read-only for evaluation], `artifacts/research/flares_full.parquet`, `artifacts/policies/operator_policy_v2.json`) |
| Success criteria | RED tier issues alerts at the operator-chosen cost ratio with episode precision ≥ 0.5 at episode recall ≥ 0.5 *if the frontier permits* — otherwise the frontier itself, honestly published, is the deliverable; every tier of the policy shows positive marginal episode-level benefit or is removed |
| Scientific exit criteria | RQ1 verdict with non-overlapping block-bootstrap CIs (either direction); A12 converted from FALSE-in-use to retired (window metrics demoted to diagnostics) |
| Engineering effort | ~2 sprints, one engineer; the harness is stdlib+numpy on existing arrays |
| Compute | Deterministic validation pass ≈ 2 h; MC-Dropout on policy-active validation subset ≈ 3–5 h; sweeps and bootstraps minutes; total ≤ 10 h MPS |
| Expected measurable outcome | First matched episode-level table: V1 vs persistence vs climatology with CIs; functioning RED tier or a documented impossibility frontier |

## Phase B — Settle the Instruments (Sprints 26–27; parallelizable with Phase C after its first week)

| Field | Content |
|-------|---------|
| Objective | RQ3 / SCI-001 verdict on flare-bearing joint data (P5, P11, P12) |
| Deliverables | Extended aligned GOES+SoLEXS+HEL1OS corpus built backward from `data/aditya_l1/processed/` (Oct 2023 → Jun 2026) with per-interval coverage and saturation audit; joint flare-episode census; pre-registered paired significance test GOES-only vs fusion on joint flare episodes (via Phase A harness); `model_v3.py` defaults fixed (P12, day-one hygiene); V3 integrate-or-retire ADR under `artifacts/decisions/` |
| Dependencies | Phase A harness for the significance test's episode framing; independent for the corpus build itself |
| Success criteria | ≥ 10 M/X episodes inside verified joint coverage, or a documented finding that coverage/saturation makes this impossible (also a publishable result) |
| Scientific exit criteria | SCI-001 verdict at α = 0.05, published regardless of direction; A10 converted to VALIDATED or FALSE |
| Engineering effort | ~2 sprints; dominated by alignment/quality engineering, not modeling |
| Compute | Corpus build I/O-bound (hours); V3 + GOES-only inference over the extended corpus ≈ 4–8 h MPS |
| Expected measurable outcome | The multi-instrument claim becomes assertable or is retired with evidence; V4 architecture scope is decided by data, not preference |

## Phase C — Regime Robustness (Sprints 27–28)

| Field | Content |
|-------|---------|
| Objective | Bound SC24→SC25 drift; make calibration and thresholds regime-aware (RQ4; P6, feeds P23) |
| Deliverables | Monthly walk-forward evaluation 2023–2026 using archived test predictions (each month scored by calibrator + thresholds fit strictly on earlier data); monthly ECE and episode-metric drift curves with bounds; rolling-recalibration procedure + governance spec if bounds are violated; monitoring specification (what Phase E watches = these curves, live) |
| Dependencies | Phase A harness (episode metrics per month) |
| Success criteria | Monthly calibrated ECE ≤ 0.10 across the test era, or an adopted rolling procedure that achieves it in backtest |
| Scientific exit criteria | A7/A8 converted to VALIDATED or to quantified-and-mitigated |
| Engineering effort | ~1.5 sprints |
| Compute | Minimal — reuses archived arrays; isotonic refits are seconds per month |
| Expected measurable outcome | A drift bound the ISRO submission can state instead of the current unquantified "CRITICAL WARNING" (`PROJECT_STATUS.md`) |

## Phase D — Model Science (Sprints 29–31)

| Field | Content |
|-------|---------|
| Objective | Only now, improve the model — measured on the Phase A yardstick against Phase A baselines (RQ1 improvement, RQ5, RQ6; P7, P8, P9, P13, P28) |
| Deliverables | Reproducible baseline suite regeneration (replacing the NOT-PROVEN-provenance `artifacts/baseline_metrics.json`); multi-seed V1/V3 variance; stealth-flare candidate features (quiet-background-relative flux, flare-location covariates from GOES event lists per P28) as pre-registered ablations; conformal prediction evaluation; V4 candidate model trained and promoted only through the harness + provenance gates; git + broadened tests + CI adopted at phase start as retraining hygiene (pulled forward from P16–P18) |
| Dependencies | Phase A (yardstick + baselines), Phase B (whether fusion is in scope), Phase C (regime context for training-data choices) |
| Success criteria | V4 candidate beats V1 on episode TSS with non-overlapping CIs AND does not regress stealth-stratum recall or post-flare precision beyond 2 points |
| Scientific exit criteria | A2 VALIDATED (or the negative-result contingency of RQ1 formally adopted); A3, A13, A14 resolved (label audit included here) |
| Engineering effort | ~3 sprints; heaviest phase |
| Compute | Retraining: V1-scale ≈ 1 day/run on MPS ⇒ multi-seed ×5 ≈ 5 days background; ablations comparable; total ~2 weeks wall-clock of background compute |
| Expected measurable outcome | Either a certifiably better model or a certified understanding that GOES-history skill has plateaued at the persistence-plus margin |

## Phase E — Operational Pilot (Sprints 32+)

| Field | Content |
|-------|---------|
| Objective | Live shadow operation an operator can watch (P16–P23; RQ2 lived, not simulated) |
| Deliverables | Real-time GOES ingestion scheduler; auth; application Dockerfile; monitoring per Phase C spec; operator dashboard surfacing alerts with policy provenance; 30-day shadow run with an alert log scored against actual flares; latency budget measured (MC-Dropout 50-pass cost — currently NOT PROVEN against any target); deployment packaging that resolves the policy-startup dataset-fingerprint requirement on hosts without research parquets |
| Dependencies | Phases A (policy), C (monitoring), D (final model choice); B only if fusion shipped |
| Success criteria | 30 consecutive shadow days ≥ 99% scheduler uptime; live episode metrics within the Phase A/C confidence bounds; zero provenance-gate violations |
| Scientific exit criteria | Live performance consistent with backtest — the final trust argument |
| Engineering effort | ~3+ sprints; engineering-dominant |
| Compute | Continuous light inference; negligible training |
| Expected measurable outcome | The ISRO conversation changes from "here is our test set" to "here is last month, live" |

---

## Cross-phase notes

- **What was revised by adversarial review:** Phase A gained the matched-baseline requirement (NASA persona, flaw F5 — upgraded from "missing baseline" to "existing persistence baseline may beat the model"); Phase D gained the label audit (A13) and location covariates (ISRO persona, flaw F1); Phase E gained the latency budget and the dataset-fingerprint deployment problem (FAANG persona, flaws F11, F12). Unresolved flaws are in `VERSION4_RISK_REGISTER.md`.
- **Hackathon slice:** if a submission deadline lands mid-roadmap, the demonstrable package is Phase A's outputs (honest frontier + working RED tier + matched-baseline table) plus the Sprint 22.5/23 leakage-remediation story; nothing in later phases is required for a credible entry.
