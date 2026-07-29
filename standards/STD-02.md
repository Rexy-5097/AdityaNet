---
id: STD-02
title: Content addressing
status: active
verification: PROP
---

# STD-02 — Content addressing

Every immutable object is identified by the SHA-256 digest of its content
([ADR-0005](../adr/ADR-0005.md)). Sequential and timestamp identifiers are forbidden for
immutables.

**Enforcement:** identifier-format gate; digest-stability property test.
