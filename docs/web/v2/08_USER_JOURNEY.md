# 8 · User Journey

## 8.1 The three visitors

Design for all three. They want incompatible things, and the architecture must not force a
compromise that fails any of them.

| | **The Curious** | **The Sceptic** | **The Reviewer** |
|---|---|---|---|
| Who | Arrived from a link, no domain knowledge | A scientist who distrusts pretty science sites | Assessing rigour, provenance, or the engineering |
| Wants | To feel something, then understand | Evidence, immediately. Suspicious of cinematics | Method, artefacts, hashes, failure log |
| Entry | `/` top, scrolls the arc | `/` → **skip to evidence** in one keystroke | `/findings`, `/validation`, `/build` directly |
| Success | Reaches the number and *cares* | Verifies a claim without watching one frame | Can trace any number to an artefact + hash |
| Failure | Bounces before the pivot | Concludes it's style over substance | Finds an unsourced claim |

> **The Sceptic is the primary user.** AdityaNet's thesis is that it caught itself running
> on synthetic data and published a negative result. If a sceptic cannot verify that in
> seconds, the cinematics are decoration and the project has failed. **"Skip to evidence" is
> the first focusable element on the page.**

## 8.2 The main arc — `/`

| Beat | `t` | What the visitor sees | What they should feel | Register |
|---|---|---|---|---|
| **Arrival** | 0.00 | The Sun fills the frame. Real SDO footage. Watermarked `ILLUSTRATIVE · SDO / NASA · NOT ADITYA-L1 DATA` | Awe — and immediately, that someone is being careful with them | A |
| **Scale** | 0.12 | A tiny craft enters against an enormous Sun | Perspective. *That* is what we sent | A |
| **Attention** | 0.22 | Rack focus: Sun softens, craft sharpens | The subject just changed | A→S |
| **Structure** | 0.30 | The craft opens. Seven payloads light in sequence | Curiosity — *what are all of these?* | S |
| **Hold** | 0.46 | Everything stops. Seven lit payloads, 400 ms of stillness | Anticipation | S |
| **Focus** | 0.54 | Six fade. SoLEXS remains, outlined, named | *This is the one this project is about* | S |
| **The Crossing** | 0.60–0.72 | One photon travels to the detector. Nothing else moves | Inevitability | S |
| **Collapse** | 0.72–0.82 | Geometry contracts to a point | Compression — all that, to this | S→B |
| **The Number** | 0.86 | `112.98` resolves. Watermark flips to `MEASURED · T1 solexs_lc_1min · 43fd0e22` | *That's real. That's an actual measurement* | B |
| **The Curve** | 0.90–1.00 | A light curve draws — real 2024-05-14, X8.7 flare | Context. One number becomes a day | B |
| **The Turn** | end | "The machine learning did not help." → `/findings` | Respect. They told me the unflattering result | B |

**The emotional arc is: awe → curiosity → focus → inevitability → verification → trust.**
Trust is the product. Everything before it exists to make the visitor care enough to check.

## 8.3 The pivot moment

`t ≈ 0.82–0.86` is the entire site. Everything before earns it; everything after cashes it.

Design requirements for that instant:
- **Nothing moves except the number resolving.** No camera, no effects, no supporting motion.
- The canvas is **gone**, not faded behind — the measurement is not decorated.
- The watermark change is **legible and simultaneous** — provenance arrives with the value.
- The number uses tabular figures so digits do not reflow.
- It is **immediately traceable**: one click reveals artefact, JSON pointer, hash.

If a visitor screenshots one frame of this site, it should be this one — and the screenshot
should contain enough provenance to be checked by a stranger.

## 8.4 The sceptic's path

```
Land on /  →  Tab (first stop: "Skip to evidence")  →  /findings
   → negative ML result, stated plainly, no hedging
   → artefact hash + JSON pointer on every number
   → /validation: how the synthetic-data failure was caught
   → /build: the issue log, including the mistakes
```

**Total cinematics consumed: zero.** Time to first verifiable claim: seconds.

The `/validation` surface is the project's credibility keystone — it documents that v1's
entire Aditya-L1 archive was mock/simulated, that only 10 real ISSDC days existed, and that
all v1 results were voided. A project that publishes its own worst finding earns the right
to be believed about everything else.

## 8.5 Cross-surface continuity

Astro native View Transitions carry the descent between surfaces. The depth gauge (from v1,
retained) shows how far into the evidence the visitor has travelled — the connective tissue
already built and validated.

Every evidence surface offers a return path to the moment in the arc that motivated it, via
`?t=` — e.g. `/findings` links back to `/?t=0.86`, the number itself.

## 8.6 Journey failure modes

| Risk | Mitigation |
|---|---|
| Bounce before the pivot | Arc is ~14 s at full scroll; chapter nav lets anyone jump straight to the crossing |
| Cinematics read as overclaiming | Watermarks are present from frame one, never below 0.5 opacity |
| Sceptic dismisses as style | Skip-to-evidence is the first focusable element |
| Motion-sensitive visitor | Full reduced-motion path; on-page toggle independent of OS setting |
| Slow connection | Still frame, no video; full story preserved |
| Visitor never reaches findings | The arc's final beat *is* the handoff to the negative result |

## 8.7 The one-sentence test

> A visitor should leave able to say: **"They showed me something beautiful, then showed me
> it wasn't data, then showed me what the real data actually said — including that their own
> method didn't work."**

If any design decision weakens that sentence, it is wrong regardless of how good it looks.
