# Technical Implementation Specification v1.0

**Governed by:** Architecture Freeze v1.0 (ADR-0001…0027, minus superseded 0009/0018)
**Sequenced by:** Engineering Plan v1.0 (E1…E14, M0…M10, issues #1…#47)
**Status:** implementation handbook. Not an architecture document.

> **This document may not change architecture.** Where a design decision appears necessary
> it cites the governing ADR. Where the Freeze is silent, the text says
> **"Not defined by Architecture Freeze v1.0."** and defers — it does not decide.

---

## Table of contents

- [§0 Cross-cutting requirements](#0-cross-cutting-requirements)
- [§1 E1 — Constitution & repository bootstrap](#e1--constitution--repository-bootstrap)
- [§2 E2 — Amputation](#e2--amputation)
- [§3 E3 — Provenance shared kernel](#e3--provenance-shared-kernel)
- [§4 E4 — Contracts & pure domain model](#e4--contracts--pure-domain-model)
- [§5 E5 — Ingest](#e5--ingest)
- [§6 E6 — Curation & Tier 1 storage](#e6--curation--tier-1-storage)
- [§7 E7 — Ground truth registry](#e7--ground-truth-registry)
- [§8 E8 — Protocol & environment registries](#e8--protocol--environment-registries)
- [§9 E9 — Method registry](#e9--method-registry)
- [§10 E10 — Evaluation engine](#e10--evaluation-engine)
- [§11 E11 — Evidence, supersession & portal](#e11--evidence-supersession--portal)
- [§12 E12 — Bitemporal migration](#e12--bitemporal-migration)
- [§13 E13 — Continuous evaluation (GATED)](#e13--continuous-evaluation-gated)
- [§14 E14 — CI gates & architecture enforcement](#e14--ci-gates--architecture-enforcement)
- [§15 Master issue table](#15-master-issue-table)
- [§16 Diagrams](#16-diagrams)

---

## §0 Cross-cutting requirements

These apply to every epic and are stated once. An epic section overrides them only where it says so explicitly.

### 0.1 Implementation language

**Not defined by Architecture Freeze v1.0.**

ADR-0021 pins `PYTHONHASHSEED` and an "interpreter version"; ADR-0019 assumes a monorepo with two languages. This *implies* Python for pipeline contexts and TypeScript for `apps/portal`. Recorded as an implied convention. An implementer choosing otherwise must satisfy every ADR obligation, including a deterministic hash-seed equivalent.

### 0.2 Failure taxonomy

Every context uses exactly these classes. No others. No catch-all.

| Class | Meaning | Disposition |
|---|---|---|
| `ContractViolation` | Input fails its schema or an invariant | Abort. Never coerce (Standard 13) |
| `IntegrityFailure` | Digest mismatch, tamper, truncation | Abort. Never partial-ingest (ADR-0005) |
| `ProvenanceFailure` | Required provenance absent or unresolvable | Abort (ADR-0012) |
| `UnavailableResource` | External source unreachable | Retry per adapter policy, then abort |
| `PolicyRejection` | A gate refused the operation | Abort with the gate's identity |

**Forbidden universally:** bare `except`, silent fallback, default-on-error, coercion of malformed input, imputation of a missing value (ADR-0017).

### 0.3 Logging (Standard 14)

Structured records only. Prose logs are not observability.

**Mandatory fields on every record:** `run_id`, `context`, `event`, `level`, `ts_utc`.
**Mandatory where applicable:** `artifact_digest`, `source_id`, `instrument_id`, `release_digest`, `gate`.
**Forbidden in any record:** credentials, cookies, session tokens, raw archive bytes (ADR-0023 §Tier 0, E5 §13).

### 0.4 Determinism

Per ADR-0021, determinism is enforced by a **pinned input**, not by discipline. No context may read wall-clock time, environment variables, or `random` without seeding from the `EnvironmentRelease`. Exception: `ingest_time` capture in E5, which is definitionally a clock read at the acquisition boundary.

### 0.5 Performance expectations

**Not defined by Architecture Freeze v1.0** beyond ADR-0014 (batch, single-node) and Standard 20 (no optimisation without measurement, no throughput claims without a benchmark).

Volumetric facts that bound the work, recorded so implementers do not over-engineer: ~424 SoLEXS observation days; ~1,985 files; ~600 MB canonical per release; ~192,541 held-out test minutes; ~21 GB Tier 0 (referenced, not stored). No latency budget exists because no operational consumer exists (ADR-0001 non-goals).

### 0.6 Code ownership

Bus factor 1 — an accepted risk on record. `CODEOWNERS` assigns every path to the maintainer. Context directories are listed individually so that ownership becomes divisible without restructuring if contributors arrive.

### 0.7 Universal acceptance bar

No issue is Done until: all gates in E14 pass; the clean-export build succeeds; real-data tests **skip rather than fail** when the archive is absent (Standard 12); and no new numeric literal appears in a publication template (Standard 5).

---

## E1 — Constitution & repository bootstrap

**Issues:** #1 #2 #3 #4 · **Milestone:** M0 · **ADRs:** 0001, 0019, 0026

**1. Purpose.** Make the Freeze an in-tree, citable, machine-checkable artifact set before any code exists.

**2. Scope.** ADR corpus, standards, folder skeleton, `specs/` prose, L-11. *Out of scope:* any executable context code.

**3. Responsibilities.** Own `adr/`, `standards/`, `specs/`, and the top-level directory contract.

**4. Public interfaces.** Stable citation identifiers: `ADR-nnnn`, `STD-nn`, `L-nn`, `CONTRA-nnn`, `SPEC-parsers@rN`. Every other epic cites these and must never restate their content (ADR-0013).

**5. Internal modules.** None — prose and structure only.

**6. Input contracts.** Existing prose assets in the legacy tree (parser specification, L-1…L-10, six contradiction records).

**7. Output contracts.** One file per citable ID. Front-matter: `id`, `title`, `status` (`active` | `superseded`), `supersedes`, `superseded_by`.

**8. Failure modes.** Dangling citation → `ContractViolation` at gate time. Duplicate ID → `ContractViolation`.

**9. State transitions.** ADR: `proposed → accepted → superseded`. **`accepted → edited` does not exist** — supersede, never edit.

**10. Validation rules.** Every ID unique; every `supersedes` resolves; superseded documents retain their bytes in `adr/superseded/`.

**11. Invariants.** *(i)* Exactly one file per citable ID. *(ii)* An accepted ADR's bytes never change. *(iii)* Every `L-nn` cited anywhere resolves.

**12. Performance.** N/A.

**13. Security.** None — no secrets, no external input.

**14. Logging.** N/A (no runtime).

**15. Error handling.** Gate-time only.

**16. Test requirements.** Architecture test: no forbidden directory names (`common`, `shared`, `utils`, `core`, `legacy`, `archive`, `misc`) at any depth. Link gate: every citation resolves.

**17. CI requirements.** `links`, `architecture` gates active from the first commit.

**18. Acceptance criteria.** 26 active + 2 superseded ADRs present; STD-01…24 present; skeleton matches TIS §16.4 exactly; L-11 authored and matching ADR-0022 wording; a PR touching only `adr/` reports every required check.

**19. Example execution flow.** Author writes ADR-0028 → `status: proposed` → review → `accepted`, and if it supersedes 0021 then 0021 moves to `adr/superseded/` with `superseded_by: ADR-0028`. Its bytes are unchanged.

**20. Files.** `adr/ADR-00{01..27}.md`, `adr/superseded/ADR-0009.md`, `adr/superseded/ADR-0018.md`, `adr/index.md`, `standards/STD-{01..24}.md`, `specs/parsers/`, `specs/limitations/L-{01..11}.md`, `specs/contradictions/`, per-directory `README.md`.

---

## E2 — Amputation

**Issues:** #7 #8 #9 · **Milestone:** M1 · **ADRs:** 0001

**1. Purpose.** Remove ~22,900 LOC of the repudiated v1 generation, which trained on simulated data and is referenced by no CI job, deploy, or surface.

**2. Scope.** `app/api`, `app/main.py`, `app/services/**`, v1 scripts, sprint-numbered artifact directories, duplicate compose/config. *Out of scope:* `app/v2/**`, which E5 ports.

**3. Responsibilities.** Tag, salvage prose, delete, verify nothing broke.

**4. Public interfaces.** Git tag `v1-surya-final`. Recovery: `git checkout v1-surya-final -- <path>`.

**5. Internal modules.** None.

**6. Input contracts.** Current `main`.

**7. Output contracts.** Deletion commit whose message contains the tag and the recovery command.

**8. Failure modes.** Deleting something still referenced → CI failure (this is the intended detection mechanism).

**9. State transitions.** `present → tagged → salvaged → deleted`. Deletion may not precede tagging.

**10. Validation rules.** Before deletion, prove orphanhood: no reference from `.github/`, `render.yaml`, or any surface.

**11. Invariants.** Git history is the archive (ADR-0001 §Non-goals; no in-tree `archive/`).

**12–15.** N/A — no runtime.

**16. Test requirements.** Full CI green post-deletion; clean-export build succeeds.

**17. CI requirements.** All gates.

**18. Acceptance criteria.** Tag resolves and restores; ~22,900 LOC removed; salvage prose present in `specs/salvage/`; clean-export build succeeds.

**19. Example execution flow.** Tag → write `specs/salvage/goes-ingestion.md` citing the tagged commit → delete in reviewable batches → CI green.

**20. Files.** Deletions only, plus `specs/salvage/*.md`.

---

## E3 — Provenance shared kernel

**Issues:** #10 · **Milestone:** M2 · **ADRs:** 0005, 0026

**1. Purpose.** The single minting authority for digests. Reclassified from context to **shared kernel** by ADR-0026.

**2. Scope.** `Artifact`, `Digest`, `Run`, `ProvenanceRecord`, DAG traversal. *Out of scope:* anything domain-aware.

**3. Responsibilities.** Mint digests; record lineage; traverse the DAG; answer reachability queries used by E11's supersession gate.

**4. Public interfaces.**

| Operation | Input | Output |
|---|---|---|
| `digest(bytes)` | byte sequence | `Digest` |
| `record(run, inputs[], outputs[])` | run + digests | `ProvenanceRecord` |
| `ancestors(digest)` | digest | set of reachable digests |
| `begin_run(context, event)` / `end_run(run_id, status)` | — | `Run` |

**5. Internal modules.** `artifact`, `digest`, `run`, `record`, `dag`.

**6. Input contracts.** Byte sequences and digests only. **No domain object may enter this kernel** (ADR-0026).

**7. Output contracts.** `provenance-record.schema.json`.

**8. Failure modes.** `IntegrityFailure` on digest mismatch; `ProvenanceFailure` on an unresolvable input digest.

**9. State transitions.** Run: `started → ended(ok|failed)`. Terminal states are immutable.

**10. Validation rules.** Every `ProvenanceRecord` input digest must already exist. Cycles are rejected.

**11. Invariants.** *(i)* **The kernel imports nothing** — no internal package, no third party (test-enforced). *(ii)* Digest is stable across process restarts, orderings and platforms. *(iii)* Records are append-only.

**12. Performance.** Streaming digest computation; the 21 GB Tier 0 cache must never be fully buffered.

**13. Security.** No network. No filesystem writes outside the artifact store root.

**14. Logging.** `run_id` on every record; digests logged as prefixes only.

**15. Error handling.** Fail loud. A digest that cannot be computed is never substituted.

**16. Test requirements.** Unit: digest stability, DAG construction, cycle rejection. Property: same bytes → same digest across restarts and input orderings. Architecture: **zero imports**.

**17. CI requirements.** `architecture` gate blocks any import added to the kernel.

**18. Acceptance criteria.** Kernel has zero imports, test-enforced; digest stability property passes; `ancestors()` returns correct closure on a fixture DAG.

**19. Example execution flow.** E5 acquires bytes → `digest()` → `begin_run` → parse → `record(run, [raw], [observations])` → `end_run`. E11 later calls `ancestors(claim_artifact)` to evaluate supersession.

**20. Files.** `kernel/provenance/{__init__,artifact,digest,run,record,dag}`, `tests/architecture/test_kernel_imports`.

---

## E4 — Contracts & pure domain model

**Issues:** #11 #12 #13 #14 · **Milestone:** M2 · **ADRs:** 0002, 0019, 0021, 0022, 0024

**1. Purpose.** The only cross-context vocabulary, plus invariants expressed as callable predicates.

**2. Scope.** Ten JSON Schemas; domain entities and value objects; import-direction rules; Tier 2 manifest format. *Out of scope:* persistence, I/O.

**3. Responsibilities.** Define contracts; express invariants; enforce the context map mechanically.

**4. Public interfaces.** The ten schemas listed in TIS §16.4, plus `domain.invariants.*` predicates.

**5. Internal modules.** `domain/entities`, `domain/values`, `domain/invariants`.

**6. Input contracts.** None — this epic is the source of contracts.

**7. Output contracts.** Normative JSON Schema. Per ADR-0019, schemas are normative and types are hand-written and validated against them. *(ARB flagged codegen for AR-2 downgrade; TIS implements the frozen ADR as written and notes the pending revision.)*

**8. Failure modes.** `ContractViolation` on schema failure or invariant breach.

**9. State transitions.** Schema: `vN → vN+1` additive within a major; breaking change requires a new major.

**10. Validation rules.**

| Contract | Rule |
|---|---|
| `observation` | `valid_time` required; `ingest_time` **nullable**, meaning "unknown — predates bitemporal capture" (ADR-0022). Never fabricated |
| `protocol` | `requires_bitemporal: bool` and `tolerance` required |
| `evaluation` | `environment_release`, `reproduction_class`, `leakage_gate_applied` required; identity is `sha256` of five inputs (ADR-0021) |
| `method-release` | `declared_instruments[]` required (ADR-0011) |
| `supersession` | `severity ∈ {CORRECTION, RETRACTION, DEPRECATION}`; `superseding` nullable (ADR-0024) |
| all | Every immutable object is content-addressed (ADR-0005) |

**11. Invariants.** *(i)* `domain/` imports stdlib only. *(ii)* No entity carries a mutable identity except `Dataset`, `Method`, `Source`, `Instrument`, `LabelSource` — all *names*, never referenced by evaluations. *(iii)* Schema diffs additive within a major.

**12. Performance.** Validation is per-object and not on any hot path.

**13. Security.** Schemas must not permit free-form paths that could escape the artifact root.

**14. Logging.** N/A — pure.

**15. Error handling.** `ContractViolation` carries the JSON Pointer of the failing field.

**16. Test requirements.** Unit: **no fixtures, no mocks** — if a mock is needed the code is in the wrong layer. Property: every invariant. Architecture: stdlib-only imports; all six ADR-0026 import rules with deliberate-violation tests.

**17. CI requirements.** `contracts` gate (additive-only diff), `architecture` gate.

**18. Acceptance criteria.** Ten schemas validate; round-trip fixtures pass; `domain/` imports stdlib only; every import rule has a passing deliberate-violation test; manifest format validates.

**19. Example execution flow.** E5 constructs an `Observation` → `domain.invariants.observation_is_wellformed()` → serialise → validate against `observation.schema.json` → hand to E6.

**20. Files.** `contracts/*.schema.json` (10), `domain/entities/*`, `domain/values/*`, `domain/invariants/*`, `tests/architecture/test_context_imports`.

---

## E5 — Ingest

**Issues:** #15 #16 #17 #18 #19 · **Milestone:** M3 · **ADRs:** 0003, 0004, 0022, 0025

**1. Purpose.** Acquire from a Source and canonicalise via an Instrument parser into bitemporal Observations.

**2. Scope.** `SourceAdapter` contract; ISSDC-PRADAN adapter; SoLEXS and HEL1OS parsers; dual write. Acquisition and canonicalisation are **one context** with two internal module groups (ADR-0026); the seam is preserved as module boundaries, which is free (ADR-0025).

**3. Responsibilities.** Retrieve; verify integrity; stamp `ingest_time` at the boundary; parse to the canonical minute grid; preserve missingness.

**4. Public interfaces.**

```
SourceAdapter:
  descriptor()            -> SourceDescriptor {source_id, authority, latency_class, granularity}
  acquire(selector)       -> RawArtifact + AcquisitionProvenance
InstrumentParser:
  parse(RawArtifact)      -> Iterable[Observation]
```

**5. Internal modules.** `adapters/issdc_pradan`, `parsers/solexs/{lc,pi,gti}`, `parsers/hel1os/{lc,hk,gti,spectra,events}`, `grid`, `write`.

**6. Input contracts.** Tier 0 retrieval descriptor (ADR-0023). Archive products per `SPEC-parsers@rN`.

**7. Output contracts.** `observation.schema.json`, plus `AcquisitionProvenance` recorded through E3.

**8. Failure modes.** `UnavailableResource` (portal/feed unreachable) · `IntegrityFailure` (digest mismatch → **no partial ingest**) · `ContractViolation` (structure violates spec → **fail loud, never coerce**) · `PolicyRejection` (adapter attempted to redistribute Tier 0 bytes).

**9. State transitions.**

```
requested → acquired → verified → parsed → stamped → written
     └────────────── any failure ─────────────→ aborted
```
No partial state is persisted. `aborted` leaves no observations.

**10. Validation rules.** Digest verified **before** any read. Structure checked before semantics. Minute grid completeness asserted. GTI endpoints inclusive per spec. **Missing stays missing** — no fill, interpolate, or zero-substitution (ADR-0017).

**11. Invariants.** *(i)* Every newly ingested Observation carries `valid_time` **and** `ingest_time`. *(ii)* **No code path writes a non-null `ingest_time` for historical data** (ADR-0022). *(iii)* Credentials never leave this context. *(iv)* Tier 0 bytes are never redistributed; local copies are evictable caches.

**12. Performance.** Streaming parse; whole-day archives must not be fully materialised.

**13. Security.** **Highest-sensitivity context.** Holds the only secrets. PRADAN session cookies confined here; never logged, never persisted to an artifact, never crossing the boundary. Retrieval descriptors record *how* to acquire, never credentials.

**14. Logging.** `source_id`, `instrument_id`, `artifact_digest` prefix, row counts, gap counts. **Never** cookies, URLs containing tokens, or raw bytes.

**15. Error handling.** Retry policy is adapter-local. Retry exhaustion → `UnavailableResource`, abort, no partial write.

**16. Test requirements.** Unit: per-field parser correctness against `SPEC-parsers@rN`. Property: no imputation on any path; every new observation has both times. Integration: adapter → parser → Observation on fixtures. **Real-data guards must test for the FITS products they need, not for a directory** (STD-12) — the legacy `isdir` guard silently disabled 188 tests.

**17. CI requirements.** `clean-export` must show real-data tests **skipping**, never failing.

**18. Acceptance criteria.** ISSDC adapter registered with latency class `~33d`, granularity `daily-archive`; both parser suites pass; every newly ingested observation has both times; **zero historical rows carry a non-null `ingest_time`**; no-imputation property passes.

**19. Example execution flow.** See sequence diagram §16.1.

**20. Files.** `contexts/ingest/adapters/issdc_pradan/*`, `contexts/ingest/parsers/solexs/*`, `contexts/ingest/parsers/hel1os/*`, `contexts/ingest/{grid,write}`, tests mirrored.

---

## E6 — Curation & Tier 1 storage

**Issues:** #20 #21 #22 · **Milestone:** M4 · **ADRs:** 0006, 0023, 0024

**1. Purpose.** Freeze observations into immutable, citable Dataset Releases and deposit them durably at zero cost.

**2. Scope.** Freeze, per-table and dataset digests, Zenodo deposition, retention. *Out of scope:* knowledge of how data will be used (ADR-0026 — curation must not optimise for the benchmark).

**3. Responsibilities.** Freeze; hash; deposit; record the manifest in git (Tier 2); enforce retention.

**4. Public interfaces.** `freeze(selector) -> DatasetRelease` · `deposit(DatasetRelease) -> DOI` · `prune(policy) -> report`.

**5. Internal modules.** `freeze`, `manifest`, `deposit/zenodo`, `deposit/github_release` (fallback), `retention`.

**6. Input contracts.** Observations from E5.

**7. Output contracts.** `dataset-release.schema.json`; Tier 2 manifest in `registry/datasets/` carrying digest + DOI + URL.

**8. Failure modes.** `PolicyRejection` on re-publishing an existing version · `IntegrityFailure` if the deposited digest differs from local · `UnavailableResource` if Zenodo is unreachable → documented fallback.

**9. State transitions.** `draft → frozen → deposited → (superseded)`. **`frozen → edited` does not exist.**

**10. Validation rules.** Version uniqueness; per-table digests roll deterministically to one dataset digest; deposited bytes re-hashed and compared.

**11. Invariants.** *(i)* A release's bytes never change (ADR-0006). *(ii)* Re-publishing a version is rejected. *(iii)* Tier 0 is never deposited (ADR-0023). *(iv)* Artifacts referenced by an Evidence Binding are **never** pruned.

**12. Performance.** ~600 MB per release. Deposition is I/O-bound; resumable upload required.

**13. Security.** Zenodo API token is a deployment secret, never in the repository.

**14. Logging.** `release_digest`, table digests, byte counts, DOI, prune classifications.

**15. Error handling.** Deposition failure leaves the local frozen release intact and re-runnable.

**16. Test requirements.** Unit: digest rollup determinism. Integration: freeze → Zenodo sandbox → digest match; re-freeze rejected; fallback path exercised. Property: a referenced artifact is never selected for pruning.

**17. CI requirements.** `retention` gate; `contracts` gate on the manifest.

**18. Acceptance criteria.** A release is frozen, deposited with a DOI, deposited digest matches; re-publishing rejected; fallback exercised; prune dry-run correct.

**19. Example execution flow.** Freeze → per-table digests → dataset digest → deposit → DOI → commit manifest to `registry/datasets/` → the manifest, not the data, is what git carries.

**20. Files.** `contexts/curation/{freeze,manifest,retention}`, `contexts/curation/deposit/{zenodo,github_release}`, `registry/datasets/*.json`.

---

## E7 — Ground truth registry

**Issues:** #23 #24 · **Milestone:** M5 · **ADRs:** 0007

**1. Purpose.** Version an exogenous, revisable authority so that a label revision cannot silently invalidate historical scores.

**2. Scope.** Label Source, Label Release, Event extraction. **Deliberately never merged into E6** (ADR-0007).

**3. Responsibilities.** Snapshot; version; extract Events deterministically.

**4. Public interfaces.** `snapshot(label_source) -> LabelRelease` · `events(LabelRelease) -> Iterable[Event]`.

**5. Internal modules.** `sources/noaa_swpc`, `release`, `events`.

**6. Input contracts.** NOAA SWPC catalog responses. Retrieved through an E5-style adapter; **credentials, if ever required, remain in the adapter**.

**7. Output contracts.** `label-release.schema.json`.

**8. Failure modes.** `UnavailableResource`; `IntegrityFailure`; `PolicyRejection` on attempting to mutate an existing release.

**9. State transitions.** `snapshotted → released → (superseded)`. A revision produces a **new** release; both are retained.

**10. Validation rules.** `ingest_time` recorded on every release. Event onset ≤ peak ≤ end. Class parsed strictly.

**11. Invariants.** *(i)* Releases are immutable. *(ii)* A revised catalog yields a second release; **the first is never overwritten**. *(iii)* Event extraction is deterministic given a release.

**12. Performance.** Small — catalog scale, not archive scale.

**13. Security.** Public feed; no secrets expected. **Not defined by Architecture Freeze v1.0** if NOAA later requires authentication.

**14. Logging.** `label_source_id`, `release_digest`, event counts by class.

**15. Error handling.** Fail loud on malformed catalog entries; never skip an unparseable event silently.

**16. Test requirements.** Unit: event boundary parsing. Property: same release → identical events. Integration: a revised catalog produces a second release with both retained and independently addressable.

**17. CI requirements.** `contracts` gate.

**18. Acceptance criteria.** Label release immutable and digest-addressed; revision yields a second release with both retained; event extraction deterministic.

**19. Example execution flow.** Snapshot catalog → digest → `LabelRelease` → manifest to `registry/labels/` → E10 pins it **by digest**, never by "latest."

**20. Files.** `contexts/groundtruth/{release,events}`, `contexts/groundtruth/sources/noaa_swpc`, `registry/labels/*.json`.

---

## E8 — Protocol & environment registries

**Issues:** #25 #26 · **Milestone:** M5 · **ADRs:** 0008, 0021

**1. Purpose.** Make pre-registration meaningful (Protocol) and the central invariant checkable (EnvironmentRelease).

**2. Scope.** Both registries. *Out of scope:* executing anything.

**3. Responsibilities.** Freeze protocols as artifacts; capture and digest environments.

**4. Public interfaces.** `register_protocol(spec) -> Protocol` · `capture_environment() -> EnvironmentRelease`.

**5. Internal modules.** `protocols/registry`, `environment/capture`, `environment/digest`.

**6. Input contracts.** Protocol specification (migrated from prose); live process environment.

**7. Output contracts.** `protocol.schema.json`, `environment-release.schema.json`.

**8. Failure modes.** `ContractViolation` on an incomplete protocol; `PolicyRejection` on mutating a registered protocol.

**9. State transitions.** `drafted → registered → (superseded)`. Registered protocols are immutable (ADR-0008).

**10. Validation rules.** Protocol must carry splits, metrics, uncertainty estimator, operating points, permitted instruments, label source, `requires_bitemporal`, `tolerance`. Environment must carry interpreter, lockfile digest, BLAS, thread counts, hash seed, container digest where used, **and record platform without pinning it** (ADR-0021).

**11. Invariants.** *(i)* A protocol referenced by an evaluation exists by digest. *(ii)* Same environment → same digest; different BLAS → different digest. *(iii)* Platform is recorded, never pinned — cross-architecture bit-identity is **not** claimed.

**12. Performance.** Negligible.

**13. Security.** Environment capture must not record secrets present in the process environment. Allow-list the captured variables; never capture wholesale.

**14. Logging.** `protocol_digest`, `environment_digest`, captured field names (never values).

**15. Error handling.** Missing required environment field → `ContractViolation`. Never default.

**16. Test requirements.** Unit: digest sensitivity to each pinned field. Property: capture is stable within a machine and run. Integration: protocol migrated from prose validates.

**17. CI requirements.** `contracts` gate; gate that every referenced protocol/environment digest resolves.

**18. Acceptance criteria.** Protocol migrated from prose to immutable artifact; environment digest changes when BLAS changes; secrets never captured.

**19. Example execution flow.** Capture environment → digest → register → E10 pins it as the fifth input.

**20. Files.** `contexts/evaluation/protocols/registry`, `contexts/evaluation/environment/{capture,digest}`, `registry/{protocols,environments}/*.json`.

---

## E9 — Method registry

**Issues:** #27 #28 #29 · **Milestone:** M6 · **ADRs:** 0010, 0011, 0016

**1. Purpose.** Make methods retrievable and re-executable. A benchmark whose methods cannot be retrieved is a report.

**2. Scope.** Method Release registry; execution wire format; porting the eight detectors. **Isolation infrastructure is not built** — ADR-0016 as frozen specifies the wire format; the ARB flagged the isolation build for AR-2 downgrade.

**3. Responsibilities.** Register; retrieve; invoke through a serialised boundary; carry declared instrument requirements.

**4. Public interfaces.** `register(method_artifact, params, training_provenance, declared_instruments) -> MethodRelease` · `invoke(MethodRelease, inputs) -> Predictions`.

**5. Internal modules.** `registry`, `wire`, `methods/{threshold_rate,logistic,random_forest,lightgbm,random,majority,climatology,persistence}`.

**6. Input contracts.** Serialised method artifact; training provenance from E3.

**7. Output contracts.** `method-release.schema.json`; predictions over the wire format.

**8. Failure modes.** `ContractViolation` (missing `declared_instruments`) · `IntegrityFailure` (artifact digest mismatch on retrieval) · `PolicyRejection` (invocation bypassing the wire format).

**9. State transitions.** `trained → registered → (superseded)`. Immutable once registered.

**10. Validation rules.** `declared_instruments` non-empty and drawn from the known instrument set. Retrieval re-hashes the artifact.

**11. Invariants.** *(i)* A registered release re-instantiates from its digest and reproduces identical predictions on a fixture. *(ii)* **The Method context cannot reach test-period Label Releases** — enforced by executing with a filtered view (ADR-0026). *(iii)* All methods, including first-party, are invoked through the wire format.

**12. Performance.** Wire serialisation must not dominate; **Not defined by Architecture Freeze v1.0** beyond STD-20.

**13. Security.** The wire format is the trust boundary. Deserialisation must reject arbitrary object construction. Out-of-process, no-network execution is specified by ADR-0016; **infrastructure deferred**, so until then first-party methods run in-process through the same serialised interface, and this limitation is recorded, not hidden.

**14. Logging.** `method_release_digest`, `declared_instruments`, prediction counts.

**15. Error handling.** A method raising is a `ContractViolation` attributed to that release, never to the engine.

**16. Test requirements.** Unit: registry round-trip. Property: retrieved release reproduces identical predictions on a fixture. Integration: all eight methods invoked through the wire format.

**17. CI requirements.** `contracts`; gate that no method is invoked outside the wire format.

**18. Acceptance criteria.** Eight methods registered immutably with declared requirements; each re-instantiates and reproduces predictions; all invoked through the wire format.

**19. Example execution flow.** Train → serialise → `register` with `declared_instruments=["solexs"]` → E10 retrieves by digest → E10's gate checks declared ⊆ permitted → invoke.

**20. Files.** `contexts/method/{registry,wire}`, `contexts/method/methods/*`, `registry/methods/*.json`.

---

## E10 — Evaluation engine

**Issues:** #30 #31 #32 #33 #34 · **Milestone:** M7 · **ADRs:** 0021, 0022, 0011 · **HIGHEST RISK**

**1. Purpose.** Realise the central invariant: an Evaluation is a function of five pinned inputs.

**2. Scope.** Engine, reproduction class, leakage gate, instrument gate, scoring with intervals. *Out of scope:* how a method works internally — the engine executes a released artifact and never imports a method (ADR-0026).

**3. Responsibilities.** Pin five inputs; enforce two gates; compute scores with uncertainty; assign a reproduction class; refuse to publish unreproducible results.

**4. Public interfaces.**

```
evaluate(method_release, dataset_release, label_release, protocol, environment_release)
    -> Evaluation
```

**5. Internal modules.** `engine`, `gates/leakage`, `gates/instrument`, `scoring/metrics`, `scoring/bootstrap`, `reproduction_class`.

**6. Input contracts.** Five digests. Nothing else. No wall clock, no environment reads outside the pinned `EnvironmentRelease` (§0.4).

**7. Output contracts.** `evaluation.schema.json`, including `environment_release`, `reproduction_class`, `leakage_gate_applied`.

**8. Failure modes.** `PolicyRejection` — instrument gate (declared ⊄ permitted) · `PolicyRejection` — leakage gate (a future-ingested observation reached a prediction) · `ContractViolation` — a Score without an Interval · `PolicyRejection` — attempt to persist an `UNREPRODUCIBLE` evaluation.

**9. State transitions.**

```
requested → inputs_pinned → gates_passed → scored → classified → persisted
     │                │              │
     │                │              └─ gate failure → refused (PolicyRejection)
     │                └─ missing digest → refused
     └─ UNREPRODUCIBLE → refused, never persisted
```

**10. Validation rules.**

| Rule | ADR |
|---|---|
| Evaluation identity = `sha256` of all five inputs | 0021 |
| `declared_instruments ⊆ permitted_instruments` | 0011 |
| If `requires_bitemporal`: exclude `ingest_time IS NULL`; reject any observation with `ingest_time > as_of` | 0022 |
| If `¬requires_bitemporal`: record `leakage_gate_applied = false` | 0022 |
| Every Score carries Interval, estimator name, exchangeable unit, denominator | STD-05 |
| `EXACT` iff five inputs and platform match; `EQUIVALENT` iff platform differs and scores agree within `tolerance`; else `UNREPRODUCIBLE` | 0021 |

**11. Invariants.** *(i)* Identical five inputs → identical scores (class `EXACT`). *(ii)* `UNREPRODUCIBLE` evaluations are never persisted or published. *(iii)* The engine imports contracts and domain only. *(iv)* Day-block bootstrap is the declared estimator — the exchangeable unit is the **day**, never the minute.

**12. Performance.** ~192,541 test minutes × 8 methods. Single-node, batch (ADR-0014). No latency requirement.

**13. Security.** Executes third-party-shaped artifacts through E9's wire format. Deserialisation hardening is E9's responsibility; the engine must not extend trust beyond it.

**14. Logging.** All five digests; gate outcomes with the gate's identity; reproduction class; score count. A refusal must log **which** gate refused and why.

**15. Error handling.** A gate refusal is a first-class outcome, not an exception to be swallowed. Refusals are recorded as artifacts so that "this was refused" is itself auditable.

**16. Test requirements.**
Unit: metric correctness; bootstrap; class assignment.
Property: identical five inputs → identical scores; **no prediction consumes an observation with `ingest_time > as_of`**; no Score serialises without an Interval.
Integration: **regression test reproducing the v1 failure** — a method declaring a GOES input is rejected by an Aditya-only protocol; a changed environment digest yields a distinct evaluation identity.

**17. CI requirements.** All gates; the v1 regression test is a required check.

**18. Acceptance criteria.** Identity is `sha256` of five inputs; identical inputs reproduce identical scores; reproduction class assigned correctly; leakage gate enforced in both protocol modes; v1 regression test passes; no Score without an Interval.

**19. Example execution flow.** See sequence diagram §16.2 and state machine §16.3.

**20. Files.** `contexts/evaluation/engine`, `contexts/evaluation/gates/{leakage,instrument}`, `contexts/evaluation/scoring/{metrics,bootstrap}`, `contexts/evaluation/reproduction_class`, `registry/evaluations/*.json`.

---

## E11 — Evidence, supersession & portal

**Issues:** #39 #40 #41 #42 · **Milestone:** M9 · **ADRs:** 0012, 0013, 0015, 0024

**1. Purpose.** Bind every published value to bytes; surface supersession transitively; render.

**2. Scope.** Supersession model, evidence binding, consistency gate, static portal. Evidence and Publication are **one context** (ADR-0026).

**3. Responsibilities.** Bind; gate; render; display data age; never write to any other context.

**4. Public interfaces.** `bind(claim, artifact, pointer) -> EvidenceBinding` · `check() -> GateReport` · `supersede(release, severity, reason, superseding?) -> Supersession`.

**5. Internal modules.** `binding`, `gate`, `supersession`, `render`.

**6. Input contracts.** Artifacts and manifests from every other context (read-only).

**7. Output contracts.** `evidence-binding.schema.json`, `supersession.schema.json`, static HTML + Tier 2 payloads.

**8. Failure modes.** `ContractViolation` — numeric literal in a template · `IntegrityFailure` — rendered value diverges from artifact · `PolicyRejection` — `RETRACTION` in a claim's provenance DAG.

**9. State transitions.** Release standing: `active → DEPRECATION | CORRECTION | RETRACTION`. **Bytes never transition** (ADR-0024).

**10. Validation rules.** Components accept measurement keys, never values. Gate re-reads artifacts from storage and compares against rendered output. Supersession is evaluated **transitively** via `kernel.provenance.ancestors()`. Every surface displays data age (STD-17).

**11. Invariants.** *(i)* Evidence writes nothing (ADR-0026). *(ii)* A retraction anywhere in a claim's DAG **fails the build**. *(iii)* Zero JS on evidence routes (ADR-0015). *(iv)* Superseded release bytes are never changed or deleted.

**12. Performance.** Static generation. Per-route byte budgets enforced.

**13. Security.** Strict CSP; no external origins; hash-based script allow-listing.

**14. Logging.** Gate reports enumerate every checked binding, not just failures.

**15. Error handling.** Gate failures are build failures, never warnings (ADR-0020).

**16. Test requirements.** Unit: binding resolution. Property: no supersession mutates a release. Integration: deliberate drift fails; literal in a template fails; **a retracted release three hops upstream fails the build**.

**17. CI requirements.** `evidence`, `supersession`, `budget`, `links`, `lexicon`, `age` gates — all required.

**18. Acceptance criteria.** Supersession records immutable; retraction three hops upstream fails the build; gate covers every pointer-reachable published quantity; zero JS on evidence routes; data age displayed on every surface.

**19. Example execution flow.** Render binds `roc_auc` by key → gate re-reads `evaluation.json`, resolves the pointer, compares → mismatch fails build. Separately, `ancestors(claim)` returns a digest with a `RETRACTION` → build fails.

**20. Files.** `contexts/evidence/{binding,gate,supersession,render}`, `apps/portal/**`, `registry/supersessions/*.json`, `tools/gates/*`.

---

## E12 — Bitemporal migration

**Issues:** #19 (Stage 1, in E5) #35 #36 #37 #38 · **Milestones:** M3, M8 · **ADRs:** 0004, 0022, 0027 · **HIGH RISK**

**1. Purpose.** Execute ADR-0027's five stages without fabricating provenance and without an irreversible step before validation.

**2. Scope.** Stage 1 dual write (delivered in E5 #19); Stages 2–5 shadow, validate, cutover, decommission.

**3. Responsibilities.** Run both paths; compare; validate; cut over; rehearse rollback; decommission only after a full cycle.

**4. Public interfaces.** `shadow_compare(evaluation_set) -> DivergenceReport` · `cutover(release) -> Supersession`.

**5. Internal modules.** `shadow`, `compare`, `cutover`, `rollback`.

**6. Input contracts.** Legacy path outputs; bitemporal path outputs.

**7. Output contracts.** `DivergenceReport` (field-level, with run IDs); a `DEPRECATION` supersession at cutover.

**8. Failure modes.** Any non-zero divergence **halts the migration** and opens a defect. Divergence is never tolerated or explained away — both paths compute the same thing over the same data.

**9. State transitions.**

```
S1 dual_write ──▶ S2 shadow ──▶ S3 validate ──▶ S4 cutover ──▶ S5 decommission
      │              │              │                │
   rollback:      rollback:      rollback:        rollback:        (none —
   ignore col.    disable        remain on        re-point to      after one
   (additive)     shadow         legacy path      prior digest     full cycle)
```

**10. Validation rules.** **Exit criterion for S3: zero divergence across all published evaluations for three consecutive full runs at class `EXACT`.** S5 may begin only after one full acquisition cycle with no rollback.

**11. Invariants.** *(i)* **No backfill. Historical `ingest_time` remains NULL** (ADR-0022). *(ii)* Rollback through S4 is a configuration change, not a restore — the prior release is immutable and still present. *(iii)* Rollback is rehearsed **before** cutover is declared complete.

**12. Performance.** Shadow doubles evaluation cost. Acceptable and time-boxed.

**13. Security.** None beyond inherited.

**14. Logging.** Every divergence with run IDs, field path, both values.

**15. Error handling.** Halt on divergence. No auto-retry, no tolerance widening.

**16. Test requirements.** Integration: rollback rehearsal at S4 must succeed before cutover is declared. Property: no code path backfills `ingest_time`.

**17. CI requirements.** The S3 criterion is a CI-checkable report artifact.

**18. Acceptance criteria.** Zero divergence for three consecutive runs at `EXACT`; new release published; figures re-derived; evidence gate green; prior release marked `DEPRECATION`; rollback rehearsed; legacy path removed only after a full cycle.

**19. Example execution flow.** See state machine §16.3.

**20. Files.** `contexts/evaluation/migration/{shadow,compare,cutover,rollback}`, `tools/gates/divergence`.

---

## E13 — Continuous evaluation (GATED)

**Issues:** #43–#47 · **Milestone:** M10 · **ADRs:** 0014, 0003

**Status: NOT SPECIFIED.**

Engineering Plan v1.0 states: *"Issues elaborated at milestone entry, not before — specifying them now would fabricate precision about a system whose consumer is undefined."*

Writing a twenty-section specification for a gated epic would contradict the frozen plan and manufacture detail this project has no basis for. **Entry gate: a named consumer exists** (ADR-0001 non-goals). Until then this section remains deliberately empty.

Interfaces it will inherit unchanged when opened: `SourceAdapter` (E5), evaluation engine (E10), provenance kernel (E3). No new abstraction is anticipated — a live source is a registration, not a redesign (ADR-0003).

---

## E14 — CI gates & architecture enforcement

**Issues:** #5 #6 · **Milestone:** M0 (active throughout) · **ADRs:** 0020, all standards

**1. Purpose.** Make every standard mechanical. A standard depending on human discipline is a preference.

**2. Scope.** Gate programs; architecture tests; workflow configuration.

**3. Responsibilities.** Run every gate on every PR and every push to main, with **no path filters**.

**4. Public interfaces.** Each gate is a program returning non-zero on violation with a machine-readable report.

**5. Internal modules.** One module per gate in `tools/gates/`.

**6. Input contracts.** Repository tree; build output; registries.

**7. Output contracts.** Gate reports (JSON), suitable as CI artifacts.

**8. Failure modes.** A gate that does not run is a **failure**, not a pass (ADR-0020). This is the single most important behaviour in the epic — the legacy repository lost 188 tests to a silently-skipping gate.

**9. State transitions.** N/A.

**10. Validation rules.** Full gate table at TIS §16.5.

**11. Invariants.** *(i)* No path filters on any required workflow. *(ii)* Every gate has a deliberate-violation test proving it fails when it should. *(iii)* Real-data tests skip, never fail, in a clean export.

**12. Performance.** Full gate suite must remain within a few minutes; currently well under.

**13. Security.** Secret scanning; no gate may echo a secret into a report.

**14. Logging.** Reports enumerate what was checked, not only what failed — a gate that reports only failures cannot be distinguished from a gate that did not run.

**15. Error handling.** Fail closed, always.

**16. Test requirements.** Every gate has a deliberate-violation test.

**17. CI requirements.** Branch protection requires every gate; `enforce_admins` on.

**18. Acceptance criteria.** A PR touching only `adr/` reports every required check; a deliberate architecture violation fails CI; clean-export shows real-data tests skipping.

**19. Example execution flow.** PR opened → all gates run regardless of touched paths → any failure blocks merge → merge button disabled.

**20. Files.** `tools/gates/*`, `tests/architecture/*`, `.github/workflows/*`.

---

## §15 Master issue table

Ownership is `@maintainer` throughout (bus factor 1, accepted risk). LOC estimates are **approximate and carry no schedule meaning** — the ARB noted effort estimates as the weakest part of prior planning.

| # | Order | Epic | LOC | Cx | Depends on | Unit | Property | Integration |
|---|---|---|---|---|---|---|---|---|
| 1 | 1 | E1 | 0 | M | — | — | — | link gate |
| 2 | 2 | E1 | 0 | S | 1 | — | — | dir-name test |
| 3 | 3 | E1 | 0 | M | 2 | — | — | citation gate |
| 4 | 4 | E1 | 0 | S | 3 | — | — | — |
| 5 | 5 | E14 | 150 | M | 2 | — | — | no-path-filter test |
| 6 | 6 | E14 | 250 | M | 2,5 | harness | — | self-violation |
| 7 | 7 | E2 | 0 | S | — | — | — | tag restore |
| 8 | 8 | E2 | 0 | M | 3 | — | — | — |
| 9 | 9 | E2 | −22,900 | L | 7,8 | — | — | full CI + clean export |
| 10 | 10 | E3 | 400 | M | 2,6 | digest, DAG, cycles | digest stability | — |
| 11 | 11 | E4 | 600 | L | 10 | schema validity | round-trip | additive-diff gate |
| 12 | 12 | E4 | 900 | L | 11 | entities (no mocks) | all invariants | — |
| 13 | 13 | E4 | 300 | M | 6,12 | — | — | 6 violation tests |
| 14 | 14 | E4 | 250 | M | 11 | manifest validity | — | — |
| 15 | 15 | E5 | 200 | M | 11 | contract conformance | — | credential-boundary |
| 16 | 16 | E5 | 700 | L | 15 | descriptor | — | fixture acquire |
| 17 | 17 | E5 | 900 | L | 15,12 | per-field vs spec | no imputation | parse fixtures |
| 18 | 18 | E5 | 900 | L | 17 | per-field vs spec | no imputation | parse fixtures |
| **19** | **19** | **E5/E12** | **400** | **L** | **17,18,14** | write path | **both times present; no backfill** | **dual-write** |
| 20 | 20 | E6 | 500 | L | 19,10 | digest rollup | — | re-freeze rejected |
| 21 | 21 | E6 | 400 | M | 20,14 | — | — | Zenodo sandbox + fallback |
| 22 | 22 | E6 | 300 | M | 14 | classification | referenced never pruned | dry-run |
| 23 | 23 | E7 | 450 | L | 14,10 | parsing | — | revision → 2 releases |
| 24 | 24 | E7 | 250 | M | 23 | boundaries | determinism | — |
| 25 | 25 | E8 | 400 | L | 11,14 | — | — | prose migration |
| 26 | 26 | E8 | 300 | M | 14 | digest sensitivity | capture stability | — |
| 27 | 27 | E9 | 450 | L | 14,10 | round-trip | — | retrieve + re-instantiate |
| 28 | 28 | E9 | 300 | M | 11,27 | — | — | conformance all methods |
| 29 | 29 | E9 | 800 | L | 27,28 | — | identical predictions | 8 methods |
| **30** | **30** | **E10** | **1,200** | **XL** | **25,26,27,20,23** | metrics | **identical → identical** | **env digest → new identity** |
| 31 | 31 | E10 | 250 | M | 30,26 | class assignment | — | cross-platform (or documented unexercised) |
| 32 | 32 | E10 | 400 | L | 30,19 | both modes | **no future-ingested obs** | — |
| 33 | 33 | E10 | 250 | M | 30,27,25 | subset check | — | **v1 regression** |
| 34 | 34 | E10 | 600 | L | 30 | metrics, bootstrap | no Score without Interval | — |
| 35 | 35 | E12 | 400 | L | 30,19 | — | — | shadow + disable |
| 36 | 36 | E12 | 200 | M | 35 | — | — | 3× zero divergence |
| 37 | 37 | E12 | 350 | L | 36,39 | — | — | **rollback rehearsal** |
| 38 | 38 | E12 | 150 | M | 37 | — | — | full CI + clean export |
| 39 | 39 | E11 | 300 | M | 12,14 | record | no mutation | — |
| 40 | 40 | E11 | 400 | L | 39,41 | — | — | **retraction 3 hops fails** |
| 41 | 41 | E11 | 600 | L | 10,30 | binding | — | drift fails; literal fails |
| 42 | 42 | E11 | 900 | L | 41 | — | — | budget, links, age gates |

**Totals:** ~17,500 LOC added, ~22,900 removed. Net **≈ −5,400**.

---

## §16 Diagrams

### 16.1 Observation lifecycle (E5)

```
Adapter          Kernel           Parser          Store
   │                │                │              │
   ├─ acquire ─────▶│                │              │
   │                ├─ digest(raw)   │              │
   │◀─ digest ──────┤                │              │
   ├─ verify ───────┤                │              │
   │   ✗ ─────────────────────────────────────────▶ ABORT (IntegrityFailure)
   ├─ stamp ingest_time (clock read — §0.4 exception)
   ├─ parse ───────────────────────▶│              │
   │                │                ├─ grid, GTI, missingness preserved
   │                │                ├─ ✗ ────────▶ ABORT (ContractViolation)
   │                │◀─ observations ┤              │
   │                ├─ record(run,[raw],[obs])      │
   │                │                │              │
   ├─ write (valid_time + ingest_time) ───────────▶│
```

### 16.2 Evaluation (E10)

```
Caller      Engine      InstrGate   LeakGate    Method     Scoring
  │           │             │           │          │          │
  ├─evaluate─▶│             │           │          │          │
  │           ├─pin 5 digests           │          │          │
  │           ├────────────▶│           │          │          │
  │           │   declared ⊆ permitted? │          │          │
  │           │◀─ ✗ PolicyRejection ────┤          │          │
  │           ├────────────────────────▶│          │          │
  │           │   requires_bitemporal?  │          │          │
  │           │   drop ingest_time NULL │          │          │
  │           │   reject ingest_time>as_of         │          │
  │           ├───────────────────────────────────▶│  (wire)  │
  │           │◀────────────── predictions ────────┤          │
  │           ├──────────────────────────────────────────────▶│
  │           │◀───────── Scores + Intervals ─────────────────┤
  │           ├─ classify: EXACT | EQUIVALENT | UNREPRODUCIBLE
  │           ├─ UNREPRODUCIBLE ─────────────────────▶ REFUSE
  │◀─Evaluation
```

### 16.3 Bitemporal migration state machine (E12)

```
        ┌────────────┐  additive schema, dual write
        │ S1 DUAL    │  historical ingest_time = NULL
        └─────┬──────┘  rollback: ignore column
              ▼
        ┌────────────┐  both paths run, nothing published
        │ S2 SHADOW  │  rollback: disable shadow
        └─────┬──────┘
              ▼
        ┌────────────┐  zero divergence × 3 runs @ EXACT
        │ S3 VALIDATE│  divergence → HALT + defect
        └─────┬──────┘  rollback: stay on legacy (no deadline)
              ▼
        ┌────────────┐  new release; figures re-derived
        │ S4 CUTOVER │  prior release → DEPRECATION
        └─────┬──────┘  rollback: re-point to prior digest
              ▼          (rehearsed BEFORE completion)
        ┌────────────┐  after one full acquisition cycle
        │ S5 DECOMM  │  rollback: NONE
        └────────────┘
```

### 16.4 File responsibility

```
adr/          decisions          immutable once accepted
standards/    enforced rules     mechanical
contracts/    vocabulary         normative, additive-only
domain/       invariants         stdlib only, no mocks
kernel/       digests, lineage   imports NOTHING
contexts/     six contexts       no cross-internal imports
registry/     Tier 2 manifests   git is the system of record
apps/portal/  rendering only     zero JS on evidence routes
specs/        governing prose    cited by ID, never restated
tools/gates/  enforcement        every gate has a violation test
```

### 16.5 CI gate table

| Gate | Fails on | ADR/STD |
|---|---|---|
| `contracts` | non-additive schema change within a major | STD-09 |
| `architecture` | import-direction or forbidden-name violation | 0026 |
| `unit` / `property` | any failure | — |
| `clean-export` | build fails, or a real-data test fails instead of skipping | STD-12 |
| `evidence` | rendered value diverges; literal in template | 0012, STD-05 |
| `supersession` | `RETRACTION` in a claim's provenance DAG | 0024 |
| `budget` | route byte budget exceeded | 0015 |
| `links` | unresolved internal href or citation | E1 |
| `lexicon` | vocabulary implying live operation | 0001 |
| `age` | surface implies currency without displaying data age | STD-17 |
| `retention` | referenced artifact scheduled for pruning | STD-24 |
| `divergence` | S3 criterion not met | 0027 |

---

## §17 Explicit gaps — Not defined by Architecture Freeze v1.0

1. Implementation language and runtime (§0.1).
2. Concurrency model within a context.
3. Latency and throughput budgets (STD-20 forbids inventing them).
4. NOAA authentication, should it ever be introduced (E7 §13).
5. Cross-platform reproduction tolerance values — per-protocol, set at protocol registration (E8).
6. Sandbox resource limits — ADR-0016 infrastructure deferred by ARB to AR-2 (E9 §2).
7. Zenodo community/licence selection for deposition.

These must not be resolved by an implementer acting alone. Each requires either a protocol-level decision or an ADR.
