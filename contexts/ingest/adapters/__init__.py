"""Source adapters — one per acquisition channel.

One channel exists: `issdc_pradan`. There is no registry, no dispatch table and no lookup by
`source_id` here, and there will not be one until a second channel exists. ADR-0003 states
that explicitly — it *"does not authorise a source-plugin registry, a dispatch layer, or a
configurable adapter framework"* — and ADR-0025 classifies all three as paid abstractions,
forbidden at N=1. A caller constructs the adapter it wants.

The directory exists rather than the module sitting flat because E5 §20 names the path
`contexts/ingest/adapters/issdc_pradan/*`, and because a second channel is a new directory
beside this one rather than a change to anything in it.
"""
