# Verification & Validation Master Plan v1.0

**Authority:** Architecture Freeze v1.0 · Engineering Plan v1.0 · TIS v1.0 — all frozen, none modified by this document.
**Role:** Independent Verification & Validation. The implementing team is assumed to be a different team.
**Mandate:** demonstrate conformance. Never redesign.

> Where the architecture does not expose enough evidence to verify a requirement, this plan
> says so explicitly and marks the requirement **UNVERIFIABLE**. IV&V does not close a gap
> by inventing a method.

---

## PART 1 — Verification philosophy

Four distinct activities. Conflating them is the most common way conformance work becomes theatre.

| Activity | Question | Authority | Failure means |
|---|---|---|---|
| **Verification** | Was the system built *to the frozen specification*? | Architecture Freeze v1.0, TIS v1.0 | Implementation deviates. Fix the implementation |
| **Validation** | Was the *right* system specified? | ADR-0001 (product constitution) | The product is wrong. Requires an ADR — outside IV&V authority |
| **Scientific validation** | Are the published scientific claims *true and reproducible*? | Frozen protocols, limitation clauses L-1…L-11 | A claim is unsupported. Retract per ADR-0024 |
| **Engineering validation** | Does the system behave correctly under *real inputs and real failure*? | Failure taxonomy TIS §0.2, gates TIS §16.5 | Behaviour diverges from spec under load or corruption |

**Standing rules for this plan.**

1. IV&V may fail a build. IV&V may not change a requirement.
2. A requirement verified only by "the author says so" is **not verified**.
3. Absence of a failing test is not evidence. Every gate must have a *deliberate-violation* test proving it fails when it should (TIS E14 §11) — otherwise a passing gate is indistinguishable from a gate that did not run.
4. Negative results and limitations are verification targets, not disclaimers.

---

## PART 2 — Requirements Traceability Matrix

Methods: **INSP** inspection · **STAT** static analysis · **ARCH** architecture test · **UNIT** · **PROP** property · **INTG** integration · **E2E** · **BENCH** scientific benchmark · **MAN** manual review · **FORM** formal reasoning.

### 2.1 Active ADRs

| ADR | Requirement | Method | Verification artifact |
|---|---|---|---|
| 0001 | Product scope; non-goals honoured | INSP, MAN | Lexicon gate report; non-goal audit checklist |
| 0002 | Ubiquitous language; `Method` not `Model` | STAT, MAN | Identifier scan; glossary review |
| 0003 | Source distinct from Instrument | ARCH, UNIT | Type separation test; adapter registration test |
| 0004 | Observations bitemporal | PROP, INTG | "both times present" property; dual-write integration |
| 0005 | Content addressing for immutables | PROP, UNIT | Digest stability property; ID-format gate |
| 0006 | Dataset releases immutable | INTG, PROP | Re-freeze rejected; byte-immutability property |
| 0007 | Ground truth separate & versioned | ARCH, INTG | Context import test; revision → two releases |
| 0008 | Protocols immutable, pre-registered | INTG, INSP | Mutation rejected; prose-migration review |
| 0010 | Method releases immutable, retrievable | INTG, PROP | Retrieve-and-reproduce property |
| 0011 | Instrument declaration gate | INTG | **v1 regression test** (GOES-declaring method rejected) |
| 0012 | Evidence binding + consistency gate | INTG, ARCH | Drift fails build; literal-in-template fails |
| 0013 | Limitations versioned, cited by ID | STAT, INSP | Citation-resolution gate; single-copy audit |
| 0014 | Batch, single-node | INSP, ARCH | Dependency scan for broker/orchestrator imports |
| 0015 | Static publication; live isolated | INTG | Byte-budget gate; deploy-topology review |
| 0016 | Sandboxed method execution | **PARTIAL** | Wire-format conformance only. **Isolation UNVERIFIABLE — see §10.2** |
| 0017 | No imputation | PROP, STAT | No-imputation property; `fillna`/`interpolate` ban |
| 0019 | Monorepo; contracts sole vocabulary | ARCH | Cross-context import test |
| 0020 | Gates fail closed | INTG, INSP | No-path-filter test; per-gate violation tests |
| 0021 | Environment as fifth pinned input | PROP, INTG | Identical-five → identical-scores; env digest → new identity. **EQUIVALENT class PARTIAL — §10.2** |
| 0022 | Unknown ingest_time is NULL | PROP, INTG | No-backfill property; both protocol modes |
| 0023 | Three storage tiers; raw referenced | INTG, INSP | Deposit digest match; Tier 0 non-redistribution gate. **Durability INSP only — §10.2** |
| 0024 | Bytes immutable; standing is not | PROP, INTG | No-mutation property; retraction-3-hops fails build |
| 0025 | Free seams vs paid abstractions | MAN | ADR review checklist at each boundary change |
| 0026 | Six contexts + one shared kernel | ARCH | Kernel-zero-imports; six import-direction tests |
| 0027 | Bitemporal migration procedure | INTG, INSP | Divergence report; rollback rehearsal evidence |

### 2.2 Engineering standards

| STD | Requirement | Method |
|---|---|---|
| 01 | Dependency direction | ARCH |
| 02 | Content addressing | PROP |
| 03 | Bitemporality; NULL semantics | PROP |
| 04 | Missing never imputed | PROP, STAT |
| 05 | No bare numbers in publication | STAT (template gate) |
| 06 | Evidence consistency | INTG |
| 07 | Gates fail closed | INTG |
| 08 | *(superseded by ADR-0021)* | — |
| 09 | Additive schema evolution | STAT (contract diff gate) |
| 10 | Releases immutable | INTG |
| 11 | Abstraction requires two instances | MAN |
| 12 | Tests run without proprietary data; guards check files | INTG (clean-export) |
| 13 | Errors fail loud | STAT (bare-except ban), UNIT |
| 14 | Structured logs with run_id | STAT, INTG |
| 15 | ADR required for boundary change | MAN (PR checklist) |
| 16 | Deletion over accumulation | INSP (reachability report) |
| 17 | Data age always displayed | INTG (age gate) |
| 18 | Third-party execution isolated | **UNVERIFIABLE — §10.2** |
| 19 | Credentials confined to Ingest | ARCH, STAT (secret scan) |
| 20 | No unmeasured performance claims | INSP, STAT (lexicon) |
| 21 | Reproduction class declared | PROP |
| 22 | RETRACTION fails build | INTG |
| 23 | Raw referenced, not redistributed | INTG |
| 24 | Retention policy | PROP, INTG |

### 2.3 Architecture invariants

| Invariant | Source | Method |
|---|---|---|
| Kernel imports nothing | E3 §11 | ARCH |
| `domain/` imports stdlib only | E4 §11 | ARCH |
| Evaluation imports contracts + domain only | E10 §11 | ARCH |
| Evidence writes nothing | E11 §11 | ARCH |
| No context imports another's internals | E4 §11 | ARCH |
| Method cannot reach test labels | E9 §11 | ARCH, INTG |
| Every new Observation has both times | E5 §11 | PROP |
| No path writes non-null historical `ingest_time` | E5 §11 | PROP |
| Identical five inputs → identical scores | E10 §11 | PROP |
| `UNREPRODUCIBLE` never persisted | E10 §11 | PROP, INTG |
| No Score without Interval | E10 §11 | PROP |
| Superseded bytes never change | E11 §11 | PROP |
| Zero JS on evidence routes | E11 §11 | INTG (budget gate) |
| No partial ingest on failure | E5 §9 | INTG |

### 2.4 Protocol requirements

| Requirement | Method |
|---|---|
| Protocol carries splits, metrics, estimator, operating points, permitted instruments, label source, `requires_bitemporal`, `tolerance` | STAT (schema) |
| Protocol frozen before any method fitted | INSP (commit-order audit) |
| Exchangeable unit is the day, never the minute | UNIT, MAN |
| Referenced protocol resolves by digest | INTG |

**Every requirement in §2 has at least one method. Four are PARTIAL or UNVERIFIABLE and are itemised in §10.2.**

---

## PART 3 — Verification methods

| Method | Definition | Authoritative for | Not sufficient for |
|---|---|---|---|
| **Inspection** | Structured human reading against a checklist | Prose conformance, non-goals, commit ordering | Any behavioural claim |
| **Static analysis** | Lint, type, schema-diff, secret scan, template scan | Forbidden constructs, schema evolution | Runtime behaviour |
| **Architecture test** | Executable assertion over the import graph and tree | Context map, dependency direction, naming | Semantics |
| **Unit test** | Single module, no fixtures, no mocks | Domain invariants, parser fields | Cross-context behaviour |
| **Property test** | Universally-quantified assertion over generated inputs | Determinism, no-imputation, no-leakage | Specific known defects |
| **Integration test** | Two or more contexts across a real boundary | Adapters, registries, gates | Whole-system claims |
| **End-to-end** | Raw descriptor → published claim | Audit chain completeness | Isolated correctness |
| **Scientific benchmark** | Evaluation under a frozen protocol | Reproducibility of results | Engineering conformance |
| **Manual review** | Expert judgement, recorded | Seam/abstraction judgements, glossary | Anything mechanisable |
| **Formal reasoning** | Argument from construction | Digest uniqueness, immutability by construction | Empirical properties |

**Precedence:** where two methods disagree, the more mechanical wins. Manual review may never overturn a failing gate.

---

## PART 4 — Validation datasets

All drawn from assets the project already holds. **No synthetic instrument data may be introduced** — the v1 failure originated in exactly that (T0 audit).

| Class | Content | Purpose | Source |
|---|---|---|---|
| **Reference** | `AdityaNet_v2_dataset_r1`, digest `43fd0e22…`, 424 SoLEXS days | The baseline every release is compared against | Existing frozen release |
| **Golden — science** | **2024-05-14**: T1 peak 16:49 UTC against GOES X8.7 at 16:51 | The single strongest end-to-end signal that real instrument data flows correctly | Existing |
| **Golden — determinism** | The 12 days of the reproducibility check (2× tables, 24 comparisons) | Byte-identical rebuild | `reproducibility_check.json` |
| **Regression** | Frozen benchmark outputs for all 8 methods on the M/X nowcast | Detect silent score drift | `benchmark_results.json` |
| **Failure — known archive defects** | F-19 GTI `STOP ≤ START` (12 archives); F-16 duplicate HK `mjd` (2 orbits); F-12 inactive detectors (426 GTI files) | Parser must fail loud or dispose per spec, never coerce | `ARCHIVE_QUALITY_REPORT.md` |
| **Parser edge cases** | Dual PHA channel families (CZT 341 / CdTe 511); GTI inclusive endpoints; R-1 epoch H3→H1→H2; NaN ⇏ GTI-excluded | Spec conformance at the exact points contradictions were raised | `SPEC-parsers@rN`, CONTRA-001…006 |
| **Corrupted** | Truncated ZIP; digest-mismatched archive; zero-length FITS; AppleDouble `._*` sidecars | `IntegrityFailure`, no partial ingest | Constructed from reference bytes |
| **Missingness** | Days with ~21% NaN; `live_time_s = 0` minutes | No imputation on any path | Existing real archive |
| **Historical releases** | Prior dataset releases retained after supersession | Rollback and audit of superseded claims | Produced by E6/E12 |
| **Label revision** | Two SWPC catalog snapshots differing on at least one event | Revision yields a second release; both retained | Captured over time |

**Gap, stated:** a genuine label-revision pair may not exist yet. Until one is captured, ADR-0007's revision behaviour is verified by *constructed* snapshots, which is weaker evidence. Recorded in §10.2.

---

## PART 5 — Acceptance testing

### Entry criteria (a milestone may be tested)

1. Every issue in the milestone is merged to `main`.
2. All twelve CI gates green on `main`.
3. Clean-export build succeeds; real-data tests **skip**, never fail.
4. Every new gate has a passing deliberate-violation test.
5. TIS acceptance criteria for the milestone are individually checkable.

### Exit criteria (a milestone is accepted)

1. Every RTM row touching the milestone has a passing verification artifact.
2. No requirement moved to UNVERIFIABLE without an entry in §10.2.
3. Regression dataset produces identical scores, or divergence is explained by an intentional, ADR-traceable change.
4. Definition of Done from Engineering Plan v1.0 §7 satisfied.

### Release criteria

Per §9, by release class. Common floor: **§7 audit procedure executable end-to-end by a person who has not seen the codebase.**

### Rollback criteria

Rollback is mandatory — not discretionary — if any of:

| Trigger | Action |
|---|---|
| Evidence gate fails on a published surface | Immediate revert to prior release digest |
| A published Score cannot be reproduced from its five inputs | Revert; open scientific-validation investigation (§8) |
| Provenance chain broken for any published claim | Revert; §8.3 |
| A dataset release is found scientifically wrong | Do **not** revert bytes. Issue `RETRACTION` per ADR-0024 |
| Divergence detected during ADR-0027 S2/S3 | Halt migration; remain on legacy path; no deadline |
| Credentials found outside Ingest, or in a log or artifact | Immediate revert; rotate; treat as security incident |

**Rollback through ADR-0027 S4 is a configuration change — re-point to the prior immutable digest — not a restore.**

---

## PART 6 — Scientific validation

### 6.1 Dataset releases are reproducible

**Claim:** rebuilding from raw produces byte-identical canonical tables.
**Method:** BENCH + INTG. Rebuild the 12 golden determinism days; compare content hash and bytes per table.
**Pass:** 24/24 comparisons byte-identical.
**Honest scope:** this is a **12-day sample across 2 of 7 tables**, not the 1,985-file archive. The published metric must say so — the existing "Partial" label is correct and must not be upgraded without full-archive evidence.

### 6.2 Evaluation results are reproducible

**Claim:** an Evaluation re-executes to identical Scores.
**Method:** PROP + INTG. Re-run from the five recorded digests on the same platform.
**Pass:** bit-identical Scores, class `EXACT`.
**Honest scope:** cross-platform `EQUIVALENT` is **not** demonstrable on a single-machine setup. See §10.2.

### 6.3 Provenance is complete

**Claim:** every published number is reachable in the provenance DAG from a raw source descriptor.
**Method:** E2E. For each Evidence Binding, walk `ancestors()` to a Tier 0 descriptor.
**Pass:** 100% of *pointer-bound* published values.
**Honest scope:** values carried verbatim inside prose tables from frozen reports are traced to the **report**, not to a pointer. Completeness is therefore verified for one of two tiers. See §10.2.

### 6.4 Limitations are respected

**Claim:** no published claim exceeds what L-1…L-11 permit.
**Method:** INSP against a checklist, one row per clause; plus STAT for the specific mechanised ones (L-3 severity, L-2 forecast-skill vocabulary) via the lexicon gate.
**Pass:** every claim maps to permitted scope; every model card cites its governing clause IDs.

### 6.5 Negative results remain reproducible

**Claim:** the headline negative result — ML provides no operational benefit over a threshold — still holds on re-execution.
**Method:** BENCH. Re-run all 8 methods under the frozen protocol; compare against the regression dataset.
**Pass:** the threshold detector's event recall remains statistically indistinguishable from the learned models', and false-alarm-run ratio is preserved in direction and order of magnitude.
**IV&V note:** this is the check most likely to be quietly dropped, because nobody is incentivised to re-verify an inconvenient result. **It is a required release gate at every class in §9.**

---

## PART 7 — Audit procedure

An external reviewer challenges a published claim. This procedure requires **no privileged access** and no contact with the maintainer.

```
CLAIM  (a sentence on a published page)
  │  1. Read the claim's Evidence Binding: measurement key + artifact + JSON pointer + digest + run_id
  ▼
EVIDENCE BINDING
  │  2. Fetch the artifact from registry/ (Tier 2, git) or its recorded URL
  │  3. Re-hash the fetched bytes; compare to the recorded digest
  │     MISMATCH → §8.3 broken provenance
  │  4. Resolve the JSON pointer; compare the value to what the page renders
  │     MISMATCH → §8.4 failed gate (the gate should have caught this)
  ▼
EVALUATION
  │  5. Read the Evaluation's five input digests + reproduction_class + leakage_gate_applied
  │  6. Confirm class is EXACT or EQUIVALENT. UNREPRODUCIBLE must not exist here
  │  7. Retrieve MethodRelease, Protocol, EnvironmentRelease by digest
  │  8. Re-execute. Compare Scores (bit-identical if EXACT; within tolerance if EQUIVALENT)
  ▼
DATASET RELEASE + LABEL RELEASE
  │  9. Resolve the dataset manifest in registry/datasets/ → Zenodo DOI
  │ 10. Download; re-hash; compare per-table and dataset digests
  │ 11. Check registry/supersessions/ for any record naming this release
  │     RETRACTION → the claim should not have rendered; §8.4
  ▼
RAW SOURCE DESCRIPTOR (Tier 0)
  │ 12. Read the retrieval descriptor: source_id, authority, selector, digest
  │ 13. Independently acquire from ISSDC/NOAA using the descriptor
  │ 14. Re-hash the acquired bytes; compare to the recorded digest
  ▼
VERDICT
```

**Every step is executable by a third party.** Steps 3, 10 and 14 are the ones that make the platform's central claim falsifiable — if any digest fails to match, the claim is unsupported regardless of how the page reads.

**Expected audit duration is not defined by the Freeze.** Step 13 is bounded by ISSDC PRADAN's manual acquisition path (~33-day latency is *publication* latency, not retrieval latency; retrieval time is unmeasured).

---

## PART 8 — Failure investigation

Common protocol: open a Run record; attach all evidence to it; conclude with a written disposition. **No investigation closes without a disposition, and no disposition may be "could not reproduce" without recorded attempts.**

### 8.1 Incorrect parser
Reproduce on the smallest failing archive → compare behaviour against `SPEC-parsers@rN` → determine spec-defect vs implementation-defect. **If the spec is wrong, raise a contradiction record (CONTRA-nnn) and adjudicate — do not silently change the parser.** Then assess blast radius: which releases contain affected rows → §8.2.

### 8.2 Corrupted / wrong release
Do **not** mutate bytes (ADR-0006). Determine severity: `CORRECTION` (wrong but recoverable), `RETRACTION` (scientifically invalid), `DEPRECATION` (superseded, not wrong). Issue a Supersession (ADR-0024). Rebuild and publish a new release. Verify the evidence gate now surfaces the notice transitively on every affected claim.

### 8.3 Broken provenance
Treat as **highest severity** — this is the platform's core property. Identify the break point via `ancestors()`. If a recorded digest cannot be resolved, the affected claims are unsupported and must be withdrawn until the chain is restored. Do not re-hash and re-record to "fix" it — that destroys the evidence of the break.

### 8.4 Failed CI gate
Never bypass. Never widen a tolerance to pass. Classify: true defect (fix code) vs gate defect (fix gate, add a violation test proving the corrected gate fails when it should). **A gate that produced a false pass is a Severity-1 finding** — the legacy repository lost 188 tests to precisely that, and the loss was invisible for four days.

### 8.5 Retracted dataset
`RETRACTION` in any claim's DAG fails the build (ADR-0024). Verify the build actually fails — do not assume. Publish the retraction notice; preserve the retracted release's bytes and every Evaluation that used it, as the audit record of what was believed and why.

### 8.6 Supersession
Verify: bytes unchanged; prior release still resolvable; notice rendered on every transitively affected claim; superseding release resolvable; rollback to the prior digest still works.

---

## PART 9 — Release certification

| Class | Required evidence |
|---|---|
| **Research Preview** | M0–M3 accepted · all 12 gates green · clean-export succeeds · audit §7 executable to the Dataset Release step · every published claim carries an Evidence Binding · limitations L-1…L-11 published · **negative-result benchmark (§6.5) reproduced** · all non-goals honoured (lexicon gate clean) |
| **v0.1** | Everything above, plus: M4–M7 accepted · at least one Dataset Release deposited with a DOI and digest-verified · Evaluation reproducible from five digests at class `EXACT` · **v1 regression test passing** (instrument gate rejects a GOES-declaring method) · Method Registry round-trip reproduces identical predictions · audit §7 executable **end to end including step 14** · §10.2 UNVERIFIABLE list published on the reproducibility surface |
| **v1.0** | Everything above, plus: M8–M9 accepted · ADR-0027 cutover complete with rollback rehearsed and evidenced · Supersession demonstrated on a real (not constructed) case · evidence gate covers 100% of pointer-bound published values · determinism verified beyond the 12-day sample **or** the sampled scope explicitly published as a limitation · an **independent third party** has executed §7 end-to-end and recorded the result |

**No class may be declared while any Severity-1 finding is open.**

**v1.0 explicitly does not require:** continuous evaluation, alerting, a public leaderboard, or sandboxed third-party execution. These are non-goals or gated items in ADR-0001 and the Engineering Plan, and requiring them here would contradict the Freeze.

---

## PART 10 — Verification coverage

### 10.1 Coverage summary

| Category | Count | Fully verified | Partial | Unverifiable |
|---|---|---|---|---|
| Active ADRs | 26 | 23 | 2 | 1 |
| Engineering standards | 24 (23 active) | 21 | 1 | 1 |
| Architecture invariants | 14 | 14 | 0 | 0 |
| CI gates | 12 | 12 | 0 | 0 |
| Protocol requirements | 4 | 4 | 0 | 0 |

**Architecture invariants and CI gates are at 100% mechanical coverage.** That is the strongest part of this plan and reflects that the Freeze made those requirements executable rather than aspirational.

### 10.2 Requirements that cannot currently be verified

Stated plainly, as the mandate requires.

| ID | Requirement | Why unverifiable | Status |
|---|---|---|---|
| **U-1** | **ADR-0016 / STD-18 — third-party execution is out-of-process, network-denied and resource-limited** | The isolation infrastructure is not built. The ARB deferred it to AR-2 and TIS E9 §13 records that first-party methods run in-process through the serialised interface. There is nothing to test | **UNVERIFIABLE.** The security property must not be claimed in any published material until AR-2 |
| **U-2** | **ADR-0021 — `EQUIVALENT` reproduction class** | Requires two platforms; the project runs on one (macOS arm64). Additionally, per-protocol `tolerance` values are **Not defined by Architecture Freeze v1.0** (TIS §17 gap 5) | **PARTIAL.** `EXACT` fully verifiable. `EQUIVALENT` must be marked unexercised wherever reported |
| **U-3** | **ADR-0023 — Tier 1 long-term durability** | A third-party institutional preservation commitment cannot be verified by testing | **PARTIAL — INSP only.** Verified by reading the host's stated policy. Deposit integrity *is* fully verifiable (digest match); durability is not |
| **U-4** | **§6.3 — provenance completeness for report-bound values** | The two-tier evidence model (pointer-bound vs report-bound) was deferred to AR-2 by the ARB. Values inside verbatim prose tables trace to a report, not a pointer, so the gate cannot check them | **PARTIAL.** Coverage claims must state "100% of pointer-bound values", never "100% of published values" |
| **U-5** | **ADR-0007 — behaviour under a real label revision** | No genuine SWPC revision pair has been captured yet. Constructed snapshots are weaker evidence | **PARTIAL.** Upgrade to full when a real revision is observed |
| **U-6** | **ADR-0001 — product-validation success metrics** (external model submissions, third-party reproductions, citations) | Outcomes external to the software. IV&V can verify the *mechanism* exists, never that anyone uses it | **OUT OF SCOPE for verification.** Track as product validation, not conformance |
| **U-7** | **Bus factor 1 / maintainer continuity** | Not a software property. Recorded as an accepted risk in the ARB report | **NOT VERIFIABLE. Accepted risk** |

### 10.3 IV&V findings against the frozen documents

Findings, not change requests — IV&V has no authority to modify the Freeze.

| Finding | Severity | Disposition |
|---|---|---|
| **F-1** | U-1: a security property (sandboxing) is specified by an active ADR but not built. Risk is that published material claims it | **Severity 2** | Add "pending verification" labelling for ADR-0016, consistent with the container precedent. Requires AR-2, not IV&V |
| **F-2** | U-4: the freeze document's evidence-coverage claim is broader than what the gate can check | **Severity 2** | Publish "pointer-bound" qualifier. Already flagged for AR-2 by the ARB |
| **F-3** | U-2: `tolerance` undefined makes one of three reproduction classes untestable | **Severity 3** | Set tolerance at first protocol registration (E8). No ADR needed — the Freeze delegates it to the protocol |
| **F-4** | §6.1 determinism evidence is a 12-day, 2-table sample presented alongside full-archive integrity figures | **Severity 3** | Existing "Partial" label is correct. IV&V will fail any attempt to upgrade it without full-archive evidence |

**No Severity-1 findings.** The architecture exposes sufficient evidence to verify every architecture invariant and every gate mechanically, which is the substantive question this plan was convened to answer.

---

## PART 11 — IV&V independence

1. IV&V artifacts live in `docs/tis/` and are versioned with the code they assess.
2. IV&V may block a release. IV&V may not modify the Freeze, the Plan, or the TIS.
3. Any disagreement between IV&V and the implementing team escalates to an ADR — which is an architecture decision, and therefore outside both parties' authority to make unilaterally.
4. This plan is itself subject to the rule it imposes: **a claim in this document that cannot be demonstrated is a defect in this document.**
