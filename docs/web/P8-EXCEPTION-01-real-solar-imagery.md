<!-- VERSION STATUS: ACTIVE -->
<!-- REASON: Formal record of an owner-approved exception to P8. -->
<!-- DATE: 2026-07-23 -->

# P8 Exception 01 — Real solar imagery in the hero

**Status:** ACTIVE · owner-approved 2026-07-23 · applies to the Crossing hero (M1 onward)

## The principle being excepted

P8 / the Experience Bible hold that the platform must never present another mission's
observations as its own, and that Register A (artistic) makes no factual claim. Using a
real photograph of the Sun in the hero brushes against both: it is a factual image, and
it comes from a *different* mission's imaging instruments. Aditya-L1's SoLEXS is a
non-imaging photometer and records no image at all.

## The decision

After the owner reviewed a full comparison (procedural stylised sun, licensed CGI
texture, real telescope imagery) and the stated cost of each, the owner chose **real
solar imagery**, accepting the honesty tradeoff. This document is the formal record
promised at the time of that decision.

## What makes the excepted use honest anyway

The exception is bounded by one hard rule that preserves the project's integrity:

> **Real imagery is labelled, in-frame, as exactly what it is.**

- **Source:** NASA Solar Dynamics Observatory (SDO), AIA 171 Å. Public domain (NASA
  media guidelines). File committed at `prototype/crossing/public/latest_1024_0171.jpg`.
  An HMI continuum white-light frame is also available (`latest_1024_HMIIC.jpg`).
- **Watermark, burned into the frame:** `ILLUSTRATIVE · SDO / NASA · NOT ADITYA-L1 DATA`,
  and during the drain `SCHEMATIC · NOT TO SCALE · SDO / NASA`.
- **The Crossing makes the distinction its point.** The image is illustrative context;
  the pivot then reveals that Aditya-L1's actual record is not this image at all — it is
  one number. The narrative *is* "other missions see this; ours is blind and measures
  that." Properly labelled, the real image strengthens rather than undermines the claim.

This is the documentary standard: crediting stock footage is honest; passing it off as
your own is not. The label is the whole difference.

## What is still forbidden

- The SDO image may **never** appear without its attribution watermark.
- It may **never** be described, captioned, or implied to be Aditya-L1 data or a SoLEXS
  observation.
- It may **never** be shown transforming into a measured value *without* the watermark
  first having stated it is illustrative SDO imagery — the ordering matters, so the
  viewer knows it was context before the real measurement appears.
- No claim of scale, resolution, or simultaneity with the archive.

## Review

If the platform is ever presented to ISRO or a scientific reviewer, this exception is
the first thing to disclose. It is defensible as labelled illustration; it is
indefensible if the label is ever dropped. Any implementation that removes the
attribution watermark is a regression and must fail review.
