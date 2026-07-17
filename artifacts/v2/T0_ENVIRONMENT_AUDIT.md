<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Phase 0 / T0 execution report. Contains a roadmap-invalidating discovery. -->
<!-- DATE: 2026-07-17 -->

# T0 — Environment Audit & Dependency Closure: Execution Report

**Verdict: environment PASS (after remediation) — but T0's mandate to "verify every prerequisite, assume nothing, measure everything" uncovered a project-existential finding: the Aditya-L1 data archive used by ALL of v1 is synthetic. Execution is STOPPED per governing rules pending roadmap amendment approval.**

---

## 1. Environment audit (items 1–16)

1. **Python:** 3.12.12 (venv-local).
2. **Venv:** healthy, `venv/` on project volume, prefix verified.
3. **Package inventory (key):** numpy 1.26.4, pandas 2.2.2, scikit-learn 1.5.0, scipy 1.17.1, torch 2.12.1, pyarrow 16.1.0, matplotlib 3.11.0, astropy 6.1.7 (new).
4. **Missing packages:** astropy (now closed).
5. **astropy status:** installed. **Incident:** `pip install astropy` (unpinned) pulled astropy 8.0.1 and **silently upgraded numpy 1.26.4 → 2.5.1**, breaking the v1 reproducibility baseline. Remediated: numpy re-pinned to 1.26.4, astropy pinned `<7` → 6.1.7. `pip check`: no broken requirements.
6. **FITS parsing capability:** OBSERVED functional — genuine FITS opens, headers and binary tables read (§3).
7. **Disk usage:** repo 38 GB.
8. **Available storage:** 893 GiB free on the T7 volume.
9. **Hardware:** Apple M4, 16 GB RAM, torch MPS available = True.
10. **Repository health:** `git fsck` initially reported invalid refs and bad sha1 files — all were macOS AppleDouble (`._*`) junk inside `.git/refs` and `.git/objects` (exFAT volume). Purged; fsck now clean (one dangling tree, normal). Residual `._*` pollution exists across data directories (harmless to parquet readers; T3 must inventory it).
11. **Git status:** working tree clean at audit start.
12. **Branch:** `main`.
13. **Latest commit:** `c85a88a` (v2 roadmap).
14. **Dependency conflicts:** none after remediation. AppleDouble `._*` entries in site-packages caused pip "invalid distribution" warnings — purged.
15. **Environment risks:** (a) unpinned installs can silently move the numpy baseline — **mitigation: a `requirements.lock` must be created in T2**; (b) exFAT AppleDouble regeneration by Finder — cosmetic, periodic cleanup; (c) no `requirements.txt` exists at repo root.
16. **Recommended fixes:** lockfile (T2); `export COPYFILE_DISABLE=1` in dev shells; the data-layer actions in §5.

## 2. THE FINDING — the Aditya-L1 archive is synthetic

Evidence chain, all OBSERVED today:

1. All 915 `data/aditya_l1/raw/solexs/ad1_solexs_l2_*.fits` are **exactly 204,800 bytes**. `scripts/aditya_l1/download_payload_data.py` contains `generate_mock_fits_file(dest_path, size_kb=200)` — writes one FITS header card + null padding, invoked by `--mock`. The files are unparseable by astropy (no END card, null padding) and contain **no data**.
2. `scripts/aditya_l1/parse_fits.py` falls back to `generate_simulated_solexs_data()` / `generate_simulated_hel1os_data()` whenever astropy is unavailable **or parsing fails**. Both conditions held for the entire v1 history (astropy first installed today; mock files unparseable regardless). The simulators are date-seeded uniform noise + 0–3 random exponential spikes/day; SoLEXS "channel" is `randint(1,10)` **per sample** — not even coherent spectra.
3. Decisive statistical test: dataset `log_solexs_soft` vs real GOES `long_flux` over 786,298 aligned training minutes: **corr = −0.0068**. The "Aditya" observables are statistically independent of real solar activity.
4. Per-feature scan of the 15 "Aditya-only" nowcast features: 14 correlate with real GOES flux at |r| < 0.024 (noise). **`nonthermal_thermal_ratio` correlates −0.9151** — its own code (`features_v4/aditya.py`, class `NonthermalThermalRatio`) declares `instrument = "hel1os+goes"`, `requires = ("hel1os_rate_band0", "long_flux")`: synthetic noise divided by **real GOES long flux** → the feature is a disguised −log(GOES).
5. Ten directories in `raw_extracted/solexs/` (`AL1_SLX_L1_20260602..20260614_v1.0`) are **genuine ISSDC SoLEXS L1 products**: per-SDD `.gti/.lc/.pi` files, variable sizes (1 KB–8.5 MB), compliant FITS, `TELESCOP='AL1'`, `INSTRUME='SoLEXS'`, 86,400 rows/day at 1-s cadence. A real download succeeded for ~10 days in mid-June 2026; the mock generator filled the other 905.

## 3. What this resolves and what it voids

**Resolved:** Experiment E's R² = 0.0018 anomaly — completely. The regression predictors were three noise features; R² ≈ 0 is the *correct* measurement of synthetic noise. Experiment E functioned exactly as designed and was the instrument that exposed this.

**Reinterpreted (frozen artifacts untouched; correction memorandum required):**
- The v1 "Aditya-only" nowcaster is actually a **GOES-long-flux detector** operating through one disguised feature. Its measured numbers (recall M 0.909/X 0.900, ~1/month genuine false, Experiment A's 94.2% C-overlap) remain valid *as measurements of that GOES-driven detector* — the flares it detects are real, via GOES.
- "Aditya-only forecast TSS 0.359" = one noisy GOES transform + 14 noise channels; coherent with the real 17-feature era-matched GOES control at 0.4383.
- Sprints 30–32's "Aditya adds nothing to GOES" (ISRO NOT SUPPORTED) is trivialized: the Aditya features were noise, so of course they added nothing. The question is **unanswered**, not answered in the negative.
- All GOES-side science (Study A, S2 dataset, era-matched control, forecast-ceiling diagnostic on GOES data) stands — `goes_full.parquet` is real archive data.
- **No experiment has ever been run on real Aditya-L1 data.** The ISRO problem statement is, as of today, unaddressed.

**Why three audits missed it:** every guard checked schemas, leakage, statistics, and provenance *within* the pipeline — none checked physical authenticity against an independent instrument. The 0.91-recall detector looked like Aditya working; it was GOES working.

## 4. Verdict & gate

- **Environment (T0 letter): PASS** — evidence in §1; FITS capability proven on genuine ISSDC files.
- **Phase 0 continuation to T1: NO — STOP.** Governing rule: "If execution reveals that the governing roadmap is incorrect, stop immediately… wait for approval." Roadmap standing-assumption #3 and the known-truth item "raw per-channel L2 data exists and was never used" are **false** (what exists is synthetic; the 10 real days are the exception). Phase 1 (instrument characterisation) is impossible on synthetic data. Branch S/L of Gate 1 are both meaningless until real data exists.

## 5. Recommended roadmap amendment (awaiting owner approval)

1. **Insert Phase 0.5 — Data Authenticity & Acquisition** before Phase 1: (a) acquire real SoLEXS+HEL1OS L1/L2 from ISSDC/PRADAN for the mission span — likely requires owner credentials/portal action; the 10-day corpus proves the path worked in June 2026; (b) meanwhile, build and validate real-product parsers (`.lc/.pi/.gti`, per-SDD) against the 10 authentic days; (c) quarantine `data/aditya_l1/{raw,processed}` as `SYNTHETIC — DO NOT USE` by register.
2. **Add an authenticity gate to the charter:** no dataset enters any experiment without either cross-correlation against an independent reference instrument or physics-consistency checks (flare-catalog coincidence at minimum).
3. **Correction memorandum** (new artifact, frozen artifacts untouched) re-labelling every v1 "Aditya" conclusion per §3.
4. **Timeline:** Phases 1–6 shift behind the external acquisition dependency (duration unknown, owner-gated). Parser development on the 10-day corpus can proceed in parallel immediately upon approval.
5. Known-truth register: strike the voided item; add this finding.

## 6. Self-review / falsification attempt

Attempted falsifications of the synthetic-data conclusion: (i) *"the processed parquets came from a different, real source"* — refuted: dataset feature correlates 0.93 with the recomputed band-sum from the simulated parquets, and −0.007 with real GOES; (ii) *"the mock generator was only used for a few gap days"* — refuted: 915/915 files byte-identical at the mock size, incompatible with any real archive; (iii) *"detector performance proves the data must be real"* — refuted: the performance is fully explained by the GOES-requiring feature, and the per-feature correlation scan confirms no other feature carries signal; (iv) *"the 10 ISSDC directories are also mock"* — refuted: variable sizes, compliant FITS, coherent product structure, plausible headers. The conclusion survives all four attempts. One earlier error corrected in the process: my Phase-0-checklist statement that processed data was "9 channels at 5-second cadence, counts/s, genuine absolute scale" — that was a description of the *simulator's output*; it is withdrawn.
