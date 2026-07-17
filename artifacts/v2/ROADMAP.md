<!-- VERSION STATUS: GOVERNING DOCUMENT -->
<!-- REASON: AdityaNet v2 master roadmap. Product of joint PI review, FMEA, and redesign review (2026-07-17). -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-17 -->

# AdityaNet v2 — Master Roadmap (Governing Document)

**Status:** governing. Amendable only by a logged revision with rationale; never edited silently.
**Provenance:** synthesises the completed v1 evidence base (Sprints 24–33, Experiments A/C/D/E, three adversarial audits, FMEA of 2026-07-17). Every design decision below cites the evidence that forced it.

---

## 0. Vision

Measure what the Aditya-L1 X-ray payloads can actually see, then build the strongest honest product on top of that measurement — a flare nowcaster with severity estimation and a characterised prediction-skill curve — such that every reported number survives adversarial audit.

v1's central lesson, encoded here as the ordering principle: **understand the instrument before featurizing it; featurize before modelling; pre-register conclusions before looking at outcomes — but never before knowing what object is being measured.**

## 0.1 Objectives (deliberately separated; v1's core strategic error was blending them)

- **Scientific:** measure the information content of SoLEXS+HEL1OS with respect to (i) flare detection, (ii) severity discrimination at the C/M boundary, (iii) precursor information as a function of horizon. The deliverable is the measurement, whichever way it falls.
- **Engineering:** a reproducible one-command pipeline raw-FITS → alert stream, with declared physical units and provenance at every stage, and QA gates that fail loudly.
- **Operational:** a GOES-independent L1 alert channel with quantified alarm economics (per-class recall, genuine-false rate, latency, severity confidence), demonstrated on a replay stream. **Scope limit (declared):** L2 products are daily files; true real-time operation is an ISRO ground-segment capability outside this project. We deliver the algorithmic pipeline and its latency budget, not a real-time service.
- **Hackathon:** an automated pipeline satisfying the brief's literal ask ("detect or predict solar flares from combined SoLEXS+HEL1OS") and its motivation (disruption anticipation ⇒ M/X focus), with severity ranking and an honest evaluation dossier as differentiators.
- **Publication:** one paper: instrument capability characterisation (either branch of Gate 1) + the detection system + the skill-vs-horizon curve + the rigorous 6-h negative result, targeted at Space Weather / Solar Physics / JGR-class venues.

## 0.2 Standing assumptions (each is a risk if false)

1. Hackathon deadline ≥ 6 weeks out (owner to confirm; compression plan in §5).
2. The GOES/NOAA flare catalog is acceptable primary ground truth (class quantisation ~0.05 dex is second-order).
3. The 915-day L2 archive is processing-stable across the mission (Phase 1 checks this).
4. Laptop-class compute suffices (evidenced: 14 min/seed detector training in v1; compute is nowhere near the critical path).
5. Team of ~2 (one scientist, one engineer), single timeline.

## 0.3 Inherited-asset register (immutable)

Inherited **verbatim**: the episode-level evaluation harness (block bootstrap, 2,880-window blocks, frozen seeds), the leakage/provenance guard system, the pre-registration discipline with OBSERVED/DERIVED/HYPOTHESIS labelling, and every v1 frozen number as a baseline (detector recalls, FE rates, TSS values, era-matched GOES control, Experiment A taxonomy and attribution method).
Inherited **nothing else** without a units-and-provenance check. The v1 feature pipeline is presumed lossy until Phase 1 says otherwise.

## 0.4 Known-truth register (v1 results no v2 experiment may ignore or silently re-litigate)

6-h Aditya-only TSS 0.359 (ceiling diagnostic: GENUINE LIMIT); era-matched GOES 0.438; detector per-class episode recall M 0.909 / X 0.900 / C 0.244 / B 0.002; 94.22% of "false" episodes are real C flares, genuine false ≈ 1/month; policy layer on-frontier (audit); representation probes exhausted for the v1 encoder (+0.0026); seed-level class-AUC SD ≈ 0.017 (all power analyses use this); R² = 0.0018 anomaly OBSERVED and unexplained; raw per-channel L2 data exists and was never used by any v1 model.

---

## 1. Phases

### Phase 0 — Charter & Data Inventory
- **Purpose:** fix objectives, benchmark policy, and a complete units/provenance inventory before anything else runs.
- **Scientific reasoning:** v1's Experiment E failed on an unknown scale convention; v1 discovered its own raw data in the final week. Both are inventory failures.
- **Engineering reasoning:** a manifest (`physical_unit, scale_type, aggregation, transform_chain` per data product) is the cheapest guard in the project.
- **Deliverables:** charter (incl. benchmark policy: *GOES is ground truth and one control, never the competitive target*); data inventory + units manifest; risk register; this roadmap frozen.
- **Dependencies:** none. **Duration:** 2 days.
- **Success:** every data product's physical units and provenance documented. **Failure:** any critical product's provenance unresolvable → escalate to owner before Phase 1.
- **Exit:** charter + inventory committed.
- **Risks:** perfunctory execution ("we know our data"). **Mitigation:** the inventory is a gate artifact reviewed at G0, not a formality.
- **Datasets:** all `data/aditya_l1/*`, catalogs. **Tools:** none beyond pandas/astropy.

### Phase 1 — Instrument Characterisation (two stages, strictly ordered)
**Stage 1a — Forensics (exploratory tier, documented not frozen)**
- **Purpose:** explain the R² = 0.0018 anomaly; characterise gain/attenuation modes, pile-up, secular drift, spike contamination; isolate HEL1OS band behaviour during flares (v1 never characterised HEL1OS independently — Experiment E's β₃ ≈ 0 on degenerate features is *not* evidence about the instrument).
- **Scientific reasoning:** the anomaly is the unresolved fork between "our features destroyed the signal" and "the instrument compresses it." Every downstream interpretation inherits its resolution. One-day evidence (X-flare: 1.5 dex SoLEXS vs 3 dex GOES) suggests compression; one day is not a measurement.
- **Deliverables:** forensics report — mode timeline, pile-up curve (rate vs hardness distortion), drift model, per-channel flare-response curves, HEL1OS flare-phase characterisation.
- **Duration:** 2–3 days. **Dependencies:** P0.
- **Success:** anomaly assigned to mechanism(s) with evidence. **Failure:** no mechanism found → do NOT block; proceed to 1b with widened uncertainty, and log the anomaly as an open finding in all downstream reports.

**Stage 1b — Capability Study (confirmatory tier, frozen pre-registration)**
- **Purpose:** measure per-channel calibration scatter σ against GOES flux, boundary-local, with CI; measure flare-window availability. The v1 Experiment E structure (three-outcome decision rule, layered OBSERVED/bridge/decision reporting) is retained — it was the input, not the design, that failed.
- **Scientific reasoning:** this is the single highest-information measurement remaining (FMEA Part 4): both branches are decisive and publishable.
- **Engineering reasoning:** prereg written *after* forensics — v1's design-blindness rule is amended: **blindness applies to outcome distributions, never to schemas, units, or instrument state.** Power analysis mandatory (σ_seed = 0.017 known).
- **Deliverables:** frozen prereg; capability verdict (three-outcome); measured σ(boundary), CI, availability.
- **Duration:** 3–4 days. **Dependencies:** 1a.
- **Success = Gate 1:** the measurement exists under the frozen rule — *any* of the three outcomes passes the gate. The gate tests measurement integrity, not favourability.
- **Risks:** repeating Experiment E's degeneracy. **Mitigation:** predictor units check is a stopping rule; raw per-channel counts only; both absolute and background-relative branches regressed.

### Phase 2 — Data Engineering
- **Purpose:** versioned dataset from raw L2: per-channel features, dual absolute/relative branches, availability masks (no silent imputation), provenance manifest, QA gates; GOES-label build; SoLEXS-native event catalog (secondary ground truth).
- **Scientific reasoning:** SoLEXS is a spectrometer; v1 lump-summed it into a photometer before any model saw it. The spectral dimension is the only untapped severity information. The SoLEXS-native catalog is the only structural answer to "your ground truth is GOES."
- **Engineering reasoning:** QA gates include known-X-flare-day spot checks; every feature ships its manifest entry.
- **Deliverables:** frozen SHA'd dataset; two catalogs; QA report.
- **Duration:** 1 week. **Dependencies:** Gate 1 (branch determines which severity targets are built).
- **Success:** QA green; spot-checks pass; manifest complete. **Failure:** QA reveals upstream defects → return to Phase 1a scope, bounded to 3 days before owner escalation.
- **Risks:** scope creep in catalog construction. **Mitigation:** SoLEXS-native catalog is time-boxed (2 days) and may slip to parallel track P3∥.

### Phase 3 — Baselines & Modelling
- **Purpose & order (fixed):** (i) **B0 physics baselines first** — calibrated-flux threshold detector, persistence, climatology; (ii) M1: shared encoder, dual heads (detection + severity-as-log-flux-regression), 5 seeds, known-good v1 recipe, **selection metric = pre-registered endpoint** (v1 defect corrected); (iii) H1: horizon sweep (0.5–6 h labels on the same encoders — inference-cheap).
- **Scientific reasoning:** v1 never ran the dumbest defensible baseline on calibrated flux; every ML result is uninterpretable without it. Severity as ordinal regression dissolves the arbitrary C/M binary into calibrated confidence. The horizon *curve* ("where does X-ray precursor information die?") replaces the single frozen 6-h point that made v1's forecast arm look like pure failure. 6-h forecasting is demoted to one point on that curve (Known-truth register: ceiling established).
- **Branch behaviour:** Branch S (Gate 1 tight): severity head trained on calibrated flux targets. Branch L (Gate 1 loose): severity *ranking* only (v1-measured AUC ≈ 0.91 capability), and the characterisation result becomes the paper's centrepiece.
- **Pre-declared rule:** if B0 meets the operational profile within CI of M1, **ship B0** — simpler wins; that outcome is a success, not an embarrassment.
- **Deliverables:** B0 report; 5-seed checkpoints; validation endpoints; skill-vs-horizon curve (validation).
- **Duration:** 1 week. **Dependencies:** Gate 2. **Success:** M1 beats B0 on validation by prereg'd margin, or B0 adopted. **Failure:** neither beats persistence-class baselines → Branch L reporting posture.

### Phase 4 — Sealed Validation
- **Purpose:** one-touch test evaluation of every pre-registered endpoint.
- **Test-contamination protocol (declared, non-negotiable):** no unseen data exists — v1 opened the test span (2025-12-15 → 2026-06-14) for specific frozen endpoints. Mitigations: (1) chronological splits identical to v1 so no *additional* exposure occurs by re-splitting; (2) all v2 endpoints frozen before any v2 test access; (3) every v1 test-span exposure enumerated in an appendix; (4) publication reports this history explicitly. Residual risk is real and is disclosed, not hidden.
- **Deliverables:** frozen eval report with CIs; reconciliation checks (v1-style count reconciliation).
- **Duration:** 2–3 days. **Dependencies:** Gate 3. **Success:** endpoints computed, reconciliation green. **Failure:** any reconciliation mismatch → bug protocol, no result reported until resolved.

### Phase 5 — Operational Evaluation
- **Purpose:** full operating-point **frontier** + alarm economics (per-class recall, genuine-false rate via Experiment-A taxonomy, latency, duty cycle, severity confidence), replay-stream demonstration.
- **Scientific reasoning:** v1's binary budget gate buried a working detector under a self-imposed criterion; the v1 stretch criterion (≤5 FE/mo at ≥0.80) is reported as *one labelled reference point on the frontier*, not a verdict.
- **Duration:** 2 days. **Dependencies:** P4.

### Phase 6 — Reporting & Submission
- **Purpose:** hackathon submission; manuscript draft; reproducibility bundle (one-command re-run of every number).
- **Success criterion:** an independent reviewer reproduces every headline number from the bundle. **Duration:** 3–4 days. **Dependencies:** P5.

---

## 2. Decision Gates (no phase begins before its gate)

| Gate | Measurable criteria |
|---|---|
| **G0** | Charter committed; units manifest covers 100% of data products consumed downstream; benchmark policy signed. |
| **G1a** | Anomaly mechanism identified with supporting measurement, OR explicitly logged unresolved with quantified consequence. |
| **G1 (THE FORK)** | Capability verdict issued under frozen prereg (any outcome passes); σ(boundary) + CI + availability on record; branch S/L/intermediate declared in writing. |
| **G2** | Dataset SHA'd; QA gates green; X-flare spot-checks pass; both catalogs delivered (native catalog may carry a logged waiver to parallel track). |
| **G3** | M1 vs B0 comparison complete on validation with prereg'd margin; power check on file; selection metric = endpoint verified in code review. |
| **G4** | Test opened exactly once; all endpoints computed; reconciliation checks green; contamination appendix complete. |
| **G5** | Frontier + alarm economics frozen; replay demo runs end-to-end. |
| **G6** | Independent reproduction of headline numbers succeeds. |

## 3. Critical Path Analysis

- **Critical path:** P0 → P1a → P1b → P2 → P3 → P4 → P5 → P6. Every item on it is analysis-bound, not compute-bound.
- **Highest-risk:** (1) P1a inconclusive (mitigated: non-blocking, widened uncertainty); (2) test-span contamination challenge at review (mitigated: disclosure protocol); (3) deadline compression (mitigated: §5 cut order).
- **Highest-information:** P1b capability study — the fork for everything downstream. Second: H1 horizon curve.
- **Highest-compute:** none worth optimising — v1 evidence: 14 min/seed; the entire modelling phase is < 1 GPU-day equivalent. Compute is explicitly *not* a constraint; do not let it drive design.
- **Highest-scientific-value:** P1b (either branch is the paper's spine); H1 curve; the SoLEXS-native catalog.
- **Parallel-safe:** GOES-label build ∥ P1; SoLEXS-native catalog ∥ P3; report scaffolding + repro bundle ∥ everything from P2 onward; forensics sub-analyses ∥ each other.
- **Never parallel:** prereg *writing* with data examination of the same measurement object; anything with sealed-test access; P1a with P1b (the prereg depends on forensics output by design).

## 4. Timeline (~5 weeks, 2 people)

Week 1: P0 (d1–2) + P1a (d3–5). Week 2: P1b (d1–4) + Gate 1 fork declaration (d5). Week 3: P2. Week 4: P3. Week 5: P4 (d1–3) + P5 (d4–5). Week 6 (buffer): P6.

**Why this order:** uncertainty ordering. The phases are sorted by how much each one's output changes the design of everything after it — the exact inversion of v1, which built models for eight sprints and measured the instrument in its final week. Characterisation gates engineering; engineering gates modelling; modelling earns one test touch; the test touch earns the operational story; the operational story earns the report. No phase is entered on schedule pressure — gates only.

**Compression plan (if deadline < 6 weeks):** cut in this order: SoLEXS-native catalog → H1 horizon resolution (3 points instead of 6) → Branch-S severity head (ship ranking-only) → paper draft (hackathon dossier only). Never cut: P1a, P1b, the B0 baselines, the one-touch test protocol.

## 5. Self-Review Record (revisions this roadmap already absorbed)

1. **Linear → fork-shaped** at G1; a linear plan would misrepresent where the uncertainty lives.
2. **Named the no-unseen-data constraint** and added the contamination-disclosure protocol (P4) — absent from every prior plan, and the first thing a competent referee will ask.
3. **Scoped the operational claim** to replay-stream + latency budget; L2 daily-file cadence makes "real-time" an ISRO ground-segment property, not ours.
4. **Added the "B0 wins → ship B0" rule** to remove the ML-favouring bias every ML team carries.
5. **Gave HEL1OS an explicit characterisation task**; v1 produced no valid evidence about the instrument (only about degenerate features of it).
6. **Amended the design-blindness rule** (blind to outcomes, never to units/schemas) — the precise failure mode of Experiment E.
7. **Dropped a separate "representation learning" phase** from the earlier blueprint sketch — Experiment D showed no evidence it buys anything over joint training; it was roadmap ornamentation.
8. **Made Gate 1 outcome-neutral** (the gate is that the measurement exists) — a gate that only passes on good news is not a gate, it is a bias.
