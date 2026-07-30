# Contract conventions

Normative JSON Schema. Per [ADR-0019](../adr/ADR-0019.md) these schemas are the source of
truth and language types are hand-written and validated against them.

## Identifier and version

Every schema carries a `$id` of the form `urn:adityanet:contract:<name>:<major>`.

A URN rather than an `https://` URL, deliberately: an `https://` `$id` implies a resolvable
endpoint, this project serves no such endpoint, and [ADR-0001](../adr/ADR-0001.md) forbids
implying capability the platform does not have. The URN is a stable name, not an address.

The major version is part of the identifier because a breaking change produces a *different*
contract, not a new revision of the same one ([STD-09](../standards/STD-09.md)).

## Closed by default

Every object sets `additionalProperties: false`. An unrecognised field is a defect, not a
harmless extra: silently accepting one is how a producer and a consumer come to disagree
about a payload while both believe they are conforming. No schema in this set permits
extension; if one ever must, it will say so explicitly and say why.

## Content addressing

[ADR-0005](../adr/ADR-0005.md): every immutable object is identified by the SHA-256 of its
content. The `digest` definition is `^[0-9a-f]{64}$` — lower-case hex, fixed length —
reused everywhere rather than restated, so the constraint cannot drift between contracts.

## Conditional requirements

`manifest.schema.json` is the first contract whose required fields depend on one of its own
values, and it uses `if`/`then` rather than a looser schema plus a documented rule.

The reason is [ADR-0023](../adr/ADR-0023.md). Tier 0 bytes are referenced and **never**
redistributed; Tier 1 bytes are deposited externally; Tier 2 bytes live in git. Each tier
therefore requires a different locator and must forbid the others. Expressed as a convention,
"a Tier 0 manifest must not carry a deposition" is a sentence someone has to read. Expressed
as `if tier = 0 then not deposition`, a manifest that would redistribute another
organisation's raw archive **cannot be written**, and no reviewer has to notice.

The same applies to retention ([STD-24](../standards/STD-24.md)): a `prunable` entry with a
non-empty `referenced_by` is the one combination that would let a published claim lose the
bytes underneath it, so the contract makes it unrepresentable rather than merely discouraged.

## Missing versus absent

`null` and "field not present" are different, and the difference is load-bearing.
[ADR-0017](../adr/ADR-0017.md) forbids imputing a missing measurement, so `value` is
nullable and `null` means *observed to be absent*. [ADR-0022](../adr/ADR-0022.md) gives
`ingest_time = null` exactly one meaning: *unknown — predates bitemporal capture*. Neither
is ever fabricated, and neither is expressed by omitting the field.
