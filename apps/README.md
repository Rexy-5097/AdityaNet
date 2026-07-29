# `apps`

**Deployable surfaces.**

## Responsibility

Applications that are built and deployed. Everything else in this repository is a
library, a context, or a tool.

## What may not enter

- Business logic. Applications compose contexts; they do not implement them.
- A live surface sharing a deployment with a static evidence surface.

## Governing decisions

[ADR-0015](../adr/ADR-0015.md)
