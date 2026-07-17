<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Independent forensic verification of the T0 synthetic-data finding. -->
<!-- DATE: 2026-07-17 -->

# Forensic Verification of the T0 Finding

**Scope:** treat "the Aditya-L1 data used by v1 was synthetic and the reported Aditya results are invalid" as a hypothesis; attempt to falsify it with tests independent of the original evidence. **Outcome: every critical claim CONFIRMED, one materially new discovery (a 21 GB genuine ISSDC archive on disk, never consumed by the model pipeline), and one v1 claim additionally authenticated (the GOES side is real).**

All tests run 2026-07-17; commands and outputs reproducible from this report.

---

## Claim 1 — The 915 raw FITS files are mock

- **Evidence:** six files sampled across the mission span (2023-12-13 … 2026-06-14) have **one** unique SHA-256 — byte-identical content. Identical files cannot encode per-day observations. Source generator `generate_mock_fits_file(size_kb=200)` present in `scripts/aditya_l1/download_payload_data.py`; 204,800 B = 200 KiB exactly, matching all 915 file sizes.
- **Refutation attempts:** "sample bias" — the six samples span first day, last day, and four interior dates over 2.5 years; identical hashes across that span rule out real content for any plausible archive. "Real data with fixed container size" — refuted by content hash identity, not just size.
- **Alternative explanations:** none survive content identity.
- **Strengthening evidence available:** hash all 915 (expected: 1 unique).
- **Verdict: CONFIRMED.**

## Claim 2 — The processed parquets are simulator output

- **Evidence (new, strongest possible):** the simulator is date-seeded and deterministic. Regenerating with `generate_simulated_solexs_data()` and diffing against stored parquets: **bit-identical** (`rate` allclose, `channel` array_equal) on 2023-12-13 (first day), 2024-05-09 (X-flare day), and 2026-06-02 (a day for which *real* ISSDC data exists on disk). HEL1OS likewise bit-identical on the tested day.
- **Refutation attempts:** "parquets came from a different real source" — impossible; bit-identity with a pseudo-random generator has no alternative explanation. "Only some days simulated" — the three probes bracket the span, including the most favourable candidate for real data (a day with a real download present); even there, simulation was stored.
- **Verdict: CONFIRMED.**

## Claim 3 — Training features derive from the simulated parquets (lineage)

- **Evidence:** `build_multi_instrument_dataset.py:77,80` reads exactly `data/aditya_l1/processed/{solexs,hel1os}/*.parquet` (the simulated stores). Recomputing `log_solexs_soft` from *regenerated* simulator output for 2024-05-09 vs the training parquet column: Pearson 0.952, Spearman 0.779 (the non-monotone residual is consistent with the documented train-p95 winsorisation + scaling steps). Independently: the dataset feature correlates −0.0068 with real GOES flux over 786,298 minutes — excluding any real-solar origin.
- **Refutation attempts:** "the dataset was rebuilt later from a different source" — the lineage path constants, the correlation with regenerated simulation, and the null correlation with real activity triangulate; a real source would produce the opposite signature on all three.
- **Strengthening evidence:** re-running the builder end-to-end (heavier; not required given triangulation).
- **Verdict: CONFIRMED.**

## Claim 4 — No real SoLEXS measurements entered the training pipeline

- **Evidence:** Claim 2's bit-identity on 2026-06-02 proves that even where real data existed, the stored product is simulation. The real archive (below) lives under `data_pipeline/downloads/raw/`, outside the builder's input globs. The 14 SoLEXS/HEL1OS-derived features correlate |r| < 0.024 with real GOES flux.
- **Refutation attempts:** "real data entered via the availability columns" — `solexs_available` correlates 0.0019 with real GOES flux; its exact provenance is unresolved (logged as an open item) but it demonstrably carries no solar signal into the models.
- **Verdict: CONFIRMED** (with the availability-column provenance flagged as an open, non-material item).

## Claim 5 — A GOES-derived quantity sat inside the "Aditya-only" feature set

- **Evidence:** `features_v4/aditya.py` class `NonthermalThermalRatio`: `instrument = "hel1os+goes"`, `requires = ("hel1os_rate_band0", "long_flux")` — real GOES long flux in the denominator, by code and by declared spec. Measured corr with log GOES flux: **−0.9151** (its 15-min difference: −0.19). All other 14 features are noise ⇒ the v1 nowcaster's entire signal is this disguised GOES channel.
- **Refutation attempts:** "the correlation is via real SoLEXS/HEL1OS physics" — the numerator is proven simulation (Claim 2), so the correlation can only come from the GOES denominator. "It's a small contribution" — a feature at |r| = 0.92 with the label-generating flux among 14 noise features is, necessarily, the model's dominant input; the detector's measured behaviour (fires on real flux exceedances; Experiment A's 94.2% C-overlap) matches a GOES-flux detector exactly.
- **Note on intent:** the GOES dependence is *declared in the class metadata* — a documented design decision (physically sensible had HEL1OS been real) whose consequence for the "Aditya-only" framing went unexamined. This is a framing/verification failure, not concealment.
- **Verdict: CONFIRMED.**

## Claim 6 — From-scratch reproduction yields the same conclusion

- **Evidence:** executed at the decisive scope: simulator regenerated from source → bit-identical to stored processed data (Claim 2) → recomputed feature matches training column (Claim 3). The chain mock-FITS → simulator → parquet → feature → model input is reproduced.
- **Verdict: CONFIRMED** at tested scope (three days bracketing the span + both instruments; full 915-day rebuild available but non-informative given bit-identity).

## Collateral verification — the GOES side is REAL (v1's GOES science stands)

The flare catalog contains the historic May 2024 storm sequence (X1.0 ×3 on May 8, X2.2/X1.1 May 9, X3.9 May 10, X5.8 May 11, **X8.7 on 2024-05-14 16:51**) matching the real solar record; `goes_full.parquet` peaks at **8.69×10⁻⁴ W/m² at exactly 2024-05-14 16:51** — the X8.7 flare, to the minute and the class decimal. Study A, the forecast-ceiling diagnostic, and the era-matched control retain their evidentiary basis.

## NEW FINDING — a genuine 21 GB ISSDC archive exists on disk, never used

`data_pipeline/downloads/raw/` holds **827 authentic ZIPs (21 GB)**: **431 SoLEXS daily L1 archives** (`AL1_SLX_L1_YYYYMMDD_v1.0.zip`) and ~396 **HEL1OS orbit-level L1 archives** (`HLS_*_lev1_V111.zip`, with `aux/hk.fits`, GTI tables, CZT pixel maps — authentic instrument packaging). Verified real: `AL1_SLX_L1_20240501` parses as compliant FITS, `TELESCOP='AL1'`, 86,400 rows at 1-s cadence, **with genuine data gaps (~21% NaN)** — real instruments have gaps; the simulator does not.

**Coverage (SoLEXS, by month):** dense 2024-02→2024-05 (118 days); near-empty 2024-06→2025-05 (5 days); dense 2025-06→2026-06 (~308 days). Total 431 of ~868 days in span; the major hole is **Jun 2024 – May 2025**.

**Implication:** the acquisition problem is roughly half-solved on disk. v1 downloaded real data and then never wired it into the model pipeline — the mock/simulator path (built for pipeline testing, per its own `--mock` flag and docstrings) became the de-facto source, undetected because astropy was absent so the FITS-parsing path *always* fell back to simulation.

## Recommendation

**A roadmap amendment is justified — every critical claim is confirmed.** Proposed **Phase 0.5 — Data Authenticity & Real-Archive Activation** (supersedes the T0 sketch, revised for the new finding):

1. **Inventory & extract** the 21 GB real archive (827 ZIPs → per-day L1 products; SHA manifest).
2. **Build real parsers** for SoLEXS `.lc/.pi/.gti` (per-SDD) and HEL1OS orbit products; validate against ≥3 hand-checked days including 2024-05-14 (the X8.7 day — the real SoLEXS response to the strongest flare in the archive is also the first physics sanity check).
3. **Quantify true coverage** and define the gap-fill acquisition request (Dec 2023–Jan 2024; Jun 2024–May 2025) — owner action via ISSDC/PRADAN; proceed on the ~431 real days meanwhile.
4. **Authenticity gate** added to the charter: no dataset enters any experiment without flare-catalog coincidence checks against an independent reference (the check that would have caught this in v1's first week).
5. **Quarantine** `data/aditya_l1/{raw,processed}` as SYNTHETIC by register; frozen v1 artifacts untouched.
6. **Correction memorandum** re-labelling v1 "Aditya" conclusions (GOES-side results explicitly re-affirmed per the collateral verification above).

Open items logged: provenance of the dataset `solexs_available` columns (non-material); HEL1OS orbit-file coverage profile (computed during 0.5.1).
