---
id: STD-07
title: Gates fail closed
status: active
verification: INTG
---

# STD-07 — Gates fail closed

A gate that cannot execute fails; it never passes by default. Required checks carry no path
filters. Every gate has a deliberate-violation test ([ADR-0020](../adr/ADR-0020.md)).
