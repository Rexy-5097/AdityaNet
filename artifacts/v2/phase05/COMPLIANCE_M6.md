<!-- VERSION STATUS: CURRENT -->
<!-- REASON: Milestone VI specification-compliance report (Version Resolution Engine, §4). -->
<!-- DATE: 2026-07-17 -->

# Milestone VI — Specification Compliance Report

**Verdict: COMPLIANT, ZERO DEVIATIONS. 154/154 tests pass (30 new), 0 xfail, 0 skip. No contradiction raised. Milestone VII authorised.**

Contract: `PARSER_SPECIFICATION.md` §4. Implementation: `app/v2/resolution/version_engine.py`. **The parser layer was not touched** — the engine imports nothing from `app.v2.parsers` (verified).

---

## 1. Archive-wide result (real data, all 391 orbits)

| Metric | Value |
|---|---|
| Candidates | **391 orbits** |
| Owned `(minute, detector)` pairs | **1,065,572** |
| Conflicting pairs resolved | **48,604** |
| Distinct conflicts | **256** |
| Rules invoked | **R1_higher_version: 47,328** · **R2_longer_duration: 1,276** |
| R3 (processing date) invoked | **0** |
| R4 / F-14 terminations | **0** |
| Unique-ownership invariant | **HOLDS** |

Log: `artifacts/v2/phase05/version_resolution_log.json`.

## 2. Scope items

| # | Required | Implementation | Verified |
|---|---|---|---|
| 1 | Minute-level coverage map; single authoritative representation of ownership | `CoverageMap`; `build_coverage_map()` | ✅ 1,065,572 pairs; `assert_unique_ownership()` |
| 2 | Deterministic precedence: version → duration → processing-date → fail | `_compare()`, order frozen in `PRECEDENCE_ORDER` | ✅ 11 precedence tests incl. rule-inversion attempts |
| 3 | Each (minute, detector) has exactly one owner; no duplicate; no implicit overwrite | two-phase build (collect → resolve) | ✅ order-independence proven on synthetic **and** real data (3 shuffles) |
| 4 | `version_resolution_log.json` with winner, rejected candidates, rule invoked, timestamps affected, provenance hashes | `resolution_log()` / `write_resolution_log()` | ✅ every field asserted by `test_resolution_log_has_every_required_field` |
| 5 | Class A + Class B demonstrated; duplicate-minute impossible; F-15 unbypassable | dedicated tests | ✅ §3 below |

## 3. Class A and Class B

**Class A** (identical interval, different version — the real `HLS_20251208_000008_43178sec` V111/V211 pair): V211 wins **every** minute via R1.

**Class B** (partial overlap — the real `20251207_120003_43195sec_V211` vs `121028_42570sec_V111`): each file keeps its **exclusive** minutes and precedence decides only the **contested** ones. The test asserts that the *lower-version* file `late_V111` still owns its exclusive region — **a file-level winner would have destroyed those minutes outright.** This is the concrete reason §4 mandates a per-minute map rather than file-level selection.

## 4. Falsification pass

**"Selects provenance. Nothing else."** — verified by AST analysis of executable code (docstrings stripped, so prose cannot produce a false pass):

- never interpolates · never averages · never merges values · never fills/imputes · never writes measurements — **all PASS**
- **no measurement attribute is referenced anywhere** (`counts`, `ctr`, `stat_err`, `ener`, `rate`, `spectra`): the engine operates purely on orbit metadata, so averaging competing files is not merely forbidden but **structurally impossible — the engine never holds a measurement.**
- `select_owned_rows()` filters by ownership and every surviving value is asserted byte-identical to its input.

**No implicit overwrite** — the build is deliberately two-phase (collect all claims → resolve). A single-pass "assign as you go" loop would silently implement last-write-wins, which §4 forbids. Order-independence is proven, not asserted: identical maps from shuffled candidate orders, on synthetic and real archive data.

**F-15 unbypassable** — `assert_no_duplicate_minutes()` is the last line of defence and catches duplicates even when the coverage map is bypassed entirely, including sub-minute duplicates after flooring (two samples 50 s apart in the same minute) and detector-aware cases (same minute + different detectors is legal; same detector is not).

**Naive ingestion impossible** — `coverage_map` is a required keyword argument of `select_owned_rows()`; passing a non-`CoverageMap` terminates with F-14. There is no v2 API that concatenates orbit files directly.

## 5. Finding: precedence rule 3 has no data source (recorded, not a contradiction)

`OBSERVED`: **HEL1OS primary headers contain no `DATE` keyword** (they carry `MISSION, INSTRUME, TELESCOP, CREATOR, POC, ENTITY, MJDSTART, MJDSTOP, ISOSTART, ISOSTOP, SUNRA…, L1VER, L1REL, CHECKSUM, DATASUM`). Rule 3 therefore cannot fire on this archive.

**This is not a contradiction**, because §4 already prescribes the outcome: if version and duration tie and no later processing date can be established, **F-14 terminates — never a coin-flip.** The rule is implemented faithfully and tested (`test_R4_fires_when_processing_date_absent__the_real_hel1os_case`), and retained because a reprocessed product could add `DATE`.

`OBSERVED`: rule 3 is also **unreachable** in the current archive — of 49 time-overlapping orbit pairs, **0** tie on both version and duration. Every conflict resolves at R1 or R2, which the archive-wide run confirms (47,328 + 1,276 = 48,604, R3 = 0).

`OBSERVED`, supporting §4's A-1 ("version digits are opaque"): `L1VER='0.1'` and `L1REL='20230815'` are **identical** across the V111/V211 Class-A pair, so the filename version digits are not reflected in any header. Their semantics remain undocumented, and the engine treats them as an opaque ordinal exactly as the contract directs.

## 6. Deviations

**None.**

## 7. Statistics

M-I 13 + M-II 19 + M-III 31 + M-IV 30 + M-V 31 + M-VI 30 = **154 passed, 0 failed, 0 xfail, 0 skip** (19.2 s).
