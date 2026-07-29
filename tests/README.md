# `tests`

**Cross-context, property and architecture tests.**

## Responsibility

Tests spanning more than one context, plus the executable assertions that enforce the
architecture itself. Unit tests live beside the code they test.

## What may not enter

- Unit tests for a single module. Those live with their context.
- Any test that fails rather than skips when the real archive is absent.

## Governing decisions

[STD-12](../standards/STD-12.md)
