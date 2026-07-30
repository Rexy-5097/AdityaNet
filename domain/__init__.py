"""The pure domain model.

Entities, value objects and invariants. Imports the standard library and nothing else — no
third party, no kernel, no context — so every invariant is testable with no fixtures, no
mocks and no infrastructure (ADR-0026, TIS E4 §11(i), §16).

That restriction is not asceticism. TIS E4 §16 states the consequence directly: if a test here
needs a mock, the code under test is in the wrong layer. A domain that can only be exercised
with something stood up around it has already absorbed a dependency it does not admit to.

WHAT THIS PACKAGE DOES NOT DO
-----------------------------
It does not mint digests. ADR-0005 makes `kernel/provenance` the only minting authority, and
the domain cannot import it in any case. `domain.values.Digest` validates the *form* of a
content address so an entity cannot hold something that is not one; the bytes-to-digest step
belongs to the kernel and stays there.

It does not read a clock, the environment, or `random`. TIS §0.4 makes determinism a property
of a pinned input rather than of discipline. `Timestamp` parses; it has no `now()`.

It does not validate against JSON Schema. ADR-0019 makes the schemas normative and these types
hand-written, and validating would require a third-party library. The two are held together by
round-trip tests that serialise an entity and validate the result against its own contract —
which is where a drift between them surfaces.

Public interface (TIS E4 §4): the ten schemas in `contracts/`, plus `domain.invariants.*`.
"""
