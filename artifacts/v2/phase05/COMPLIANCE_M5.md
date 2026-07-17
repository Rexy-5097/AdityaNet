<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone V specification-compliance report against amended contract r4. -->
<!-- DATE: 2026-07-17 -->

# Milestone V — Specification Compliance Report

**Verdict: COMPLIANT, ZERO DEVIATIONS. 124/124 tests pass, 0 xfail, 0 skip. CONTRADICTION-004 CLOSED. Milestone VI authorised.**

Contract: `PARSER_SPECIFICATION.md` **r4**. Implementation: `app/v2/parsers/hel1os.py`, `hel1os_base.py`, `app/v2/utils/timeseries.py`.

---

## 1. Amendment r4 applied

| Defect | Ruling | Where | Verified |
|---|---|---|---|
| **A** — R-1 omitted H3 | **APPROVED in full** | `resolve_epoch_R1`, order H3→H1→H2 | ✅ real data resolves `relative_seconds` on 6/6 sampled orbits, residual exactly one 20 s bin |
| A — H1/H2 retained | APPROVED | both branches live | ✅ `test_R1_H1_…`, `test_R1_H2_…` |
| A — composition rule | APPROVED | `absolute_time_from_R1` | ✅ `test_R1_composition_rule…` |
| A — A-11 recorded | APPROVED | spec §8 | ✅ M-VIII obligation |
| **B** — validation contract | **APPROVED** | finite + unique + header-span + inversion stats | ✅ `test_real_hk_records_inversion_statistics…` |
| B — strict non-decreasing | **REMOVED** | — | ✅ real HK (424 inversions) now parses |
| B — **do NOT auto-sort** | **DECLINED my proposal** | parser has no sort | ✅ `test_real_hk_preserves_archive_order__r4_lossless` asserts the output is **not** monotonic |
| B — `chronological_sort()` outside parser | APPROVED | `app/v2/utils/timeseries.py` | ✅ 5 tests: every row, every value, deterministic, provenance, F-04 |
| B — A-12 recorded | APPROVED | spec §8 | ✅ M-VIII obligation |

## 2. Parser family (§2.5–§2.9)

| Product | Contract | Real-data result |
|---|---|---|
| Light curves §2.6 | 5 band HDUs, edges from EXTNAME + allowlist, `CTR` declared `cts/sec` | ✅ CZT & CdTe band sets distinct; 43,171 rows |
| GTI §2.9 | lowercase `tstart`/`tstop`; no `EXPOSURE` → SoLEXS F-09 identity N/A | ✅ 1 interval, 43,178.29 s |
| Housekeeping §2.8 | finite/unique/span; stats recorded; **archive order preserved** | ✅ 9,514 rows, 424 inversions, max 892.4 ms |
| Spectra §2.7 | 341 **PHA** (F-11), Type II, F-08 constant CHANNEL, R-1 | ✅ (2157, 341), `relative_seconds` |
| Events §2.5 | all 4 detector HDUs (F-03), `ener` in keV, **not ingested** | ✅ 5,796,441 events; `rows_out=0` |

## 3. Falsification pass

- **Parser does not sort**: the HK test asserts `not t.is_monotonic_increasing` — the lossless claim is *proven by the data*, not asserted in a comment.
- **`chronological_sort` is lossless**: row count and column list are asserted post-condition (F-20), not documented.
- **No threshold anywhere**: no "acceptable jitter" constant exists; `inversion_stats` returns statistics and compares nothing.
- **PI/PHA never conflated**: SoLEXS enforces 340/PI, HEL1OS enforces 341/PHA; each terminates on the other's numbers.
- **Band allowlist**: an unknown band terminates rather than being mislabelled.
- **Rules**: spec table 20 ≡ code 20; 0 missing, 0 invented. r4 added no rule ids.

## 4. Deviations

**None.**

## 5. Findings carried forward

1. **A-11 / A-12** are M-VIII obligations across all 391 orbits (with A-8/A-9 across 436 SoLEXS archives).
2. **The lossless-parser principle** (r4 §2.8) now applies to all v2 parsers, not just HEL1OS.
3. **CONTRADICTION-003** remains OPEN (Scientific Validation, M-VIII).

## 6. Statistics

M-I 13 + M-II 19 + M-III 31 + M-IV 30 + M-V 31 = **124 passed, 0 failed, 0 xfail, 0 skip** (18.8 s).
