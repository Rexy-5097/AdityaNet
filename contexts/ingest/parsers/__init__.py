"""Instrument parsers — canonicalise an acquired product into domain objects.

`parsers/solexs` is delivered by M3/E5/#17. `parsers/hel1os` is #18 and does not exist yet.

Acquisition and canonicalisation are one context with two internal module groups (ADR-0026),
with the seam preserved as directory boundaries because it is free under ADR-0025. There is
no parser registry and no dispatch: a caller selects the module for the product it holds.
"""
