<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone VIII scientific findings. Evidence-supported only. -->
<!-- DATE: 2026-07-18 -->

# Scientific Findings — AdityaNet v2, Phase 0.5

**Evidence-supported findings only.** No speculation, no model discussion, no feature engineering. Every statement below is backed by an archive-wide measurement recorded in `scientific_validation.json` and reproduced identically on two independent runs. Findings are labelled `OBSERVED` (measured directly) or `LOGICALLY IMPLIED` (follows necessarily from measurements).

---

## F-1 — The SoLEXS light curve is a band-limited integration of the PI spectrum

`OBSERVED` (12 temporally-spread days, per-second, ~1.03 M second-samples):
- Σ(340 PI channels) exceeds the `.lc` value on **~100 % of seconds, on every day sampled**.
- The ratio Σ(PI)/LC has median **4.08** and varies across days from **1.76 to 20.4**.
- **No** full-sum exact match occurs.
- The best contiguous PI sub-band reproducing the LC is **stable near channels 40–60** (8/12 days 40–60; 3/12 40–68; 1/12 40–76).

`LOGICALLY IMPLIED`: the light curve is **not** the total-channel sum, **not** an independent product, and **not** a fixed rescaling of the spectrum. A stable contiguous sub-band reproduces it far better than the total, and the total/LC ratio is spectrally variable rather than constant. The light curve is a **band-limited integration over a sub-band of the PI spectrum**.

**Bound on the finding:** the exact band edges are **not recoverable**. The light-curve band is defined in **energy**; PI channels are **ordinal indices**; and **no RMF/ARF exists anywhere in the archive** to map between them. The finding is therefore band-limited-integration with an empirical band of ≈ channels 40–60, not an exact channel specification.

**Consequence already in force:** T1 (`counts_total`, from the light curve) and T2 (`counts`, 340 channels) are carried **independently** in the canonical dataset; neither is derived from the other. This finding confirms that decision was necessary — deriving one from the other would have been quantitatively wrong by a factor that varies from 1.76 to 20.4.

*(This resolves CONTRADICTION-003, open since Milestone IV.)*

## F-2 — The SoLEXS GTI excludes substantially more time than data is absent

`OBSERVED` (414 days): every NaN second is GTI-excluded (**414/414 days**, no exception), but the converse fails on **70 of 414 days**. The excess — seconds marked GTI-excluded that nevertheless carry a **finite count** — totals **266,919 s**, with a per-day maximum of **43,199 s** (~12 h).

`OBSERVED` temporal structure: the excess is **strongly non-uniform**. ~156,000 s (58 %) falls in the Feb–May 2024 block; a single day in Dec 2024 contributes 43,199 s; Feb 2026 contributes 38,409 s. The **top 10 days account for 80.2 %** of all excess. No day shows a full-day (≥ 80,000 s) excess.

`OBSERVED` detector structure: **not measurable** — SoLEXS science products exist only for SDD2 (SDD1 supplies GTI only and is F-12 inactive archive-wide), so no per-detector contrast exists.

**No mechanism is asserted.** The measurement establishes that GTI exclusion in the SoLEXS archive encodes something beyond simple data absence, and that this something is concentrated in specific periods. What it encodes is not determined by this evidence.

**Consequence already in force:** the canonical invariant is the one-directional implication `NaN(COUNTS) ⇒ GTI-excluded` (spec r5), not the set equality originally assumed. `live_time_s` (from GTI) and `n_seconds_present` (from finite counts) are carried independently in T1.

## F-3 — HEL1OS housekeeping timestamps are telemetry-ordered, not chronologically sorted

`OBSERVED` (389 orbits): **112 orbits (29 %)** contain at least one backward step in the housekeeping `mjd` series; **63,166** inversions in total; the per-orbit inversion count reaches **31,436**.

`OBSERVED` magnitude distribution: **388 of 389 orbits** have a maximum backward step **< 1 s**. The orbits with the *highest inversion counts* (31,436 / 3,532 / 1,934) all have maximum backward steps **< 0.9 s**.

`LOGICALLY IMPLIED`: many small out-of-order steps, bounded below one second, is the signature of records written in **telemetry arrival order** rather than timestamp order. This is consistent with the archive's own framing of housekeeping `mjd` as a measurement rather than an index.

**Exactly one orbit differs in character:** `HLS_20260617_121028` contains a **single** backward step of **1153.4 s** (~19 min) among 5,548 rows — isolated and three orders of magnitude larger than the jitter population. It is recorded as a distinct archive-level anomaly, not as jitter.

`LOGICALLY IMPLIED` (parser excluded): the v2 parser preserves archive order losslessly and performs no sorting — a property asserted by test. Every inversion therefore exists in the archived data and is not introduced by processing.

## F-4 — HEL1OS carries two detector families with different, non-interchangeable spectral channel spaces

`OBSERVED` (all 1,564 spectra products across 389 orbits): **CZT detectors have 341 PHA channels** (782 products) and **CdTe detectors have 511 PHA channels** (782 products). Zero products deviate.

`LOGICALLY IMPLIED`: the Aditya-L1 X-ray archive contains **three mutually incommensurable spectral channel spaces** — SoLEXS PI (340), HEL1OS CZT PHA (341), HEL1OS CdTe PHA (511). None may be merged with another; a channel index has no meaning outside its own family, and no response matrix exists to relate them.

## F-5 — The HEL1OS spectra time column is an offset, not an epoch

`OBSERVED` (1,564 spectra products, 100 %): the `TSTART` column resolves as **seconds elapsed since the file's header `TSTART`**, with a residual against the header span of exactly one `EXPOSURE` bin on every product. No product resolves as MJD-days or Unix-seconds.

`LOGICALLY IMPLIED`: absolute time for HEL1OS spectra is the **composition** `mjd_to_utc(header TSTART) + column TSTART`. The column's declared unit (seconds) and the header's units (MJD) are both correct and describe different quantities — an offset and an origin respectively.

## F-6 — The SoLEXS good-time exposure identity is exact and universal

`OBSERVED` (414 parseable archives): `Σ(STOP − START + 1) == EXPOSURE` holds **exactly** — zero failures, no day requiring any tolerance. GTI interval endpoints are **inclusive** at 1-second sampling.

`LOGICALLY IMPLIED`: SoLEXS GTI live time is computed as `STOP − START + 1` per interval. An exclusive reading understates live time by exactly one second per interval.

## F-7 — First verified Aditya-L1 solar observation in this project

`OBSERVED`: on 2024-05-14, the canonical T1 SoLEXS count rate peaks at **16:49 UTC**. The GOES-catalogued X8.7 flare of that day peaked at **16:51 UTC** — a 2-minute agreement, within the acceptance window frozen before the measurement was made.

`LOGICALLY IMPLIED`: the canonical pipeline reads genuine solar X-ray signal from the real Aditya-L1 archive, independently corroborated by an unrelated instrument. This is the first such verified observation in the project's history; all prior "Aditya" results were derived from synthetic data.

---

## Findings register

| ID | Finding | Status |
|---|---|---|
| F-1 | LC is a band-limited integration of the PI spectrum (band ≈ ch. 40–60; exact edges need the RMF) | Established; resolves CONTRADICTION-003 |
| F-2 | GTI excludes more time than data is absent; temporally concentrated; mechanism unknown | Established (observation); mechanism open |
| F-3 | HK timestamps are telemetry-ordered (sub-second jitter); one orbit has an isolated 1153 s jump | Established |
| F-4 | Three incommensurable channel spaces (340 PI / 341 CZT PHA / 511 CdTe PHA) | Established |
| F-5 | HEL1OS spectra time column is an offset from the header origin | Established |
| F-6 | GTI exposure identity is exact with inclusive endpoints | Established |
| F-7 | Verified solar signal: T1 peak 16:49 UTC vs GOES X8.7 at 16:51 UTC | Established |

**Open questions carried forward (evidence insufficient, no speculation offered):** the physical meaning of the GTI-exclusion excess (F-2); the exact energy band of the SoLEXS light curve (F-1), which requires an instrument response file not present in the archive.
