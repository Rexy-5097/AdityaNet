---
id: SALVAGE-003
title: The versioned operator policy system — integrity design under a proven leak
status: active
supersedes: []
superseded_by: null
origin: salvaged
source_tag: v1-surya-final
source_paths: research/app/services/ml/policy.py
source_loc: 446
---

# SALVAGE-003 — The versioned operator policy system

> **Provenance.** Design knowledge extracted from the v1 generation before its removal by
> M1/E2/#9. The implementation is recoverable at tag `v1-surya-final`:
>
> ```
> git show v1-surya-final:research/app/services/ml/policy.py
> ```
>
> **This document contains no code and mandates nothing.** Binding decisions live in `adr/`.

## Context: this was written in response to a proven leak

An earlier generation stored operator thresholds in a single mutable JSON file. That file
was **proven** to have been generated from the test split — not suspected, proven, by
matching a dataset fingerprint (N = 1,806,313 rows, 419,150 positives) against the test
split's identity and by reproducing the reported metrics exactly.

The policy system was the response. It is the most defensively-designed component in the v1
generation, and it was designed that way because something had already gone wrong. That is
the right order of events, and it is worth recording that the project has form here.

## Design decisions that were right

**Defend against the failure, not against its spelling.** The leak was established by
fingerprint, so fingerprint verification became the load-bearing defence. The author states
this explicitly: *the defence is fingerprint verification, not string matching.* Name-based
checks catch the case you already know about; identity checks catch the class.

**Refuse to load rather than warn.** No policy loaded without complete provenance metadata,
a valid self-hash, and a passing leakage guard. There was no permissive mode, no warning
path, no override flag. This is [STD-07](../../standards/STD-07.md) and
[ADR-0020](../../adr/ADR-0020.md) applied to an artifact rather than to a build.

**A self-hash carried inside the artifact.** The policy verified its own integrity on load.
Tampering was detected at the point of use rather than at some later audit — the same
property the provenance kernel gives every record ([ADR-0005](../../adr/ADR-0005.md)).

**Verify a vector of identities, not one.** Startup checked dataset fingerprint, split
identity, generator version, schema version and scientific version, and aborted loudly on
any single failure. A policy that is valid against four of five is not valid.

**Banned tokens for the known-bad generator chain.** The specific artifacts that produced
the leak were named and forbidden in any policy generator's source. This is narrower than
the fingerprint defence and was correctly treated as *supplementary* to it rather than as
the primary control.

**Stdlib-only, deliberately.** The module avoided the ML runtime entirely so the integrity
layer could be tested without it. The component that decides whether an artifact is
trustworthy should not require the heaviest dependency in the system to run. This is the
same reasoning that keeps `kernel/provenance` free of third-party imports
([ADR-0026](../../adr/ADR-0026.md), TIS E3 §11) and the links gate free of any imports at
all.

## What the frozen architecture does differently

| v1 | Frozen architecture |
|---|---|
| Policy artifact verifies itself on load | Every immutable object is content-addressed; the store verifies on read ([ADR-0005](../../adr/ADR-0005.md), [ADR-0006](../../adr/ADR-0006.md)) |
| Dataset fingerprint as an ad-hoc identity | DatasetRelease digest is *the* identity, pinned into every Evaluation ([ADR-0021](../../adr/ADR-0021.md)) |
| Five version fields checked at startup | Five digest-addressed inputs pinned per Evaluation ([ADR-0021](../../adr/ADR-0021.md)) |
| Leakage guard over a threshold artifact | Leakage gate over observation availability, declared per Protocol ([ADR-0022](../../adr/ADR-0022.md)) |
| Thresholds are an operational artifact | The threshold detector is a MethodRelease, scored like any other ([ADR-0010](../../adr/ADR-0010.md)) |

The through-line: v1 bolted integrity onto one artifact after that artifact caused a
problem. The frozen architecture makes integrity the property of *every* artifact by
construction, so there is no second artifact waiting to cause the next one.

## What must not be carried forward

The thresholds themselves, and any policy generated before the leak was closed. They were
fitted on data whose split identity is exactly what was in question. The
*integrity machinery* is the salvage; its contents are not.
