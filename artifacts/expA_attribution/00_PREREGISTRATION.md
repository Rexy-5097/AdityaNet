<!-- VERSION STATUS: FROZEN -->
<!-- REASON: Experiment A — false-episode physical attribution. Frozen pre-registration; immutable once inspection begins. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-16 -->

# Experiment A — False-Episode Physical Attribution: FROZEN Pre-Registration

Immutable contract. Nothing below may be added, removed, or reinterpreted after any false episode is inspected. The Sprint 33 frozen verdict (operational NO; REJECTED, 0 of 5 seeds) and every frozen metric are fixed inputs this experiment cannot alter.

## Objective
Determine the physical composition of the 1,073 false alert episodes produced by the frozen Sprint 33 nowcaster across its five seeds at their frozen operating points, by attributing each episode to exactly one pre-defined category using only frozen artifacts and the frozen flare catalog — without changing any frozen metric.

## Primary scientific question
What fraction of the false alert episodes coincide with catalogued solar activity, and of what class — and does the composition indicate that the operational gap is a class-discrimination phenomenon (real sub-M/X activity scored as false) or a genuine false-detection phenomenon (no catalogued activity)?

## Hypotheses (frozen; adjudicated on the pooled 1,073-episode distribution, each episode weighted equally)
- **H0 (null):** false episodes are predominantly genuine false detections — more than 50% of pooled episodes fall in category 6 (no catalogued activity, no artifact).
- **H1 (alternative):** false episodes are predominantly real sub-M/X solar activity — more than 50% fall in categories 2, 3, and 4 combined (C-class, B-class, other catalogued activity).
- **H2 (alternative):** false episodes are predominantly M/X-adjacent — more than 50% fall in category 1 (M-class or X-class whole-event overlap, i.e., decay-phase or pre-rise emission excluded by the rise-phase label). Note: the completed whole-event sensitivity analysis (`artifacts/sprint33_nowcast/Sensitivity_Labels.md`) makes H2 unlikely; it is retained because it is falsifiable and its rejection should be measured, not assumed.
- **Pre-declared fallback:** if no hypothesis class exceeds 50%, the outcome is **MIXED** and is reported as the full distribution with no predominance claim. H0, H1, H2 are mutually exclusive by construction (disjoint category groups; at most one group can exceed 50%).

## Inputs (exhaustive; no artifact outside this list may be consulted during attribution)
1. `artifacts/sprint33_nowcast/runs/s42/test_cal_probs.npy` … `s46/test_cal_probs.npy` — frozen sealed test predictions (five files).
2. `artifacts/sprint33_nowcast/runs/s42/eval.json` and `operating_point.json` … through `s46/` — frozen thresholds (0.030, 0.045, 0.100, 0.110, 0.060) and frozen false-episode counts (304, 237, 134, 165, 233; pooled 1,073).
3. `artifacts/research_v4/dataset_adi_nowcast/test.parquet` — timestamps and the frozen rise-phase label column only (SHA-256 `5f521283a62becee3d89e60f1010ed31ed4939b9f0ac10cfb1c4eb092866387a`). No feature column is read; no model is run.
4. `artifacts/research/flares_full.parquet` — the flare catalog (see catalog freeze below).
5. `artifacts/research_v4/dataset_v4.1.0-s2/test.parquet` — the four telemetry-disclosure columns only (`solexs_available`, `solexs_staleness_n`, `hel1os_available`, `hel1os_staleness_n`), for category 5.
6. `scripts/sprint24/eval_framework.py` — the frozen episode-construction functions (`_runs`, `_merge_runs`, `GAP_MIN`), imported read-only to reconstruct episode boundaries exactly as the sealed evaluation did.
7. `artifacts/sprint33_nowcast/analysis.json` — cross-check of reconstructed false-episode counts against the frozen counts (must match 304/237/134/165/233 exactly before any attribution proceeds; a mismatch is a stop condition).

## Flare catalog (frozen)
Source: `artifacts/research/flares_full.parquet` — the project's NOAA/GOES event catalog, ingested at project build and unchanged throughout Studies A–C; SHA-256 frozen now: `536842648c3891e59b7fb68e86b1dd720fe59c36749d5636c24b61e90bae499a`; access date 2026-07-16. No catalog update will be pulled; this file version is final for Experiment A. Catalog content over the test span (2025-12-15 to 2026-06-14): 1,651 C-class, 284 B-class, 162 M-class, 12 X-class catalogued flares (aggregate counts only; no episode-level alignment has been viewed).

## Attribution taxonomy (frozen; exactly one category per episode; no new category may be created — if one seems needed, stop and end the turn)
1. **Real solar activity — M/X overlap:** the episode interval strictly intersects the whole-event interval [`start_time`, `end_time`] of a catalogued M-class or X-class flare.
2. **Real solar activity — C-class overlap:** strict intersection with a catalogued C-class flare's [`start_time`, `end_time`].
3. **Real solar activity — B-class overlap:** strict intersection with a catalogued B-class flare's [`start_time`, `end_time`].
4. **Real solar activity — other catalogued activity, not M/X/C/B flare:** strict intersection with any other catalogued event in the frozen catalog (A-class or unclassified entries). Scope limit stated now: no CME/SEP/non-flare catalog exists among the frozen inputs, so category 4 is restricted to what `flares_full.parquet` contains.
5. **Instrument or data artifact:** the episode's mean `solexs_available` < 0.5 OR mean `hel1os_available` < 0.5 over the episode interval (majority-masked telemetry; frozen threshold 0.5) — checked before categories 1–4 outrank it only if no flare overlap exists; precedence below.
6. **Genuine false detection:** no catalogued event intersects the episode, no candidate event exists within the ±120-minute temporal window, and telemetry is majority-available.
7. **Ambiguous:** evidence genuinely insufficient for categories 1–6. Every category 7 assignment requires a written per-episode explanation of what evidence is missing and what would have been needed. Category 7 is not a default for difficult cases.

**Precedence rule (frozen):** if an episode satisfies multiple categories, assign the highest-priority applicable: 1 > 2 > 3 > 4 > 5 > 6 (i.e., real-activity overlap outranks artifact; higher flare class outranks lower). Confidence marking (below) records when precedence was exercised.

## Attribution protocol (frozen; applied to every episode in order; no step skipped; no judgment outside these steps)
- **Step 1:** reconstruct the episode boundaries [first alert minute, last alert minute] from the frozen `test_cal_probs.npy` and frozen threshold via the frozen `_runs`/`_merge_runs` with `GAP_MIN` = 60, and verify per-seed false-episode counts equal the frozen counts exactly.
- **Step 2:** identify every catalogued event whose [`start_time`, `end_time`] lies within, or intersects, the episode interval extended by the **temporal candidate window of ±120 minutes** (frozen now).
- **Step 3:** test strict interval intersection between the un-extended episode interval and each candidate event's [`start_time`, `end_time`].
- **Step 4:** record event timing relative to alert onset (event start minus first-alert minute, in minutes) for every candidate.
- **Step 5:** read each intersecting event's class letter from the catalog (`flare_class`) against the category definitions.
- **Step 6:** record all catalogued events within the **proximity window of ±360 minutes** (frozen now) that do *not* intersect — near-misses reported for the confidence grade, never used for category assignment.
- **Step 7:** assign exactly one category by the definitions and precedence rule; record the complete evidence trail (episode bounds, candidates, intersections, timings, classes, availability means).

## Outputs (frozen before execution)
Category counts and percentages, per seed and pooled (1,073 episodes). Representative example per populated category: **the chronologically first episode assigned to that category, by episode start time, seed 42 first then ascending seed order** — fixed selection rule, chosen before results. Confidence per attribution: **HIGH** (exactly one category's condition met; no precedence exercised; no near-miss of a higher class within ±360 minutes), **MEDIUM** (precedence exercised among multiple satisfied categories, or intersection margin under 15 minutes), **LOW** (category 7 considered and ruled out but assignment remains uncertain, or mean availability between 0.5 and 0.756 blurs the artifact boundary). Uncertainty summary: totals at each confidence level and what they imply for the primary question. Hypothesis adjudication: pooled percentages against the frozen >50% rule → H0 / H1 / H2 / MIXED. Deliverables: `artifacts/expA_attribution/attribution.json` (full evidence trails) and `artifacts/expA_attribution/Attribution_Report.md`.

## Scope boundaries (fixed now)
**Experiment A can support:** `DIRECTLY OBSERVED` — the category composition per seed and pooled; the overlap/timing statistics; the confidence distribution; which category carries the across-seed false-episode variance (std 11.17/month at matched recall). `LOGICALLY IMPLIED` — combined with the frozen Sprint 33 result that the detector holds 0.9135 ± 0.0103 episode recall on M/X rise phases: if H1 holds, the detector responds to real soft-X-ray enhancements across flare classes and the operational gap is class discrimination rather than noise rejection, and the indicated next intervention family is intensity/class gating rather than temporal confirmation; if H0 holds, the converse family indication. **Experiment A cannot support:** it cannot alter the frozen operational NO or any Sprint 33 metric (the verdict is fixed by the pre-registered label and endpoint); it cannot justify retraining (no trainability evidence, and the completed diagnostic exhausted training levers); it cannot establish that a class-aware label formulation would pass the deployment criterion — `STILL HYPOTHESIS`, requiring its own pre-registered experiment; it cannot establish instrument-relativity of the gap — that is Experiment B; and it cannot prove category 6 episodes are non-solar — only that they are uncatalogued (catalog completeness limit). No `STILL HYPOTHESIS` conclusion may be presented as established without a follow-up pre-registered experiment.

## Scientific audit (run at freeze)
1. **Frozen verdict integrity — CONFIRMED:** attribution reads Sprint 33 outputs and writes only under `artifacts/expA_attribution/`; no frozen metric can change.
2. **Single-test-touch intact — CONFIRMED:** inputs are frozen prediction arrays, frozen thresholds, timestamps/labels, and the catalog; no model inference, no test feature read, no re-evaluation.
3. **Provenance intact — CONFIRMED:** every input is a committed artifact; the two non-committed-by-git parquets are fingerprinted here by SHA-256 (`5f521283…`, `536842…`).
4. **No post-hoc hypothesis creation — CONFIRMED:** taxonomy, H0/H1/H2, the MIXED fallback, and the >50% rule are fully specified above; no individual episode's timing or catalog alignment has been viewed (only aggregate counts, which are committed Sprint 33 outputs).
5. **No hidden tuning — CONFIRMED:** temporal candidate window ±120 minutes, proximity window ±360 minutes, artifact-availability threshold 0.5, precedence rule, predominance rule >50%, confidence definitions, and the representative-example selection rule are all frozen above.
