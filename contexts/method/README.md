# `contexts/method`

**Register and invoke detection methods.**

## Responsibility

MethodRelease registry, declared instrument requirements, and the serialised execution
wire format. A method is any detector, including a threshold — not only a model.

## What may not enter

- Any access to test-period label releases. Execution uses a filtered view.
- A MethodRelease without declared instrument requirements.
- Invocation that bypasses the wire format, including for first-party methods.

## Governing decisions

[ADR-0010](../../adr/ADR-0010.md) · [ADR-0011](../../adr/ADR-0011.md) · [ADR-0016](../../adr/ADR-0016.md)
