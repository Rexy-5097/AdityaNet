# 1 · Visual Direction

## 1.1 The thesis in one line

**A measurement is more beautiful than a rendering — but only if you earn the right to show it.**

The site spends its first thirty seconds being genuinely cinematic, then deliberately
strips that beauty away to reveal a number. The stripping *is* the product. Anything that
makes the artistic phase look expensive is justified; anything that makes the measured
phase look decorated is a defect.

## 1.2 What "Apple / SpaceX pacing" actually means

Not a visual style — a set of enforceable behaviours. Copying their look is forbidden;
adopting their discipline is the point.

| Principle | Concrete rule in AdityaNet |
|---|---|
| **One idea per viewport** | Each scroll section states exactly one thing. Never two competing focal points |
| **Motion has hierarchy** | At any instant, exactly **one** element is the primary mover. Everything else is static or damped below 20% of its amplitude |
| **Transitions are the product** | Budget more attention on the *between* states than the destination states |
| **Restraint as signal** | Effects are removed as certainty increases. The measured register is nearly bare — that austerity reads as confidence |
| **Nothing moves without cause** | No idle drift, no ambient float, no "alive" wobble. If it moves, the user caused it or the story required it |
| **Type carries the argument** | The most important element on the measured screen is a number in tabular figures, not a graphic |
| **Silence before impact** | A held beat (~400 ms of stillness) precedes each register change. The pause does the work |

## 1.3 The three registers as a visual system

The Bible defines the registers; this fixes their *rendering* treatment. Every column is
produced by stock libraries — no custom shaders anywhere in this table.

| | **A · Artistic** | **S · Schematic** | **B · Measured** |
|---|---|---|---|
| **Claims** | Nothing | Structure | Quantity |
| **Source** | NASA SDO footage | Primitive diagram | Archive artefact + JSON pointer |
| **Palette** | Warm — amber, ember, deep red | Cool — blue-grey wireframe on near-black | Neutral — paper white, viridis for data |
| **Grade (LUT)** | Warm filmic, lifted blacks | Neutral-cool, crushed blacks, high micro-contrast | Linear, no grade |
| **Post FX** | Bloom + DoF + vignette + grain | Grid overlay + outline, **no bloom** | **None** |
| **Depth** | Deep — atmospheric, shallow focus | Flat — orthographic feel, everything sharp | None — 2D DOM |
| **Motion** | Slow, continuous, drifting | Precise, stepped, mechanical | Static; only data draws in |
| **Type** | Sparse, large, light weight | Monospace labels, small, all-caps | Tabular figures, large numerals |
| **Watermark** | `ILLUSTRATIVE · SDO / NASA · NOT ADITYA-L1 DATA` | `SCHEMATIC · NOT TO SCALE` | `MEASURED · <artifact> · <hash>` |

**The transition is the site.** A→S is a *drain*: colour leaves, depth flattens, bloom dies,
grid rises. S→B is a *collapse*: geometry contracts to a point, then a number resolves where
it was. Both are driven by one scalar.

## 1.4 The restraint budget

Hard caps, enforced at review:

- **≤ 3 simultaneous post-processing effects.** The composer merges them into one pass, so
  the cost is bounded — but the *attention* cost is not.
- **≤ 1 primary mover** at any instant.
- **0 effects in Register B.** The measured screen is DOM, unfiltered. This is
  non-negotiable: post-processing a measurement is a visual lie about its provenance.
- **0 idle animation.** No floating, no breathing, no ambient particles.
- **0 effects that imply data.** No glitch, no scanlines-as-decoration, no fake telemetry,
  no HUD chrome, no counters that spin to a value they didn't compute.

> **The dishonesty test.** Before any effect ships, ask: *does this make the image look
> more like data than it is?* If yes, it is rejected regardless of beauty. This test kills
> glitch, datamosh, fake-HUD overlays, and animated "scanning" — the entire visual
> vocabulary of sci-fi UI. AdityaNet exists because it caught itself running on synthetic
> data; it cannot then cosplay as an instrument.

## 1.5 Colour and light

- **Base:** near-black `#06080a` (already in use). Not pure black — retains shadow detail
  and avoids OLED smearing on scroll.
- **Register A warmth** comes from the SDO footage itself, not from lights. We add no
  coloured lighting to the Sun; it is emissive footage.
- **Register S cool** is a single accent `#8fb8ff` on near-black. One accent only.
- **Register B** uses viridis (`d3-scale-chromatic`) for all quantitative encoding —
  perceptually uniform and colour-blind safe, as the Bible requires.
- **Lighting model:** the schematic register is *unlit* (`MeshBasicMaterial`). No PBR, no
  shadows, no ambient occlusion. A diagram is not lit; it is drawn. This is both honest and
  free.

## 1.6 Typography

| Role | Face | Licence |
|---|---|---|
| Interface, prose | **Inter** | SIL OFL 1.1 |
| Numerals, labels, code, watermarks | **IBM Plex Mono** | SIL OFL 1.1 |

Self-hosted, subset, `woff2`, `font-display: swap`. **Never Google Fonts CDN** — a
third-party request on every page load, and a GDPR liability.

Measured values always render in tabular figures (`font-variant-numeric: tabular-nums`) so
digits do not reflow as they animate.

## 1.7 What this direction explicitly forbids

- Procedural suns, coronas, prominences, granulation — **all of it**, permanently
- Photoreal spacecraft with invented internals
- Particle systems used as decoration
- Glitch, datamosh, chromatic-aberration-as-style, fake scanlines, HUD chrome
- Parallax on more than one depth layer at a time
- Any effect on the measured register
- Scroll-jacking that removes user control (Lenis smooths; it must never seize)
