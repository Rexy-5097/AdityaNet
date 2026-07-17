<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone III specification-compliance report against amended contract r2. -->
<!-- DATE: 2026-07-17 -->

# Milestone III — Specification Compliance Report

**Verdict: COMPLIANT, ZERO DEVIATIONS. 63/63 tests pass, 0 xfail, 0 skip. CONTRADICTION-002 CLOSED. Milestone IV authorised.**

Contract: `PARSER_SPECIFICATION.md` **r2** (owner-approved 2026-07-17). Implementation: `app/v2/parsers/solexs_lc.py`.

---

## 1. Amendment r2 applied — all 5 approved changes

| # | Approved change | Where | Verified |
|---|---|---|---|
| 1 | §2.1 missing-value description replaced (NaN is the sentinel; zero is a valid count) | spec §2.1 | ✅ old clause gone; new text verbatim |
| 2 | Parser behaviour: pass through / never impute / never zero / never remove | `solexs_lc.py`; **no** `fillna`/`nan_to_num`/`dropna` anywhere | ✅ `test_nan_counts_are_the_missing_data_sentinel_not_an_error` — 3 NaN in, 3 NaN out, 86400 rows retained |
| 3 | REQUIRED cross-product rule: `NaN(COUNTS)` == GTI-excluded, mismatch → F-09 | spec §2.1 + §7 table; enforced at day-assembly (M-VII) since it needs `.lc`+`.gti` | ✅ `test_real_20240514_nan_positions_equal_gti_excluded_seconds` |
| 4 | Aggregation contract: finite-only; one NaN never voids a minute; empty → `NaN`+`q_no_data` | spec §3 (T1/T2 columns updated) | ✅ contract recorded; **binding on M-VII** |
| 5 | Scope VERIFIED-on-reference-only; M-VIII verifies all 436, terminates on violation | spec §8 **A-9** | ✅ recorded; **carried as an M-VIII obligation** |

## 2. Behaviour-by-behaviour compliance (§2.1)

| Contract clause | Implementation | Test |
|---|---|---|
| HDU1 `RATE` by name | `get_hdu(hdul,"RATE")` | `test_F02_missing_rate_hdu_terminates`, `test_F02_hdu_renamed_terminates` |
| `TIME`/`COUNTS` columns, case-insensitive | `get_column` | `test_F04_missing_counts_column_terminates` |
| Semantics from `HDUCLAS3`, **never** `EXTNAME` | explicit `HDUCLAS3=='COUNTS'` gate → F-07 | `test_F07_hduclas3_not_counts_terminates` |
| `MJDREFI==40587`, `MJDREFF==0`, `TIMESYS=UTC`, `TIMEUNIT=s`, `TIMZERO==0` | five F-05 gates | 5 × `test_F05_*` |
| `TIMEDEL==1` | F-07 | `test_F07_timedel_not_one_terminates` |
| `NAXIS2==86400` | F-17 | `test_F17_wrong_row_count_terminates` |
| `TIME` finite, strictly increasing, Δ==1 s | F-16 ×3 | `test_F16_nonfinite_time…`, `…not_increasing…`, `…time_gap…` |
| `TSTART==TIME[0]`, `TSTOP==TIME[-1]`, day-bounds | F-06 | `test_F06_tstart_mismatch…`, `test_F06_mjd_epoch_data…` |
| `FILTER` matches SDD dir; `OBS_DATE` matches filename; `INSTRUME` | F-07 ×3 | 3 × `test_F07_*` |
| **`COUNTS` finiteness NOT validated (r2)** | no finiteness check on counts | `test_nan_counts_are_the_missing_data_sentinel_not_an_error` |
| F-19 negative counts only, NaN-safe | `np.any(counts < 0)` | `test_F19_negative_counts_terminate` |
| No simulation fallback | `open_fits` → F-01 | `test_F01_corrupt_terminates_never_simulates` |
| F-18 allowlist + `._*` | filename regex + guard | `test_F18_bad_filename_rejected` |

## 3. Falsification pass

Automated checks, all **PASS**:
- **NaN passes through**: no `fillna`, no `nan_to_num`, no `dropna` in the parser.
- **`COUNTS` finiteness not validated** (r2): the invented check is gone.
- **`TIME` finiteness → F-16**: retained where it belongs.
- **F-19 negative-only, NaN-safe**: `NaN < 0` is `False`, so no guard is needed.
- **Semantics from `HDUCLAS3`**: enforced.
- **No `header.get` defaults** anywhere in the parser — the v1 defect stays unrepresentable.
- **Rule-set integrity**: spec table 20 ≡ code 20; 0 missing, 0 invented. r2 added an *application* of F-09, not a new rule.

## 4. Superseded notes removed (required action 4)

All in-code references to `CONTRADICTION-002` deleted; the code now cites the contract clause (**§2.1 r2**) instead. Grep for `CONTRADICTION-002` under `app/v2/` and `tests/v2/` returns **nothing**. Rationale: a contradiction document is a *transient negotiation artifact*; once the contract absorbs it, the code must point at the contract, or the contract stops being the single source of truth.

## 5. Deviations from the amended contract

**None.**

## 6. Findings carried forward

1. **M-VII owes two contractual behaviours**: the NaN⟺GTI cross-product check (F-09) and finite-only aggregation. Both are now written into §2.1/§3 rather than living in my head.
2. **M-VIII owes two archive-wide proofs**: A-8 (`Σ(STOP−START+1) == EXPOSURE`, 436 archives) and A-9 (NaN⟺GTI bijection, 436 archives). Either violation TERMINATES validation as a scientific finding.
3. **r1 is now doubly confirmed.** The NaN evidence is an *independent* line: under the exclusive convention GTI would exclude ~10 s and could never match the 5 NaNs. Two different files, two different fields, one conclusion.

## 7. Statistics

M-I 13 + M-II 19 + M-III 31 = **63 passed, 0 failed, 0 xfail, 0 skip** (13.8 s). Real-archive coverage: 2024-05-14 SDD2 `.lc` (86,400 rows, 5 NaN, 86,395 finite == EXPOSURE) and `.gti` (5 intervals, 86,395 s exact); SDD1 `.gti` (empty → F-12).
