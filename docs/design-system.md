# Design system

The visual language exists to serve one goal: let a visitor understand each section in
seconds and let a reviewer verify every claim. This document covers the tokens, the
typographic voice, the editorial split, and the motion model. The full creative constitution
is [`web/EXPERIENCE_BIBLE.md`](web/EXPERIENCE_BIBLE.md).

## Tokens — one source, checked in CI

Colour and type are defined in `web/tokens/*.json` and emitted by `generate.ts` into both
CSS custom properties and Tailwind config. CI asserts the generated files are current, so
the two representations cannot diverge ([ADR‑0004](adr/0004-generated-design-tokens.md)).

- **Surface** — near‑black canvas (`#06080a`), layered surfaces for depth.
- **Accent** — a single restrained periwinkle eyebrow colour, promoted to a token so every
  surface speaks it.
- **Data** — viridis for quantitative encoding (perceptually uniform, colour‑blind safe).
- **Contrast** — body text ≥ **7:1** (WCAG AAA), enforced against these tokens in the budget
  gate. A token change that drops text below the floor fails the build.

## Typography

Two families, self‑hosted via Fontsource (subset `woff2`, no font CDN):

- **IBM Plex Sans** — interface and display. Light weights for headlines; the display scale
  is fluid (`clamp`) so it is *composed*, not merely scaled, at every viewport.
- **IBM Plex Mono** — measurements, labels, digests, watermarks. Tabular figures so digits
  align and do not reflow as they animate.

The distinction is epistemic: **sans = interface, mono = measurement**.

## The editorial split — story vs documentation

Every evidence area is two surfaces:

| | Story surface | Documentation surface |
| --- | --- | --- |
| Example | `/findings` | `/findings/method` |
| Job | Understand in seconds | Verify in full |
| Content | One verdict, one sentence, a few visual elements | Full tables, verbatim protocol |
| Words | ~150–270 | ~800–1400 |

A visitor gets the finding without reading paragraphs; a reviewer clicks through to the
complete record. Neither compromises the other. The rule applied throughout: **if a
paragraph can be shown visually, show it** — the goal is *less reading, not fewer words*.

## Two registers, never confused

- **Artistic** — real solar footage. Always carries `ILLUSTRATIVE · NASA / SVS · NOT
  ADITYA‑L1 DATA`. May be beautiful; claims nothing.
- **Measured** — traceable values. Carries **no** decorative post‑processing, because an
  effect on a measurement would be a visual lie about its provenance. Restraint is the
  signal of confidence.

The negative result is *shown, not argued*: on `/findings`, each model's 95% confidence
interval is drawn as a band on a shared axis, so the overlap that produces the "no gain"
verdict is legible before the caption is read. The point estimates and intervals are printed
beside every bar, so the graphic remains truthful for a screen‑reader user who receives only
the text.

## Motion

All scroll choreography on evidence surfaces is **CSS‑only** (`animation-timeline`), so it
costs zero JavaScript and degrades to "simply visible" where unsupported.

- **Reveal** — sections rise and settle on entry; the end state is held so nothing flickers.
- **Flow** — a single timeline across an element's whole pass through the viewport, so one
  section releases as the next takes over rather than stopping dead. The exit never reaches
  zero opacity — content a visitor may still be reading must not vanish.
- **Reduced motion** — under `prefers-reduced-motion: reduce`, travel is removed and only
  state changes remain; the ambient footage is replaced by its poster.

## Responsive

Breakpoints are designed, not derived from shrinking. Navigation becomes a zero‑JavaScript
disclosure menu on narrow screens; the hero recomposes (footage above, copy on clean canvas
below) rather than overlapping. Verified across 320 → 1920 px, with distinct handling for
landscape phones and ultrawide displays. Touch targets meet the 44 px floor (WCAG 2.5.5).

## Reproducible documentation imagery

Screenshots in the README are captured from the production build at fixed device profiles by
`web/scripts/screenshots.mjs`, so the documentation imagery is regenerable rather than
hand‑cropped and can be kept current as the site evolves.
