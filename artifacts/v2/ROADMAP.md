<!-- VERSION STATUS: GOVERNING DOCUMENT — REVISION 1 -->
<!-- REASON: AdityaNet v2 master roadmap. r0: joint PI review, FMEA, redesign review (2026-07-17, commit c85a88a). r1: data-authenticity amendment (2026-07-17) — see §6 Revision History. -->
<!-- SUPERSEDED BY: n/a -->
<!-- DATE: 2026-07-17 -->

# AdityaNet v2 — Master Roadmap (Governing Document, Revision 1)

**Status:** governing. Amendable only by a logged revision with rationale; never edited silently. Original r0 preserved at commit `c85a88a`; this is Revision 1 (owner-approved amendment; see §6 for what changed and why).
**Provenance:** synthesises the completed v1 evidence base (Sprints 24–33, Experiments A/C/D/E, three adversarial audits, FMEA of 2026-07-17) **as reinterpreted by the T0 data-authenticity finding and its forensic confirmation** (`T0_ENVIRONMENT_AUDIT.md` @ `ecff8eb`, `T0_FORENSIC_VERIFICATION.md` @ `dd2defb`). Every design decision below cites the evidence that forced it.

---

## 0. Vision

Measure what the Aditya-L1 X-ray payloads can actually see, then build the strongest honest product on top of that measurement — a flare nowcaster with severity estimation and a characterised prediction-skill curve — such that every reported number survives adversarial audit.

v1's central lesson, encoded here as the ordering principle: **understand the instrument before featurizing it; featurize before modelling; pre-register conclusions before looking at outcomes — but never before knowing what object is being measured.**

## 0.1 Objectives (deliberately separated; v1's core strategic error was blending them)

- **Scientific:** measure the information content of SoLEXS+HEL1OS with respect to (i) flare detection, (ii) severity discrimination at the C/M boundary, (iii) precursor information as a function of horizon. The deliverable is the measurement, whichever way it falls.
- **Engineering:** a reproducible one-command pipeline raw-FITS → alert stream, with declared physical units and provenance at every stage, and QA gates that fail loudly.
- **Operational:** a GOES-independent alert channel at Lagrange point L1 with quantified alarm economics (per-class recall, genuine-false rate, latency, severity confidence), demonstrated on a replay stream. **Scope limit (declared, updated r1):** the real ISSDC products are Level-1 daily/orbit archives delivered post-hoc; true real-time operation is an ISRO ground-segment capability outside this project. We deliver the algorithmic pipeline and its latency budget, not a real-time service. **GOES-independence (r1):** now a *verified property*, enforced by the charter — v1's `nonthermal_thermal_ratio` lesson: no feature may require GOES at runtime; GOES is ground truth and control only.
- **Hackathon:** an automated pipeline satisfying the brief's literal ask ("detect or predict solar flares from combined SoLEXS+HEL1OS") and its motivation (disruption anticipation ⇒ M/X focus), with severity ranking and an honest evaluation dossier as differentiators.
- **Publication:** one paper: instrument capability characterisation (either branch of Gate 1) + the detection system + the skill-vs-horizon curve + the rigorous 6-h negative result, targeted at Space Weather / Solar Physics / JGR-class venues.

## 0.2 Standing assumptions (each is a risk if false)

1. Hackathon deadline ≥ 6–7 weeks out (owner to confirm; compression plan in §5).
2. The GOES/NOAA flare catalog is acceptable primary ground truth — **upgraded from assumption to verified fact in r1**: catalog and `goes_full.parquet` authenticated against the real May-2024 storm (X8.7 matches to the minute).
3. ~~The 915-day L2 archive is processing-stable across the mission~~ — **INVALIDATED (r1)**: that archive is synthetic (mock FITS + date-seeded simulation; forensically confirmed bit-identical to its generator). **Replacement assumption 3′:** the 21 GB genuine ISSDC archive (`data_pipeline/downloads/raw/`, 431 SoLEXS daily L1 ZIPs + ~396 HEL1OS orbit ZIPs, 2024-02 → 2026-06) is representative of the products ISRO provides, and its ~431 real SoLEXS days are sufficient for Phases 1–3 while the Jun 2024 – May 2025 gap-fill is acquired (Phase 0.5 quantifies this).
4. Laptop-class compute suffices (evidenced: 14 min/seed detector training in v1; compute is nowhere near the critical path).
5. Team of ~2 (one scientist, one engineer), single timeline.
6. **(new, r1)** Gap-fill acquisition from ISSDC/PRADAN is possible but owner-gated and of unknown duration; the roadmap does not block on it (Phase 0.5.3).

## 0.3 Inherited-asset register (immutable) — r1

Inherited **verbatim**: the episode-level evaluation harness (block bootstrap, 2,880-window blocks, frozen seeds), the leakage/provenance guard system, the pre-registration discipline with OBSERVED/DERIVED/HYPOTHESIS labelling, and every v1 frozen number — **with r1 re-labelling**: GOES-side results (Study A, S2 dataset, era-matched control 0.438, forecast-ceiling diagnostic) inherit as *authenticated baselines*; all v1 "Aditya" numbers inherit only as *measurements of a synthetic-features system whose sole real signal was GOES long flux* (they remain useful as behavioural baselines of a GOES-flux-driven detector, and as methodology validation).
**Quarantined (r1, by register — never deleted, never consumed):** `data/aditya_l1/raw/` (mock FITS), `data/aditya_l1/processed/` (simulator output), every `dataset_v4*` / `dataset_adi_nowcast` "Aditya" feature column, and `scripts/aditya_l1/parse_fits.py`'s simulation fallback path (the fallback pattern itself is banned in v2: parsers must fail loudly, never simulate).
**Newly inherited real assets (r1):** `data_pipeline/downloads/raw/` — 827 authentic ISSDC ZIPs (21 GB); the 10 extracted real days in `raw_extracted/`; `goes_full.parquet` and the flare catalog, now authenticated.
Inherited **nothing else** without a units-and-provenance check.

## 0.4 Known-truth register (results no v2 experiment may ignore or silently re-litigate) — r1

**GOES-side (authenticated, stands):** era-matched GOES 6-h TSS 0.438; forecast-ceiling diagnostic (data-fraction flat; size-matched control trains at 0.8748, d ≈ 15) — establishes the 6-h X-ray-forecasting ceiling *on GOES data*; seed-level class-AUC SD ≈ 0.017 (all power analyses use this); GOES archive and flare catalog verified against the real May-2024 storm.
**Reinterpreted (r1):** the v1 nowcaster's numbers (recall M 0.909 / X 0.900 / C 0.244 / B 0.002; 94.22% C-overlap of false episodes; ~1/month genuine false; policy layer on-frontier; representation probes +0.0026) are measurements of a **disguised GOES-long-flux detector** (13–14 noise features + `nonthermal_thermal_ratio` at corr −0.92 with GOES). They stand as evidence of what a single noisy GOES-flux transform achieves under the frozen harness — a legitimate baseline for v2 — and as validation that the evaluation machinery works. They say **nothing about Aditya-L1**.
**Resolved (r1):** the Experiment E R² = 0.0018 anomaly — fully explained (regression on synthetic noise); Experiment E functioned correctly and was the instrument that exposed the synthetic archive.
**New facts (r1, forensically confirmed):** the v1 Aditya archive is synthetic (bit-identical to its date-seeded generator; astropy was absent for v1's entire history, so the parser always fell back to simulation); 21 GB of genuine ISSDC L1 data (431 SoLEXS days + ~396 HEL1OS orbit files, 2024-02 → 2026-06, coverage hole Jun 2024 – May 2025) exists on disk and was never consumed; **no experiment has ever run on real Aditya-L1 data — the ISRO problem statement is unaddressed as of r1.**

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

### Phase 0.5 — Data Authenticity & Real-Archive Activation (inserted by r1)

- **Purpose:** convert the discovered 21 GB genuine ISSDC archive into an authenticated, parsed, coverage-quantified data foundation; quarantine every synthetic product; institutionalise the authenticity check that v1 lacked. This phase exists because T0 proved the project has never touched real Aditya-L1 data.
- **Scientific motivation:** no measurement about an instrument can be made from data the instrument did not produce. Until real data is activated, Gate 1 (the capability fork) is undefined and every downstream phase is meaningless. Additionally, the first physics look at real SoLEXS data — its response to the catalogued May-2024 X-flare sequence — is itself the project's first genuine scientific observation.
- **Engineering motivation:** the real archive is L1 orbit/day products (`.lc/.pi/.gti` per SDD detector; HEL1OS `HLS_*` orbit ZIPs with `aux/hk.fits`, GTI, pixel maps) — a materially different format from anything v1 parsed. v1's fatal pattern — a parser that silently falls back to simulation — is banned: v2 parsers fail loudly on any unreadable input.
- **Tasks & deliverables:**
  1. **0.5.1 Extraction & manifest** — unzip all 827 archives to a versioned store; SHA-256 manifest of every member file; per-day/per-orbit coverage table for both instruments (this produces the HEL1OS coverage profile, an open item from the forensic report).
  2. **0.5.2 Real parsers** — SoLEXS `.lc/.pi/.gti` (per-SDD) and HEL1OS orbit products → tidy per-second/per-minute tables with declared units; validated against ≥ 3 hand-checked days **including 2024-05-14** (the X8.7 day: the real instrument's response to the strongest flare in the archive is the first physics sanity check); GTI-based availability masks (no imputation).
  3. **0.5.3 Coverage quantification & gap-fill request** — measured usable-day counts per instrument per month; a written acquisition request for Dec 2023 – Jan 2024 and Jun 2024 – May 2025 (**owner action**, ISSDC/PRADAN); explicit statement of what Phases 1–3 can and cannot conclude on ~431 days.
  4. **0.5.4 Authenticity gate (charter amendment)** — no dataset enters any experiment without a flare-catalog coincidence check against an independent reference (superposed-epoch response of the candidate data around catalogued M/X flares must show the instrument signature); applied first to the real archive itself.
  5. **0.5.5 Quarantine & correction memorandum** — synthetic directories registered SYNTHETIC — DO NOT USE (§0.3); a v1 correction memorandum re-labelling every "Aditya" conclusion per §0.4, explicitly re-affirming the GOES-side results (frozen v1 artifacts untouched).
- **Dependencies:** T0 complete (environment + astropy: done); owner approval of this revision.
- **Required datasets:** `data_pipeline/downloads/raw/` (21 GB), GOES catalog + `goes_full.parquet` (authenticated reference).
- **Required tools:** astropy 6.1.7 (installed), zipfile/gzip, pandas/pyarrow — no new dependencies expected.
- **Estimated duration:** ~1 week (0.5.1–0.5.2 dominate); 0.5.3's acquisition runs asynchronously and does not block Gate 0.5.
- **Exit criteria = Gate G0.5 (measurable):** (i) 100% of the 827 archives extracted or explicitly logged corrupt, with SHA manifest; (ii) parsers reproduce ≥ 3 hand-validated days including 2024-05-14; (iii) the real archive **passes its own authenticity gate** (catalog-coincidence signature present, quantified); (iv) coverage table + gap-fill request delivered; (v) quarantine register + correction memorandum committed.
- **Failure criteria:** the real archive fails the coincidence check at scale (would mean even the downloads are not usable instrument data → STOP, owner escalation — acquisition becomes the project's sole path); or usable SoLEXS coverage < ~300 days after extraction (Gate 1 power compromised → owner decision on waiting for gap-fill vs proceeding scoped).
- **Risks & mitigations:** unknown L1 format variants across 2.5 years (mitigate: fail-loud parsers + per-file error ledger; corrupt files logged, never skipped silently); HEL1OS orbit-file complexity underestimated (mitigate: SoLEXS-first ordering — Gate 1 needs SoLEXS; HEL1OS may lag into Phase 2); the 54 MB `downloads/corrupted` dir suggests some archives failed ISSDC-side (inventory them explicitly); disk (21 GB compressed → est. 40–80 GB extracted; 893 GiB free — ample).

### Phase 1 — Instrument Characterisation (two stages, strictly ordered) — re-scoped by r1
**Stage 1a — Real-instrument forensics (exploratory tier, documented not frozen)**
- **Purpose (r1):** ~~explain the R² = 0.0018 anomaly~~ — resolved (synthetic data). Now: characterise the **real** instruments from the activated archive — gain/attenuation modes, pile-up, secular drift, background behaviour, per-SDD consistency, spike/particle contamination; HEL1OS band behaviour during flares (still never characterised — v1 produced zero evidence about either real instrument).
- **Scientific reasoning (r1):** every prior belief about SoLEXS dynamic range, compression, or gaps derived from the simulator and is void (e.g., the "1.5 dex X-flare response" was a property of the random generator). Phase 1 starts from a clean slate on real data; the capability fork (Gate 1) inherits everything from it.
- **Deliverables:** forensics report — mode timeline, pile-up curve (rate vs hardness distortion), drift model, per-channel flare-response curves, HEL1OS flare-phase characterisation.
- **Duration:** 3–4 days (r1: slightly longer — clean-slate characterisation, not anomaly triage). **Dependencies (r1):** Gate G0.5 (activated real archive).
- **Success (r1):** real-instrument behaviour characterised with evidence — dynamic-range/pile-up curve measured across the May-2024 X-flare sequence, drift and background quantified, per-SDD consistency checked. **Failure:** instrument behaviour too irregular to characterise → do NOT block; proceed to 1b with widened uncertainty, logged in all downstream reports.

**Stage 1b — Capability Study (confirmatory tier, frozen pre-registration)**
- **Purpose:** measure per-channel calibration scatter σ against GOES flux, boundary-local, with CI; measure flare-window availability. The v1 Experiment E structure (three-outcome decision rule, layered OBSERVED/bridge/decision reporting) is retained — it was the input, not the design, that failed.
- **Scientific reasoning:** this is the single highest-information measurement remaining (FMEA Part 4): both branches are decisive and publishable.
- **Engineering reasoning:** prereg written *after* forensics — v1's design-blindness rule is amended: **blindness applies to outcome distributions, never to schemas, units, or instrument state.** Power analysis mandatory (σ_seed = 0.017 known).
- **Deliverables:** frozen prereg; capability verdict (three-outcome); measured σ(boundary), CI, availability.
- **Duration:** 3–4 days. **Dependencies:** 1a.
- **Success = Gate 1:** the measurement exists under the frozen rule — *any* of the three outcomes passes the gate. The gate tests measurement integrity, not favourability.
- **Risks:** repeating Experiment E's degeneracy. **Mitigation:** predictor units check is a stopping rule; raw per-channel counts only; both absolute and background-relative branches regressed.

### Phase 2 — Data Engineering
- **Purpose (r1):** versioned dataset from the **authenticated real L1 archive** (Phase 0.5 outputs): per-channel features, dual absolute/relative branches, GTI-derived availability masks (no silent imputation), provenance manifest, QA gates **including the authenticity gate**; GOES-label build; SoLEXS-native event catalog (secondary ground truth).
- **Scientific reasoning:** SoLEXS is a spectrometer; v1 lump-summed it into a photometer before any model saw it. The spectral dimension is the only untapped severity information. The SoLEXS-native catalog is the only structural answer to "your ground truth is GOES."
- **Engineering reasoning:** QA gates include known-X-flare-day spot checks; every feature ships its manifest entry.
- **Deliverables:** frozen SHA'd dataset; two catalogs; QA report.
- **Duration:** 1 week. **Dependencies:** Gate 1 (branch determines which severity targets are built).
- **Success:** QA green; spot-checks pass; manifest complete. **Failure:** QA reveals upstream defects → return to Phase 1a scope, bounded to 3 days before owner escalation.
- **Risks:** scope creep in catalog construction. **Mitigation:** SoLEXS-native catalog is time-boxed (2 days) and may slip to parallel track P3∥.

### Phase 3 — Baselines & Modelling
- **Purpose & order (fixed):** (i) **B0 physics baselines first** — calibrated-flux threshold detector, persistence, climatology; (ii) M1: shared encoder, dual heads (detection + severity-as-log-flux-regression), 5 seeds, known-good v1 recipe, **selection metric = pre-registered endpoint** (v1 defect corrected); (iii) H1: horizon sweep (0.5–6 h labels on the same encoders — inference-cheap).
- **Scientific reasoning:** v1 never ran the dumbest defensible baseline on calibrated flux; every ML result is uninterpretable without it. Severity as ordinal regression dissolves the arbitrary C/M binary into calibrated confidence. The horizon *curve* ("where does X-ray precursor information die?") replaces the single frozen 6-h point that made v1's forecast arm look like pure failure. 6-h forecasting is demoted to one point on that curve (Known-truth register: ceiling established).
- **Branch behaviour (r1):** Branch S (Gate 1 tight): severity head trained on calibrated flux targets. Branch L (Gate 1 loose): severity *ranking* only — its achievable level is **unknown** and will be measured fresh on real data (r1 correction: the previously cited "AUC ≈ 0.91" was the synthetic system reading disguised GOES and says nothing about real Aditya capability); the characterisation result becomes the paper's centrepiece.
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
| **G0** | Charter committed; units manifest covers 100% of data products consumed downstream; benchmark policy signed; **(r1)** charter includes the authenticity gate and the no-runtime-GOES rule. |
| **G0.5 (r1)** | 827 archives extracted or logged corrupt with SHA manifest; parsers reproduce ≥ 3 hand-validated days incl. 2024-05-14; real archive passes the catalog-coincidence authenticity check (quantified); coverage table + gap-fill request delivered; quarantine register + v1 correction memorandum committed. |
| **G1a** | Real-instrument characterisation report delivered (dynamic range, pile-up, drift, per-SDD consistency, HEL1OS flare behaviour), OR irregularities explicitly logged with quantified consequence. *(r1: anomaly-triage wording removed — resolved.)* |
| **G1 (THE FORK)** | Capability verdict issued under frozen prereg (any outcome passes); σ(boundary) + CI + availability on record; branch S/L/intermediate declared in writing. |
| **G2** | Dataset SHA'd; QA gates green; X-flare spot-checks pass; both catalogs delivered (native catalog may carry a logged waiver to parallel track). |
| **G3** | M1 vs B0 comparison complete on validation with prereg'd margin; power check on file; selection metric = endpoint verified in code review. |
| **G4** | Test opened exactly once; all endpoints computed; reconciliation checks green; contamination appendix complete. |
| **G5** | Frontier + alarm economics frozen; replay demo runs end-to-end. |
| **G6** | Independent reproduction of headline numbers succeeds. |

## 3. Critical Path Analysis — r1

- **Critical path:** P0 → **P0.5** → P1a → P1b → P2 → P3 → P4 → P5 → P6. Every item on it is analysis-bound, not compute-bound.
- **Highest-risk (r1):** (1) **the real archive failing its own authenticity check at scale** (P0.5 failure criterion — would leave acquisition as the only path); (2) HEL1OS orbit-format complexity delaying Gate 0.5 (mitigated: SoLEXS-first; HEL1OS may lag into P2); (3) the Jun 2024 – May 2025 coverage hole limiting Gate 1 power (mitigated: 0.5.3 quantifies before 1b pre-registers; owner-gated gap-fill runs async); (4) deadline compression (§5 cut order).
- **Highest-information:** P1b capability study — the fork for everything downstream, now on real data. Second: P0.5.2's first look at the real May-2024 X-flare response (the project's first genuine Aditya observation). Third: H1 horizon curve.
- **Highest-compute:** none worth optimising — v1 evidence: 14 min/seed; the entire modelling phase is < 1 GPU-day equivalent. Compute is explicitly *not* a constraint; do not let it drive design.
- **Highest-scientific-value:** P1b (either branch is the paper's spine); the v1 synthetic-data finding itself (a methodology lesson worth publishing honestly); H1 curve; the SoLEXS-native catalog.
- **Parallel-safe:** 0.5.1 extraction ∥ charter work; 0.5.3 gap-fill acquisition ∥ everything (owner-gated, async); GOES-label build ∥ P1; SoLEXS-native catalog ∥ P3; report scaffolding + repro bundle ∥ everything from P2 onward.
- **Never parallel:** prereg *writing* with data examination of the same measurement object; anything with sealed-test access; P1a with P1b (the prereg depends on characterisation output by design).
- **Test-span note (r1, improves on r0):** r0 assumed "no unseen data exists." Partially wrong in v2's favour: v1's models and analyses never touched *real* Aditya measurements anywhere, so the feature side of a real-data test split is virgin everywhere; only **label-side** knowledge of the v1 test span (flare lists, FE counts) is contaminated. P4's disclosure protocol is retained with this sharper scope.

## 4. Timeline (~6 weeks + buffer, 2 people) — r1

Week 1: P0 remainder (T1–T7, d1–2) + P0.5.1 extraction (d2–5). Week 2: P0.5.2 parsers + authenticity check (d1–4); Gate 0.5 (d5); 0.5.3 gap-fill request issued to owner. Week 3: P1a (d1–4) + P1b prereg (d5). Week 4: P1b execution + Gate 1 fork (d1–3); P2 begins (d4–5). Week 5: P2 completes + P3. Week 6: P4 (d1–3) + P5 (d4–5). Week 7 (buffer): P6.

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

**r1 additions:**

9. **T0's "assume nothing" mandate was load-bearing, not ceremonial** — the environment audit's FITS-capability check is what unravelled the synthetic archive. Keep audit tasks scientific.
10. **Authenticity gate institutionalised** (0.5.4): catalog-coincidence checks against an independent reference before any dataset enters any experiment — the one-week check that would have caught v1's defect at its start.
11. **Fail-loud parser rule**: no data-layer code may fall back to simulation or defaults on parse failure; v1's silent `parse_fits.py` fallback is the single proximate cause of thirty sprints on synthetic data.
12. **No-runtime-GOES rule** promoted to charter law (the `nonthermal_thermal_ratio` lesson): GOES is ground truth and control, never a model input in the Aditya frame.
13. **Corrected r0's own error**: r0's known-truth register asserted "raw per-channel L2 data exists" based on the synthetic store — even the redesign inherited an unverified claim. Every register entry now requires forensic-grade provenance.

## 6. Roadmap Revision History

### Revision 1 — 2026-07-17 (owner-approved)

**Trigger:** Phase 0 / T0 execution finding, independently forensically confirmed (`artifacts/v2/T0_ENVIRONMENT_AUDIT.md` @ commit `ecff8eb`; `artifacts/v2/T0_FORENSIC_VERIFICATION.md` @ commit `dd2defb`).

**Evidence that required the amendment (all forensically verified):** (1) all 915 v1 "raw" SoLEXS FITS are content-identical mocks (one SHA-256 across the mission span; generator function present in repo); (2) the processed parquet store regenerates **bit-identically** from the date-seeded simulator, including on days where real data exists on disk; (3) training features derive from that store and correlate −0.007 with real GOES flux; (4) the sole signal-bearing "Aditya" feature requires GOES `long_flux` by its own metadata (corr −0.9151) — the v1 nowcaster is a disguised GOES-flux detector; (5) 21 GB of genuine ISSDC L1 data (431 SoLEXS days + ~396 HEL1OS orbit files) exists in `data_pipeline/downloads/raw/`, never consumed; (6) the GOES archive and flare catalog are authentic (May-2024 X8.7 storm matched to the minute).

**Assumptions invalidated:** standing assumption 3 (the 915-day archive is real/processing-stable); r0's known-truth item "raw per-channel L2 data exists and was never used" (as it referred to the synthetic store); r0's Phase 1a premise (the R² anomaly as an open fork — now resolved); the implicit r0 belief that the operational claim of GOES-independence was already true of v1's detector.

**Assumptions that remain valid:** GOES catalog as primary ground truth (now *verified*, upgraded from assumption); laptop-class compute sufficiency; team size; the entire methodological architecture (fork-shaped plan, outcome-neutral gates, prereg discipline, B0-wins rule, one-touch test protocol); the v1 evaluation harness and GOES-side science.

**What changed:** inserted Phase 0.5 (Data Authenticity & Real-Archive Activation) with Gate G0.5; re-scoped Phase 1a from anomaly triage to clean-slate real-instrument characterisation; re-pointed Phase 2 at the authenticated L1 archive; rewrote §0.2/§0.3/§0.4 registers; added the authenticity gate, fail-loud parser rule, and no-runtime-GOES rule; updated critical path, timeline (~6 weeks + buffer), gates table, and the test-span contamination scope (label-side only — real-feature side is virgin everywhere).

**Traceability:** r0 preserved verbatim at commit `c85a88a` (tagged in git history); this revision is additive-and-annotated — struck-through text is retained where the change itself is instructive.
