<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone II specification-compliance report against amended contract r1. -->
<!-- DATE: 2026-07-17 -->

# Milestone II — Specification Compliance Report

**Verdict: COMPLIANT. 32/32 tests pass, 0 xfail, 0 skip. CONTRADICTION-001 CLOSED. Milestone II complete; Milestone III authorised.**

Contract: `PARSER_SPECIFICATION.md` **r1** (amended, owner-approved 2026-07-17). Implementation: `app/v2/parsers/solexs_gti.py`, `app/v2/utils/fitsio.py`.

---

## 1. Amendment applied — all 5 approved changes

| # | Approved change | Where | Verified |
|---|---|---|---|
| 1 | §2.3 inclusive convention `live_time = STOP−START+1` | spec §2.3; `GTI_INCLUSIVE_S=1.0`; `duration_s = stop−start+1` | ✅ `test_parses_valid_gti` asserts `duration_s == [5.0, 11.0]` |
| 2 | F-09 → `Σ(STOP−START+1)` | spec §5 table; `summed = Σ(stop−start+1)` | ✅ |
| 3 | F-09 exact equality, no tolerance | `if summed != exposure` — `EXPOSURE_TOL_S` **deleted** | ✅ `test_F09_is_now_exact_no_tolerance` (10.0/12.0/11.5 all terminate) |
| 4 | §6 D1 measured excluded-seconds | spec §6 D1 | ✅ `test_real_..._excluded_seconds_match_amended_spec` |
| 5 | Convention VERIFIED-for-target, **not** universal; Milestone VIII must check all 436 and terminate on deviation | spec §2.3 scope para + §8 **A-8** | ✅ recorded; **carried as a Milestone VIII obligation** |

## 2. Behaviour-by-behaviour compliance

| Contract clause | Implementation | Test |
|---|---|---|
| §2.3 HDU1 `GTI` by name | `get_hdu(hdul,"GTI")` | `test_F02_missing_gti_hdu_terminates` |
| §2.3 `START`/`STOP` columns, case-insensitive | `get_column` | `test_F04_missing_column_terminates` |
| §2.3 Unix-second epoch, within `OBS_DATE` day | day-bounds check → F-06 | `test_F06_wrong_epoch_terminates` |
| §2.3 `EXPOSURE` is a **string** → parse explicitly | `float(str(exp_raw).strip())`, F-07 on failure | real-file test (`'86395.0'`) |
| §2.3 `START<STOP` | F-19 | `test_F19_stop_before_start_terminates` |
| §2.3 sorted, non-overlapping | F-16 | `test_F16_unsorted…`, `test_F16_overlapping…` |
| §2.3 `Σ(STOP−START+1)==EXPOSURE` exact | F-09 | `test_F09_exposure_mismatch…`, `…_is_now_exact…`, `…_exclusive_convention_would_now_be_rejected` |
| §2.3 `NAXIS2==0` legal → inactive | F-12; empty typed frame, `detector_active=False` | `test_F12_empty_gti_is_legal_not_fatal`, real SDD1 |
| §2.1 `INSTRUME`/`OBS_DATE` cross-checks | F-07 | `test_F07_wrong_instrument`, `test_F07_obs_date_disagrees…` |
| §5 F-01 no simulation fallback | `open_fits` re-raises as F-01 | `test_F01_corrupt_file_terminates_never_simulates` |
| §5 F-18 allowlist + `._*` | filename regex + `_reject_appledouble` | `test_F18_bad_filename_rejected`, `test_F18_appledouble_rejected` |
| §3 T7 provenance | `Provenance` on every return | `test_provenance_row_has_every_T7_field` |

## 3. Falsification pass

- **Old tolerance fully eradicated:** grep for `EXPOSURE_TOL_S` / `approx(86395` / `abs=1.0` → **no hits**. The amendment could not have been faked by loosening a test.
- **Regression guard installed:** `test_F09_exclusive_convention_would_now_be_rejected` feeds an `EXPOSURE` computed the *old* way (14.0) and asserts termination with `got == 16.0`. If anyone reverts to the exclusive convention, this fails loudly.
- **Rule set integrity:** spec table 20 rules ≡ code 20 rules; 0 missing, 0 invented.
- **No simulation path in `app/v2/`:** every match for `simulat|mock|synthetic|fallback|np.random` is a prohibition comment, never executable code.
- **xfail removed, not suppressed:** the D1 test now passes on its merits; `strict=True` had guaranteed this could not be quietly left behind.

## 4. Deviations from the amended contract

**None.**

## 5. Findings recorded during this milestone

1. **Validation ordering is contractual, not incidental.** F-09 (`EXPOSURE` consistency) is evaluated **before** the F-06 day-bounds check, exactly as §2.3 lists them. A test fixture with an inconsistent `EXPOSURE` therefore trips F-09 and never reaches F-06 — this surfaced as a fixture defect and is now documented in the test itself.
2. **Exact float equality is safe here — for a reason, not by luck.** Real `START`/`STOP` are whole seconds stored as doubles (|values| ≈ 1.7e9 ≪ 2⁵³), so `Σ(stop−start+1)` is exact, and `EXPOSURE` parses from a string to an exact float. Were a future archive to carry fractional boundaries, exact equality would terminate — which is the **designed** behaviour under A-8: that is a scientific finding to report, not an error to absorb.

## 6. Statistics

Milestone I 13 tests + Milestone II 19 tests = **32 passed, 0 failed, 0 xfail, 0 skip** (0.6 s). Real-archive coverage: 2024-05-14 SDD2 (5 intervals, 86395 s exact) and SDD1 (empty → F-12).
