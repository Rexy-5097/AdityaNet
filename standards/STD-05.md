---
id: STD-05
title: No bare numbers in publication
status: active
verification: STAT
---

# STD-05 — No bare numbers in publication

Components that display measured quantities accept a measurement key, never a value
([ADR-0012](../adr/ADR-0012.md)). A numeric literal in a publication template is a defect.

**Enforcement:** template gate scanning rendered prose, excluding class attributes,
expressions, code blocks and standards references.
