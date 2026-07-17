<!-- VERSION STATUS: CURRENT — BLOCKING Milestone V -->
<!-- REASON: Two §2.x parser-level rules falsified by real HEL1OS data. -->
<!-- DATE: 2026-07-17 -->

# CONTRADICTION-004 — two HEL1OS parser-level rules are falsified

**Status: BLOCKING Milestone V. Two frozen §2.x rules are impossible to satisfy against valid, uncorrupted archive data. No specification change made. Awaiting owner approval.**

Raised under: *"Do not pause implementation unless another parser-level contradiction is proven."* Two are proven. Unlike CONTRADICTION-003 (scientific interpretation, deferred), **both defects below are parser-correctness issues**: the parsers terminate on real data and cannot proceed.

**Milestone V status: 3 of 5 HEL1OS parsers pass on real data** — light curves (5 bands, 43,171 rows), GTI (1 interval, 43,178.29 s), events (5,796,441 events across all 4 detector HDUs). **Spectra and housekeeping are blocked.**

---

## DEFECT A — §2.7's rule R-1 enumerates the wrong hypotheses

### The rule
> **Resolution rule R-1:** at implementation, test the column against both hypotheses (Unix-s and MJD-days) and accept the one reproducing the header `TSTART/TSTOP` span to <1 s; if neither fits → **F-06, terminate**.

The parser did exactly this and terminated. Residuals: **5,271,868,808 s** (MJD-days hypothesis), **1,765,152,008 s** (Unix-seconds hypothesis). Neither is remotely close.

### What the column actually is (`OBSERVED`, `hel1os_czt_spectra_czt1.fits`)

| Quantity | Value |
|---|---|
| col `TSTART` | `[0.0, 20.0, 40.0, …, 43120.0]`, n=2157 |
| col `TSTOP[0]` | `20.0` |
| `EXPOSURE` | **uniform 20.0 s** |
| header `TSTART` / `TSTOP` | `61017.0000988685` / `61017.49963590554` **MJD** |
| header span | **43,160.0 s** |
| column span | **43,120.0 s** (= span − one 20 s bin at each end) |

**`TSTART` is seconds elapsed since the orbit start**, i.e. relative to the header `TSTART`. The first value is exactly `0.0`; the step is exactly `EXPOSURE`; the span matches the header to within one bin.

### Why the contract got it wrong

§2.7 framed the ambiguity as *"column declares unit='s' but header TSTART is MJD"* and concluded the **epoch** was undetermined. That framing was wrong. **The `unit='s'` declaration was correct all along** — the column really is seconds. The genuine unknown was never the *unit*, it was the **origin**. Both metadata statements are true and **compose**: absolute time = `mjd_to_utc(header TSTART) + column TSTART seconds`. R-1 offered two absolute-epoch hypotheses and omitted the relative one, which is the true one.

This is a **third instance of the same root cause** as CONTRADICTION-001 and -003: I asserted a relationship between two fields from their declared metadata without computing it. R-1 was written to guard exactly this class of error and still fell to it — because a hypothesis test can only find hypotheses you enumerate.

### Proposed amendment (NOT applied)
1. **§2.7 R-1** — add **H3 (relative seconds)** and test it **first**, since `unit='s'` literally declares seconds: accept H3 iff `col[0] == 0` (exactly) **and** `|col_span − header_span|` ≤ one `EXPOSURE` bin. Retain H1/H2 as fallbacks; terminate via F-06 only if **all three** fail.
2. **§2.7** — record the composition rule: *absolute time = `mjd_to_utc(header TSTART) + column TSTART`*; the column is an offset, never an epoch.
3. **§8** — new assumption **A-11**: the relative-seconds convention is VERIFIED on one orbit only. Milestone VIII must verify across all 391 HEL1OS orbits; deviation terminates validation.

---

## DEFECT B — §2.8's "mjd non-decreasing" is falsified

### The rule
> **Validation:** `mjd` non-decreasing; `czt1temp`/`czt2temp` finite; `suninfov ∈ {0,1}`.

### The data (`OBSERVED`, `aux/hk.fits`, orbit `HLS_20251208_000008`)

| Quantity | Value |
|---|---|
| Rows | 9,514 |
| **Decreasing steps** | **424** (4.5 % of 9,513 steps) |
| Zero steps (duplicates) | **0** |
| All values unique | **True** |
| First decrease (row 925) | `61017.024131` → `61017.024131`, **Δ = −0.013 s** |
| Global range | `61017.000099` → `61017.499848` — correct, and within the header span |

The backward steps are **~13 milliseconds**. Every timestamp is unique, the global span is right, and the ordering is otherwise correct. This is **sub-second telemetry packet-arrival jitter**, not corruption: housekeeping packets are written in arrival order, which is not exactly time order.

`INFERRED`: `mjd` is a *measurement*, not an *index*. The contract assumed it was sorted; the archive stores it as recorded.

### Why this matters
`suninfov`, the pile-up counters, the saturation counters and the HV monitors all live in this table — it is Phase 1a's only source of instrument state. Terminating on 13 ms of jitter would make HEL1OS housekeeping **unparseable archive-wide**.

### Proposed amendment (NOT applied)
1. **§2.8 validation** — replace *"`mjd` non-decreasing"* with: *`mjd` MUST be finite and **unique**; the global span MUST lie within the header `TSTART`/`TSTOP`. Raw arrival order is **not** required to be sorted.*
2. **§2.8 parser behaviour** — the HK table is returned **stably sorted by `mjd`**, and the provenance MUST record `n_out_of_order` and `max_backward_step_s`. **This is a reordering, not a repair**: no value is created, altered, imputed or dropped, and the transformation is recorded rather than silent. *(Flagged explicitly for the owner: this is the first transformation any v2 parser performs. The alternative — return unsorted and push the problem to M-VII — is defensible; I do not think it is better, because an unsorted time series is a footgun for every downstream consumer, but the choice is the owner's.)*
3. **No threshold is proposed.** The magnitude of the jitter is **reported**, never compared against an invented tolerance. Encoding "13 ms is acceptable" would repeat the error the owner correctly rejected in CONTRADICTION-003.
4. **§8** — new assumption **A-12**: HK time jitter is characterised on one orbit only; Milestone VIII must report the distribution of `max_backward_step_s` across all 391 orbits. A **drifting or growing** jitter is a scientific finding.

---

## State of the work

Milestone V is **paused with the code committed and both parsers terminating exactly as the frozen contract requires**. Nothing has been weakened: R-1 still enumerates only two hypotheses; §2.8 still demands non-decreasing `mjd`. The three passing parsers (LC, GTI, events) are unaffected and their tests are not yet written — Milestone V's test suite and compliance report follow once these two rules are resolved.

**Awaiting approval of the two amendments above.**
