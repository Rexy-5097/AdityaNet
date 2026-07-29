# `specs`

**Versioned prose that governs code.**

## Responsibility

Parser specifications, limitation clauses and contradiction records. These are not
documentation about the code: they are the authority the code implements, cited by
stable identifier and never restated at the point of use. Subdirectories are populated
by the specification-migration issue, which owns specs/**.

## What may not enter

- Restatement of a clause. Cite the identifier instead.
- A specification without a stable citable identifier.
- Explanatory documentation. That belongs in docs/.

## Governing decisions

[ADR-0013](../adr/ADR-0013.md)
