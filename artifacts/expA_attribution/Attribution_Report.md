<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Experiment A results — false-episode physical attribution per frozen pre-registration e7ddc0a. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Experiment A — Attribution Report

**Hypothesis verdict by the frozen >50% rule: H1 — the false episodes are predominantly real sub-threshold solar activity. 94.22% of the 1,073 pooled false episodes (1,011 of 1,073) strictly intersect catalogued C-class flares. Genuine false detections — no catalogued activity, no artifact — are 1.86% (20 episodes, i.e., 0 to 7 per seed across the ~6-month test span, roughly one per month or fewer). The Sprint 33 "false-alarm problem" is, physically, a flare-class-discrimination phenomenon: the detector detects real flares; the pre-registered M/X-only label scores its correct detections of weaker real flares as false.** The frozen operational NO verdict is unchanged and unchangeable by this analysis. Full evidence trails: `artifacts/expA_attribution/attribution.json`; protocol: `00_PREREGISTRATION.md` (commit `e7ddc0a`, tag `expA-prereg`), executed verbatim with the count-reconciliation stop condition passing exactly (304/237/134/165/233).

## Pooled category composition (DIRECTLY OBSERVED)

| Category | Count | Percent |
|----------|-------|---------|
| 1 — Real solar activity, M/X overlap | 0 | 0.00% |
| 2 — Real solar activity, C-class overlap | 1,011 | 94.22% |
| 3 — Real solar activity, B-class overlap | 0 | 0.00% |
| 4 — Real solar activity, other catalogued | 0 | 0.00% |
| 5 — Instrument or data artifact | 8 | 0.75% |
| 6 — Genuine false detection | 20 | 1.86% |
| 7 — Ambiguous (candidate within ±120 min, no strict intersection; written explanation per episode in `attribution.json`) | 34 | 3.17% |

Hypothesis shares against the frozen rule: H1 (categories 2+3+4) = 0.9422 > 0.5 → **H1 confirmed**; H0 (category 6) = 0.0186; H2 (category 1) = 0.0000 — the zero M/X-overlap share independently confirms what the Sprint 33 whole-event sensitivity analysis implied (false episodes are not M/X decay-phase alerts).

## Per-seed composition and the variance question (DIRECTLY OBSERVED)

| Seed | Total false | C-overlap | Genuine false | Artifact | Ambiguous |
|------|-------------|-----------|---------------|----------|-----------|
| 42 | 304 | 278 (91.4%) | 7 | 3 | 16 |
| 43 | 237 | 219 (92.4%) | 6 | 4 | 8 |
| 44 | 134 | 132 (98.5%) | 0 | 0 | 2 |
| 45 | 165 | 160 (97.0%) | 3 | 0 | 2 |
| 46 | 233 | 222 (95.3%) | 4 | 1 | 6 |

The anomalous across-seed false-episode variance (std 11.17/month at matched recall, flagged in Sprint 33) is carried almost entirely by the C-overlap category (278 vs 132 between the extreme seeds): seeds differ in **how many real C-class flares they fire on**, not in noise production. Genuine-false production is uniformly minimal (0–7 per seed per ~6 months).

## Representative examples (frozen chronological-first rule) and uncertainty summary

Category 2: seed 43, 2025-12-15 12:25–12:27 UTC, 3-minute episode intersecting a catalogued C-class flare (MEDIUM confidence — short overlap margin). Category 6: seed 43, 2025-12-22 03:58 UTC, a single-minute alert with no catalogued event within ±120 minutes (HIGH confidence). Category 7: seed 42, 2025-12-27 20:36–20:44 UTC, 9-minute episode with a catalogued event inside the candidate window but no strict intersection (LOW confidence; per-episode explanation recorded). Confidence totals: HIGH 50, MEDIUM 983, LOW 40. The MEDIUM dominance is a mechanical consequence of the frozen definitions, not assignment uncertainty: C-overlap episodes have median duration 5 minutes, so their overlap margins are necessarily under the frozen 15-minute MEDIUM threshold, and in an active sun the ±360-minute proximity window frequently contains a higher-class near-miss — while the category assignment itself rests on binary strict interval intersection, which is factual. The 34 ambiguous plus 40 LOW-confidence episodes (≤ 6.9% combined) cannot alter the H1 verdict: even assigning every one of them to category 6 would raise H0's share only to 0.088.

## Conclusions, scope-bounded per the frozen pre-registration

`DIRECTLY OBSERVED`: the composition above; the C-overlap concentration of the seed variance; the genuine-false rate of ~0.0–1.2 episodes per month per seed. `LOGICALLY IMPLIED` (with the frozen Sprint 33 result of 0.9135 ± 0.0103 M/X episode recall): the detector responds to real soft-X-ray flare enhancements across classes — it detects M/X flares at 91% recall *and* fires on over a thousand real C-class flares — so the operational gap is **class discrimination, not noise rejection**, and the indicated intervention family is intensity/class gating rather than temporal-confirmation policies (which suppress incoherent noise, of which there is almost none: 1.86%). `STILL HYPOTHESIS` (requires its own pre-registered experiment before any claim): that an intensity-gated or class-aware formulation would meet the ≤ 5.0 false-episodes-per-month budget at ≥ 0.80 M/X recall — noting, strictly as motivation for that experiment, the `DERIVED` arithmetic that the measured genuine-false rate alone (≈ 0.0–1.2/month) sits far inside the budget, so the entire question reduces to whether C-responses can be discriminated away without sacrificing M/X recall. Unchanged and out of scope: the frozen operational NO at the pre-registered label; retraining justification (none — the diagnostic exhausted training levers); instrument-relativity (Experiment B, whose false episodes must receive this identical taxonomy per the agreed ordering); and the possibility that some category-6 episodes are real but uncatalogued activity (catalog completeness limit).
