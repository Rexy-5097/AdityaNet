<!-- VERSION STATUS: DRAFT — awaiting approval -->
<!-- REASON: Creative constitution for AdityaNet. Every future implementation derives from this. -->
<!-- DATE: 2026-07-23 -->

# THE ADITYANET EXPERIENCE BIBLE

**The creative constitution.** Every future implementation derives from this document.
Where it conflicts with an implementation decision, this document wins — unless
measurable evidence proves a principle wrong, in which case the principle is amended
here first and implemented second.

Companion documents: `PRODUCT_SPECIFICATION.md` (frozen, scientific architecture),
`SPEC_AMENDMENT_02_EXPERIENCE.md` (frozen, technical experience architecture).
This document governs **intent**. Those govern **construction**.

---

# 0 · RESEARCH SYNTHESIS

Principles extracted from work that succeeds. Not aesthetics — mechanisms.

## 0.1 Apple product pages

**Mechanism:** a `position: sticky` canvas driven by scroll *offset*, not scroll *speed*.
One idea per viewport. Text is minimal and arrives after the visual has established
context.

**Principle taken:** *pin the visual, let scroll advance the argument, never touch scroll
velocity.* This resolves an objection raised twice in earlier sprints — scroll-jacking
alters reading speed and is hostile; a pinned canvas does not, and the two were being
conflated.

## 0.2 SpaceX mission pages

**Mechanism:** they do not animate hardware. They animate **consequence** — a trajectory,
a landing profile, a payload deploying. The drama is in what the thing *does*.

**Principle taken:** *the instrument is not the story. What the instrument makes possible
is the story.* AdityaNet's protagonist is not the spacecraft. It is a measurement.

## 0.3 NASA interactive experiences

**Mechanism:** exploration precedes explanation. You fly, arrive, and the explanation
meets you there.

**Principle taken:** *earn the explanation with arrival.* Never open with exposition.

## 0.4 ESA and scientific visualisation

**Mechanism:** uncertainty is drawn, not omitted. Error bars, coverage gaps, and
unknowns appear as first-class visual objects.

**Principle taken:** *absence and doubt are content, not failure states.*

## 0.5 Museum and science-centre exhibit design

**Mechanisms:**
- **Wayfinding** — visitors must always know where they are and what is next.
- **Museum fatigue** — densely packed galleries cause visitors to stop processing
  entirely. Cognitive load is the primary enemy, not lack of content.
- **Linear vs open layouts** — linear arrangements guide a predetermined sequence; open
  arrangements invite self-directed discovery. Each is correct for different content.

**Principle taken, and it is the structural key to this project:**

> **Narrative is linear. Evidence is open.**
>
> The story is a corridor. The evidence is a set of rooms opening off it. A visitor may
> walk the corridor end to end, or enter any room directly and never see the corridor.
> Neither path is the lesser one.

This resolves the central tension: a referee needs to read a contradiction record
carefully and cite it. Making that cinematic would damage the highest-value reader.
Making the *approach* to it cinematic costs them nothing, because they never walk it.

---

# 1 · VISION

## 1.1 What AdityaNet is

**An interactive scientific documentary that carries a visitor from wonder to evidence.**

It takes something no one can verify — a beautiful star — and, without ever breaking
the thread, hands the visitor the command that reproduces every number it showed them.

## 1.2 What AdityaNet is NOT

- Not a portfolio site. Not a dashboard. Not a landing page. Not an ML demo.
- **Not a simulation.** Nothing here pretends to be a live mission.
- **Not a spacecraft flythrough.** There are hundreds. There are zero experiences built
  on an instrument that records no spatial information at all.
- **Not a persuasion device.** Its headline finding is negative.

## 1.3 The emotion that must remain

Not "that was beautiful." Not "that was impressive."

> **"I could check that. And they showed me where they were wrong."**

Awe is the entry fee. Trust is the product.

## 1.4 Why this experience exists

Because the project's own history is the story. AdityaNet ran thirty sprints on
synthetic data before catching itself, voided its own conclusions, rebuilt on the real
archive, tested machine learning honestly, and published that it did not help.

An experience that carries a visitor from an unverifiable impression to a verifiable
digest is not decoration on that history. **It is that history, made walkable.**

---

# 2 · THE CONSTITUTION

Eleven articles. Every future decision obeys them.

### Article I — Motion must communicate
Every animation answers: *what changed, why, and where did it go?* Motion that answers
none of these is decoration and must be deleted.

### Article II — Beauty must never imply evidence
Photorealism is a claim. A representation may be as beautiful as it likes, provided it
never borrows the authority of measurement it has not earned.

### Article III — Every visualisation makes an explicit epistemic claim
There are exactly three claims available: *none* (Artistic), *structural* (Schematic),
*quantitative* (Measured). Every pixel belongs to exactly one, and declares which.

### Article IV — If something is unknown, admit it in the frame
Where internal configuration is not publicly specified, the visualisation says so, at
the point of viewing. An admission of ignorance is a credibility asset, not a gap.

### Article V — Every transition increases certainty
The journey runs Artistic → Schematic → Measured, and never backward within an act. A
visitor must feel the ground getting firmer, not merely the visuals getting denser.

### Article VI — Absence is shown, never filled
Gaps are gaps. No interpolation, no zero-fill, no rounding a partial day up to a whole
one. A gap is a scientific statement.

### Article VII — Uncertainty travels with the estimate
Any quantity with a confidence interval renders that interval, as a figure **and** as
text. Overlap is never left to be judged by eye.

### Article VIII — Evidence is never slower than spectacle
The cinematic layer may never delay access to evidence. Evidence surfaces carry the
strictest performance budgets on the site, and the visitor can always leave the corridor
in one action.

### Article IX — The negative result gets equal weight
The finding that machine learning did not help is presented in the same visual treatment
any positive finding would receive. A layout that de-emphasises an inconvenient result
is dishonest regardless of its text.

### Article X — Nothing implies live operation
No live indicators, no counters, no telemetry styling, no "mission control". The archive
is closed and dated, and every temporal view says so.

### Article XI — The experience must survive its own absence
Remove all JavaScript and the argument still stands, in full, in readable prose. The
cinema is an amplifier, never a carrier.

---

# 3 · THE REGISTER SYSTEM

Three registers. A visitor must be able to identify which one they are looking at
**without reading body text**, and that identification must **survive screenshotting**.

```
   REGISTER A                REGISTER S                REGISTER B
   ARTISTIC        ──→       SCHEMATIC       ──→       MEASURED
   claims nothing            claims structure          claims quantity
   photoreal OK              deliberately flat         flat, viridis, square
   ▓▓▓▓░░░░░░                ▓▓▓▓▓▓▓░░░                ▓▓▓▓▓▓▓▓▓▓
   certainty →                                          certainty →
```

## 3.1 Register A — ARTISTIC

| Property | Definition |
|---|---|
| **Purpose** | Establish wonder. Earn the visitor's attention. |
| **Truth claim** | **None.** Makes no factual assertion of any kind. |
| **Rendering** | Photorealism permitted. HDR, bloom, volumetrics, PBR. |
| **Lighting** | Emissive, physically-inspired, cinematic. |
| **Typography** | Sans, large, sparse. Never tabular. |
| **Palette** | Warm emissive spectrum. Deep red → gold → white-hot. Disjoint from data palette. |
| **Animation** | Continuous, slow, organic. Loops permitted. |
| **Interaction** | ORBIT, APPROACH. Exploratory, no consequences. |
| **Watermark** | `ARTISTIC RENDERING · NOT OBSERVATIONAL DATA` — **rendered into the frame buffer**, not the DOM |
| **Citations** | None required. Inputs may be measured; the rendering claims nothing. |
| **Accessibility** | `role="img"` with full text alternative. Never the sole path to any information. Reduced motion → composed still. |

**Prohibited in A:** any element resembling an instrument readout. No counters, no clocks,
no "LIVE", no scan lines. It may be beautiful; it may not cosplay as a console.

## 3.2 Register S — SCHEMATIC

| Property | Definition |
|---|---|
| **Purpose** | Explain structure. Bridge wonder to evidence. |
| **Truth claim** | **Structural.** "This payload exists." "It faces sunward." Checkable against public documentation. |
| **Rendering** | **Deliberately non-literal.** Wireframe, orthographic, flat-shaded, exploded, annotated. |
| **Lighting** | **None.** No lighting model at all. Flatness is the honesty signal. |
| **Typography** | Mono for labels, sans for annotation. Technical-drawing register. |
| **Palette** | Monochrome line work, single accent for the element under discussion. |
| **Animation** | Mechanical, linear, deliberate. Layers separate; parts do not "float". |
| **Interaction** | INSPECT, ISOLATE. Hovering a component reveals its citation. |
| **Watermark** | `SCHEMATIC · NOT TO SCALE` — in frame buffer |
| **Citations** | **Mandatory.** Every structural label carries a public-documentation source, exactly as every number carries an artifact pointer. |
| **Accessibility** | Full DOM equivalent: an ordered list of components with labels and citations. |

**The rule that makes S honest:** *form announces register.* Photorealism **is** the claim
of literal accuracy. The moment a schematic looks like a photograph it is lying. Wireframe,
flat, annotated — and it can be as elegant as we can make it, because elegance is not a
truth claim.

**Where knowledge ends, the frame says so:**
> *SoLEXS — symbolic representation. Internal configuration not publicly specified.*

## 3.3 Register B — MEASURED

| Property | Definition |
|---|---|
| **Purpose** | Deliver checkable evidence. |
| **Truth claim** | **Quantitative**, traced to a committed artifact and a JSON pointer. |
| **Rendering** | Flat. Orthographic or 2D. Square frames. No perspective, no bloom, no lighting. |
| **Lighting** | None. |
| **Typography** | Mono, tabular figures, slashed zero. Decimal points align down a column. |
| **Palette** | Viridis (sequential), Okabe–Ito (categorical). Never a UI colour. |
| **Animation** | Minimal. **Data marks never animate position.** Curves may draw once. |
| **Interaction** | FOCUS, COMPARE, EXPAND, CITE. |
| **Watermark** | `MEASURED · <artifact> · <commit>` |
| **Citations** | **Mandatory and mechanical.** Enforced by codegen, lint, and a build gate that re-reads the artifact. |
| **Accessibility** | Every chart has a data-table equivalent permanently in the DOM. AAA contrast. |

---

# 4 · STORY ARCHITECTURE

Ten acts. Three registers. One direction of travel.

```
 CORRIDOR (linear, cinematic)                    ROOMS (open, evidential)
 ─────────────────────────────                   ─────────────────────────

 I    ARRIVAL        [A]  wonder
 II   APPROACH       [A→S] attention
 III  INSTRUMENT     [S]  comprehension
 IV   PHOTON         [S]  anticipation
 V    CROSSING       [S→B] ★ THE PIVOT
 ─────────────────────────────────────────────
 VI   VALIDATION     [B]  trust        ────────→  /validation  · 6 records
 VII  VERDICT        [B]  respect      ────────→  /findings    · benchmark
 VIII MACHINE        [B]  understanding ───────→  /pipeline    · stages
 IX   RECORD         [B]  agency       ────────→  /data        · 424 days
 X    REPRODUCTION   [B]  transfer     ────────→  /build       · the command
```

A visitor may enter any room directly. The corridor is an offer, never a toll gate.

---

## ACT I — ARRIVAL · Register A

| | |
|---|---|
| **Purpose** | Earn attention without asserting anything |
| **Emotion** | Awe |
| **Question posed** | *What am I looking at?* |
| **Question answered** | Nothing yet — deliberately |
| **Dominant visual** | The star. Granulation, active regions, corona |
| **Dominant interaction** | ORBIT — drag to rotate, damped, inertial |
| **Transition out** | Camera pulls back; the Sun shrinks; something dark enters frame edge |

## ACT II — APPROACH · Register A → S

| | |
|---|---|
| **Purpose** | Perform the first honesty transition, visibly |
| **Emotion** | Wonder becoming attention |
| **Question posed** | *What is that object?* |
| **Question answered** | Aditya-L1, at L1, 1.5 million km from Earth |
| **Dominant visual** | Silhouette against solar glare, **draining** into wireframe |
| **Dominant interaction** | Scroll only — this act is watched, not handled |
| **Transition out** | Watermark resolves to `SCHEMATIC · NOT TO SCALE` |

**The drain is the mechanism.** Colour flattens, lighting dies, edges become lines. The
visitor *watches the image stop claiming to be a photograph.* No text is required.

## ACT III — INSTRUMENT · Register S

| | |
|---|---|
| **Purpose** | Explain the mission's structure, sourced |
| **Emotion** | Comprehension |
| **Question posed** | *What does it carry?* |
| **Question answered** | Seven payloads; one of them measures soft X-rays |
| **Dominant visual** | Blueprint separating into layers; seven annotated payloads |
| **Dominant interaction** | INSPECT — hover a payload to raise its label and citation |
| **Transition out** | Six payloads dim. SoLEXS isolates |

**Every label cites.** Where internal detail is unknown, the annotation says so.

## ACT IV — PHOTON · Register S

| | |
|---|---|
| **Purpose** | Establish what is about to happen |
| **Emotion** | Anticipation |
| **Question posed** | *What happens when light reaches that plane?* |
| **Question answered** | Held — the answer is Act V |
| **Dominant visual** | Sensor plane, aperture, an inbound photon path |
| **Dominant interaction** | Scroll pacing only |
| **Transition out** | The photon reaches the plane |

## ACT V — THE CROSSING · Register S → B ★

**The most important act. Everything before is preface; everything after is consequence.**

| | |
|---|---|
| **Purpose** | Convert wonder into evidence, in one visible instant |
| **Emotion** | The floor changing underfoot |
| **Question posed** | *Is that number right?* |
| **Question answered** | Light became one number, and that number has an address |
| **Dominant visual** | Wireframe collapses to a point; a single value appears |
| **Dominant interaction** | None. This beat is watched |
| **Transition out** | More values arrive; a light curve assembles from real archive data |

**The beat, precisely:**

1. Photon meets plane.
2. All schematic geometry contracts inward to a point over ~600 ms.
3. Where it was: **one number**, mono, tabular, enormous.
4. Watermark resolves: `MEASURED · T1 solexs_lc_1min · 43fd0e22`.
5. A second value. A third. A light curve draws itself from the archive.

**This is the product in one beat.** Before it: beautiful, explanatory, unverifiable.
After it: checkable to a digest. The scroll position where the watermark changes is the
most important pixel on the site.

## ACTS VI–X — The Evidence

| Act | Room | Emotion | Question answered |
|---|---|---|---|
| **VI Validation** | `/validation` | Trust | *Was it right?* — Six times it was not. Here is every ruling |
| **VII Verdict** | `/findings` | Respect | *What did it conclude?* — ML did not help |
| **VIII Machine** | `/pipeline` | Understanding | *How was it made?* — Seven stages, twenty fail-loud rules |
| **IX Record** | `/data` | Agency | *Can I see the raw numbers?* — Any of 424 days |
| **X Reproduction** | `/build` | Transfer | *Can I do this myself?* — Digest and commands |

**Act X is the only act whose success is measured by the visitor leaving.**

---

# 5 · SCENE STORYBOARDS

Camera notation: `◉` camera · `☉` star · `▭` spacecraft · `→` movement · `⊙` focus target

---

## SCENE 1.1 — First light

```
        ☉ (large, centre-right)
       ╱
      ◉  fov 32°, r = 5.4, azimuth 0.6, elevation 0.22
```

| | |
|---|---|
| **Camera** | Static. Orbit under user control only |
| **Scroll** | Not yet pinned. Native page scroll |
| **Transformation** | Idle drift, ~5 min/revolution |
| **Enters** | Star, corona, prominences, hero copy |
| **Leaves** | — |
| **Text timing** | Eyebrow 60 ms, h1 130 ms, lead 200 ms, CTA 280 ms — staggered fade-up, once |
| **Interaction** | ORBIT available immediately. Cursor reads `grab` |
| **End state** | Visitor has rotated the star or scrolled |

## SCENE 2.1 — The pull-back

```
   ☉ ────────────────────────── ▭
   (shrinking)                  (entering, dark)
                        ◉ →→→   pulls back along +Z
```

| | |
|---|---|
| **Camera** | Dolly back. r: 5.4 → 42 over scroll |
| **Scroll** | **Pinned.** Canvas sticky; scroll drives camera distance |
| **Transformation** | Sun's angular size shrinks; spacecraft enters from frame right |
| **Enters** | Spacecraft silhouette |
| **Leaves** | Hero copy fades at 20% of act |
| **Text timing** | Single line at 60%: *"1.5 million kilometres from Earth."* |
| **Interaction** | Suspended — ORBIT re-enables in Act III |
| **End state** | Spacecraft occupies centre frame, still photoreal silhouette |

## SCENE 2.2 — The drain ★

```
   PHOTOREAL ──────────────────→ WIREFRAME
   [colour]  [desaturate] [flatten] [edges]
   watermark: ARTISTIC ─────────→ SCHEMATIC · NOT TO SCALE
```

| | |
|---|---|
| **Camera** | Static hold — the transformation must not compete with movement |
| **Scroll** | Pinned. Scroll drives the drain 0→1 |
| **Transformation** | Saturation → 0. Lighting → 0. Edge detection rises. Fill → transparent |
| **Text timing** | Watermark crossfades at drain = 0.7 |
| **Interaction** | None |
| **End state** | Orthographic wireframe, flat, annotated. Register S established |

**Rule:** the camera holds still through every register transition. The *image* changes
register; the *viewpoint* does not. Moving both at once reads as a cut, and a cut breaks
the continuity the whole experience depends on.

## SCENE 3.1 — Layer separation

```
   ▭ →  ▭   ▭   ▭      exploded along view-normal
        │   │   │
        └─ payload bay, structure, panels
```

| | |
|---|---|
| **Camera** | Slow orbit, 15° total, to establish depth |
| **Scroll** | Pinned. Scroll drives separation distance |
| **Transformation** | Structural layers translate apart; connecting lines persist |
| **Enters** | Seven payload markers |
| **Text timing** | Each payload label rises as its marker reaches full opacity, staggered 120 ms |
| **Interaction** | INSPECT enabled. Hover raises label + citation |
| **End state** | Seven payloads visible and labelled |

## SCENE 3.2 — Isolation

| | |
|---|---|
| **Camera** | Push toward SoLEXS. r reduces 40% |
| **Scroll** | Pinned |
| **Transformation** | Six payloads → 15% opacity. SoLEXS → accent colour |
| **Text timing** | Full annotation block at 70%, including the admission of unknown internals |
| **Interaction** | INSPECT persists |
| **End state** | SoLEXS alone, symbolic, annotated, cited |

## SCENE 5.1 — THE CROSSING ★★★

```
   t=0.0   ⊙ photon inbound      │ schematic plane
   t=0.4   ✦ contact             │ all geometry begins contracting
   t=0.7   ·  point              │ watermark begins crossfade
   t=1.0      6.23               │ MEASURED · T1 · 43fd0e22
```

| | |
|---|---|
| **Camera** | **Absolutely still.** No movement of any kind |
| **Scroll** | Pinned. This act consumes ~120vh of scroll for ~1.5 s of animation — deliberately slow, so it cannot be missed |
| **Transformation** | Geometry contracts to a point; a numeral resolves in its place |
| **Enters** | One measured value, then a light curve |
| **Leaves** | All schematic geometry, permanently |
| **Text timing** | Watermark at 0.7. Artifact path at 0.9. No prose until 1.0 |
| **Interaction** | None during. FOCUS available after |
| **End state** | Register B. The corridor ends; the rooms begin |

---

# 6 · MOTION LANGUAGE

## 6.1 Camera rules

1. **Critically damped, always.** Damping ratio 1.0. A camera must never overshoot —
   overshoot reads as nausea because the entire world travels past the target and back.
2. **One camera movement at a time.** Never dolly and orbit simultaneously.
3. **The camera holds still through register transitions.** (Scene 2.2)
4. **Scroll drives camera position, never camera velocity.** Position is a pure function
   of scroll offset, so reversing scroll reverses the shot exactly.

## 6.2 Timing

| Token | Duration | Use |
|---|---|---|
| instant | 80 ms | Hover, focus |
| fast | 150 ms | Toggles, tooltips |
| base | 250 ms | Panels, disclosure |
| slow | 400 ms | Curve draw-on, stagger |
| cinematic | 600–1200 ms | Register transitions only |

Easing: `cubic-bezier(0.16, 1, 0.3, 1)` for entrances; springs for anything interruptible.

## 6.3 The three motion laws

- **L1 — Data marks never animate position.** A point may fade in; it may never slide to
  its value. An animated data point asserts intermediate values that were never measured.
- **L2 — Loops only with an archival stamp.** A loop with a permanent date range reads as
  playback; a loop without one reads as telemetry.
- **L3 — Reduced motion is a gate, not a degradation.** All durations → 1 ms; every
  draw-on renders in its completed state; the pinned corridor collapses to a scrollable
  document that loses no information.

## 6.4 When motion must stop

- When the visitor is reading. No motion in the viewport during a prose block.
- When a measurement is on screen and being compared.
- When the tab is hidden or the canvas is off-screen — rendering halts entirely.
- When the visitor has expressed a preference for reduced motion.

## 6.5 Performance budgets

| Surface | JS (gz) | Frame | LCP |
|---|---|---|---|
| Corridor (`/`) | ≤ 450 KB lazy | 16.7 ms p95 | < 1.8 s (text + poster, never canvas) |
| `/validation` | ≤ 15 KB | — | < 0.8 s |
| `/findings` | ≤ 120 KB | — | < 1.2 s |
| `/pipeline` | ≤ 200 KB | — | < 1.2 s |
| `/data` | ≤ 260 KB | — | < 2.0 s |
| `/build` | ≤ 20 KB | — | < 1.0 s |

**Measured, never estimated.** Two framework estimates in this project's history were
wrong by 4.6× and 1.4×; budgets are verified against built output.

---

# 7 · VISUAL LANGUAGE

**Every act must be recognisable with its title removed.**

## 7.1 Shared foundations

- **Type:** IBM Plex Sans (interface), IBM Plex Mono (measurement). Two families.
- **Scales:** interface 13 px base; document 17 px base, 68ch measure.
- **Space:** 4 px unit. Content max 1440 px.
- **Elevation:** luminance and border, never shadow — on a near-black ground a drop
  shadow is physically invisible.
- **Radius:** 3/5/8 px. **Charts and tables: 0.** A rounded corner on a plot implies the
  data is clipped by decoration.

## 7.2 Per-act identity

| Act | Identity | Signature elements |
|---|---|---|
| **I Arrival** | **Void** | Full-bleed, no chrome, warm emissive, deep black |
| **II Approach** | **Drain** | Progressive desaturation; the only act that changes register mid-scene |
| **III Instrument** | **Blueprint** | Orthographic wireframe, mono annotation, leader lines, corner registration marks |
| **IV Photon** | **Vector** | Single accent path on flat ground; near-empty frame |
| **V Crossing** | **Collapse** | Geometry → point → numeral. One value, enormous |
| **VI Validation** | **Courtroom** | Exhibit numbering, ruling blocks, quoted contract text, declined amendments in amber |
| **VII Verdict** | **Debrief** | One enormous statement, then a dense benchmark. CI bars with numeric labels |
| **VIII Machine** | **Factory** | Orthographic, left→right flow, stage numbering, fail-loud rule badges |
| **IX Record** | **Laboratory** | Grid, calendar heatmap, instrument panels, viridis |
| **X Reproduction** | **Workstation** | Terminal, digests, copyable commands, monospace throughout |

## 7.3 Colour science

- **UI and data palettes are disjoint namespaces.** A chart series may never use a UI
  colour; a UI element may never use a data colour. A theme change can then never alter
  the meaning of a published figure.
- **Sequential:** viridis. Perceptually uniform, monotonic in luminance, colourblind-safe,
  degrades correctly to greyscale. Rainbow maps fabricate boundaries — in a spectrogram
  that is a scientific error, not a taste error.
- **Categorical:** Okabe–Ito, capped at six series, with redundant dash patterns.
- **Contrast:** body text ≥ 7:1 (AAA). Enforced by build gate.
- **Status is never colour alone.** Always icon or text, so it survives greyscale printing
  into a referee's report.

---

# 8 · INTERACTION LANGUAGE

## 8.1 The verbs

| Verb | Input | Register | Communicates |
|---|---|---|---|
| **ORBIT** | drag / one finger | A | The object is solid, not an image |
| **APPROACH** | wheel / pinch | A, S | Proximity reveals structure |
| **INSPECT** | hover / focus | S, B | Everything has provenance |
| **ISOLATE** | click | S | This component, alone |
| **FOCUS** | click / Enter | B | Selection; camera frames the target |
| **COMPARE** | toggle | B | Two measurements, one scale |
| **EXPAND** | disclosure | B | Detail on demand |
| **CITE** | hover / focus | S, B | Where this came from |

Eight verbs, learnable in under a minute. **Anything that is not one of these must be
justified in writing or cut.**

## 8.2 Latency

| Path | Budget |
|---|---|
| Pointer → camera | **same frame (≤16.7 ms)** |
| Hover → feedback | ≤ 50 ms |
| Click → transition begins | ≤ 50 ms |

**Architectural rule:** input never passes through the framework's state system. Pointer
events write to a mutable store read inside the render loop. Framework state changes only
on discrete semantic events — roughly once a second, not sixty times.

## 8.3 Discoverability

Four layers, escalating only when needed: proximity response → cursor semantics →
first-visit affordance (once, persisted) → idle invitation (pulses **once**, never loops).

**Prohibited:** tutorial modals, coach marks, bouncing scroll chevrons.

## 8.4 Exit is always available

Every act is skippable in one action. A persistent evidence affordance is visible on
first paint. **A referee must never be required to travel the corridor.**

---

# 9 · SCIENTIFIC HONESTY

## 9.1 What may be artistic

The star. Its granulation, corona, prominences, and colour. It asserts nothing, carries a
burned-in watermark, and its inputs — while real — are not presented as observation.

## 9.2 What may be schematic

Spacecraft exterior configuration, payload identity and placement, sensor orientation —
**each cited to public documentation.** Rendered deliberately flat so the form itself
announces that no literal accuracy is claimed.

## 9.3 What must always be measured

Every quantity. Every count, rate, digest, interval, threshold, date, and file count.
Enforced mechanically:

- The display component accepts a **key**, not a value — a developer cannot pass a number.
- Code generation fails on an unresolvable pointer.
- A lint rule rejects numeric literals in markup.
- **A build gate re-reads the original artifact from disk and asserts the rendered string
  matches.** Error budget: zero, permanently.

## 9.4 How uncertainty is represented

Confidence intervals render as a bar **and** as text, always. Overlap is never left to
visual judgement — readers systematically misjudge it, and "statistically
indistinguishable" is the most misread claim in any benchmark table.

## 9.5 How symbolic representation is marked

In-frame, at the point of viewing:
> *Symbolic representation. Internal configuration not publicly specified.*

## 9.6 How citations appear

| Register | Citation |
|---|---|
| A | None required |
| S | Public documentation, in-frame on INSPECT |
| B | Artifact path + RFC-6901 pointer + SHA-256 + commit |

## 9.7 How provenance is exposed

Every measured value is at most two interactions from its artifact path, pointer, digest,
and commit. This is a testable property, not an aspiration.

## 9.8 Prohibited absolutely

Invented internal geometry presented as literal · photoreal rendering of undocumented
structure · another mission's imagery presented as ours · live/telemetry framing · fake
alerts · interpolated gaps · count-up number animation (it animates a measurement through
values that were never measured) · any implication of institutional affiliation.

---

# 10 · PERFORMANCE CONSTITUTION

1. **No runtime server.** Every response is enumerable at build time.
2. **Evidence surfaces ship ~0 KB of JavaScript.** Cheap rooms pay for the expensive
   corridor.
3. **Progressive enhancement.** Full scene → static poster → complete prose → readable
   HTML with no JS at all.
4. **Accessibility is a gate, not a goal.** Lighthouse a11y 100 on every surface. WCAG 2.2
   AA in full, AAA on contrast. Where AAA is not met, it is stated — claiming it falsely
   would be worse than not claiming it.
5. **Budgets are measured against built output**, never against a bundler's report.
6. **The GPU pauses when unobserved.** Off-screen or backgrounded → rendering halts.
7. **The cinematic layer is sealed.** It cannot import from the evidence layer, and
   evidence cannot import from it. Total failure of the GPU layer leaves every credibility
   surface untouched.

---

# 11 · IMPLEMENTATION ROADMAP

Nothing begins before the previous milestone is accepted.

## M0 — Bible approval
**Objective:** agree the constitution. **Deliverable:** this document, signed off.
**Acceptance:** registers, acts, and honesty rules approved. **Effort:** review only.
**Risk:** approving a narrative that later proves unbuildable — mitigated by M1.

## M1 — The Crossing, alone ★
**Objective:** prove the pivotal beat lands, before building anything around it.
**Dependencies:** M0; reopening the frozen shader directory.
**Deliverables:** Act V as a standalone scene — schematic plane, photon, collapse,
numeral, watermark transition, light curve assembling from real archive data.
**Acceptance:** a first-time viewer, unprompted, understands that something changed from
*shown* to *proven*. 60 fps at p95. Bundle within budget.
**Risk:** the beat may not land. **This is the point of doing it first.**
**Effort:** 1 sprint.

## M2 — Register S foundation
**Objective:** the schematic language, with citations.
**Dependencies:** M1 accepted.
**Deliverables:** low-poly exterior from published imagery; wireframe/orthographic
treatment; annotation and citation system; `SCHEMATIC · NOT TO SCALE` in frame buffer;
DOM equivalent list.
**Acceptance:** every structural label cites public documentation; unknown internals
admitted in-frame; a11y list complete.
**Risk:** geometry effort underestimated. Mitigation: recognisable, not accurate.
**Effort:** 1–2 sprints.

## M3 — Acts II–IV: the corridor
**Objective:** connect Arrival to the Crossing.
**Dependencies:** M1, M2.
**Deliverables:** pinned-canvas scroll orchestration; the drain; layer separation;
isolation; photon approach.
**Acceptance:** scroll velocity unaltered; `Ctrl+F` works; skippable in one action;
reduced-motion collapses to readable document.
**Risk:** scroll orchestration complexity. Mitigation: native sticky + scroll offset
before reaching for a library.
**Effort:** 2 sprints.

## M4 — Act identity pass
**Objective:** each room recognisable with its title removed.
**Dependencies:** M3.
**Deliverables:** courtroom, debrief, factory, laboratory, workstation treatments.
**Acceptance:** title-removed recognition test passes for all five; evidence budgets
unchanged; contrast gates pass.
**Effort:** 1–2 sprints.

## M5 — Integration and hardening
**Objective:** one experience, not eleven pieces.
**Dependencies:** M1–M4.
**Deliverables:** full-journey pass; a11y audit with assistive technology; visual
regression; Lighthouse; deployment.
**Acceptance:** a11y 100 everywhere; all budgets met on a mid-tier device; complete
degradation ladder verified.
**Effort:** 1–2 sprints.

**Total: 6–9 sprints**, with a genuine kill point at M1.

---

# APPENDIX A — PAGE FLOW

```
                    ┌──────────────────────────────────────┐
                    │   /  THE CORRIDOR  (linear, pinned)  │
                    │                                       │
   entry ─────────→ │  I ARRIVAL    [A]  ORBIT              │
                    │  II APPROACH  [A→S] drain             │
                    │  III INSTRUMENT [S] INSPECT           │
                    │  IV PHOTON    [S]                     │
                    │  V CROSSING   [S→B] ★                 │
                    └───────────────┬──────────────────────┘
                                    │  handoff
        ┌───────────┬───────────┬───┴───────┬───────────┐
        ▼           ▼           ▼           ▼           ▼
  /validation  /findings   /pipeline     /data      /build
   courtroom    debrief     factory    laboratory  workstation
     [B]          [B]         [B]         [B]         [B]
     0 KB        ~0 KB       ~0 KB       58 KB       ~0 KB
        │           │           │           │           │
        └───────────┴───────────┴───────────┴───────────┘
              depth gauge + handoff link every room
              direct entry to any room always permitted
```

# APPENDIX B — CAMERA PATH

```
  r = 5.4  ┤●  I  Arrival (orbit, user-controlled)
           │ ╲
  r = 42   ┤  ●─────● II Approach (dolly back, then HOLD for drain)
           │        │
  r = 25   ┤        ●───● III Instrument (slow 15° orbit)
           │            │
  r = 15   ┤            ●──● III.2 Isolation (push in)
           │               │
  r = 8    ┤               ●─● IV Photon
           │                 │
  r = 8    ┤                 ●  V CROSSING — camera absolutely still
           └───────────────────────────────────────→ scroll
```

# APPENDIX C — REGISTER TRANSITION

```
  ACT:      I ──── II ──── III ──── IV ──── V ──── VI+
  REGISTER: [  A  ][A→S ][   S   ][  S  ][S→B][   B   ]
  CLAIM:     none   none   struct   struct  →   quantity
  CERTAINTY: ░░░░░░ ░░▒▒▒▒ ▒▒▒▒▒▒▒ ▒▒▒▒▒▒ ▓▓▓▓ ████████
  WATERMARK: ARTISTIC ───→ SCHEMATIC ─────→ MEASURED

  ← certainty increases monotonically, never reverses →
```

---

# ADDENDUM A — THE CINEMATIC CUT (owner storyboard, 2026-07-23)

Refines the corridor into five scenes. The Sun stops being an object we render and
becomes the **setting**; the spacecraft becomes the **actor**; the photon becomes the
**protagonist**. This is the shooting order.

| Scene | Was (Bible act) | Refinement |
|---|---|---|
| **1 · The Universe** | Arrival | Full-frame real solar footage (SDO, attributed). Non-interactive. One line only: *"Every solar flare begins here."* The Sun is environment, not centrepiece. |
| **2 · The Observer** | Approach | Aditya-L1 enters small against the enormous Sun. No text. Scale is understood instantly. |
| **3 · The Dissection** | Instrument | The spacecraft **dissects itself** — panels separate, bus separates, payload deck exposed. Seven payloads light in sequence (SUIT, VELC, HEL1OS, ASPEX, PAPA, MAG, SoLEXS). All fade but SoLEXS. This is the "now you know what this is about" beat. |
| **4 · SoLEXS** | Instrument (cont.) | Only aperture, detector plane, photon direction. No invented internals. |
| **5 · Crossing** | Crossing | Photon → detector → point → number → measured → light curve. |

**Governing refinements:**
- The Sun never competes with the spacecraft. When the dissection begins, the solar
  footage **freezes and recedes** — the spacecraft owns the screen.
- The spacecraft is composited *into* the scene (3D over the solar plate), not a flat
  background behind a UI.
- The spacecraft is rendered **schematic (Register S)** — blueprint/wireframe, glowing,
  self-dissecting. Not photoreal. This is honest (no invented solid internals), needs no
  licensed model, and is the more cinematic choice.
- Payload identities and placement are the seven publicly-documented Aditya-L1 payloads
  (ISRO / eoPortal). Every label cites, per Register S.
