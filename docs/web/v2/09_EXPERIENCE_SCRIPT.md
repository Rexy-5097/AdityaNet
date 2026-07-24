# 9 · Experience Script

**Status:** governing document. Supersedes [Doc 2](02_EFFECT_CATALOGUE.md) and
[Doc 3](03_INTERACTION_CATALOGUE.md) where they conflict.

## 9.0 Approved decisions

| Decision | Resolution |
|---|---|
| Register pivot | **LUT colour grading** — three `.cube` grades cross-faded by `t` |
| Hero footage | **SVS slow-rotation Sun clip** (not a flare event) |
| Spacecraft | **Schematic primitives.** No stock mesh |
| Scroll | **GSAP ScrollTrigger + Lenis** (drei `<ScrollControls>` dropped, not held) |

## 9.1 What this document is

Every scene declares three things: **the emotion intended**, **the information conveyed**,
and **the specific visual or interaction that carries them**.

Nothing renders without a line in this script. The test, applied to every animation,
transition and effect:

> **Does this reinforce the intended emotion, or the intended understanding?**
> If neither — remove it. If it reinforces one but damages the other — remove it.
> "It looks good" is not an answer.

An effect that is beautiful, cheap, well-supported and mature still fails if it has no line
here. §9.11 records what that test already deleted.

---

## 9.2 Scene 1 · The Universe · `t` 0.00–0.12

| | |
|---|---|
| **Emotion** | Awe — immediately qualified by care. Two feelings at once: *this is overwhelming* and *someone is being honest with me about it* |
| **Information** | The Sun is real, it is recorded, and this recording is **not** Aditya-L1 data |
| **Register** | A · Artistic |

**Carrying visual:** the SVS slow-rotation clip, full-frame, camera static. The footage is
the only thing moving. Slow rotation was chosen over a flare precisely because the hero must
not out-dramatise the crossing — the most important event on this site happens at `t=0.86`,
not here.

**Carrying interaction:** none. The visitor has done nothing yet and is owed a moment.

| Effect | Justification against this scene |
|---|---|
| **LUT (warm)** | Warmth *is* the artistic register. Establishes the temperature the site will later drain away — the pivot is unreadable unless this baseline lands first |
| **Bloom** | "This light exceeds the sensor." Serves awe directly. Dies with the register |
| **Vignette** | Turns a viewport into a *shot*. Serves the cinematic contract in one cheap, static gesture |
| **Watermark** | Carries the second half of the emotion. Without it the scene is awe alone, and awe alone is the failure mode this project exists to repudiate |

**Rejected here:** God Rays (interprets light we never measured), chromatic aberration
(§9.11), star field (§9.11).

---

## 9.3 Scene 2 · The Observer · `t` 0.12–0.24

| | |
|---|---|
| **Emotion** | Perspective, then a small pride — *that tiny thing is what we sent* |
| **Information** | Aditya-L1 exists, it is small, it is pointed at this |
| **Register** | A → S begins |

**Carrying visual:** the craft enters frame while the camera holds still. Motion belongs to
the subject; scale therefore reads honestly. A camera push here would flatter the craft and
lie about its size.

**Carrying interaction:** scroll velocity governs entry speed — the visitor's own hand
brings the spacecraft in.

| Effect | Justification |
|---|---|
| **Rack focus (DoF)** | The one flourish. Transfers attention *without moving anything* — no vestibular cost, no scale distortion. It is the exact frame where the Sun stops being the subject and becomes the setting |
| **LUT (warm→cool begins)** | Certainty starts rising. The grade must begin shifting *before* the visitor consciously notices, so the change feels discovered rather than announced |
| **Bloom (dying)** | Its decay is information: we are leaving the artistic register |

---

## 9.4 Scene 3 · The Dissection · `t` 0.24–0.48

| | |
|---|---|
| **Emotion** | Curiosity — *what are all of these?* |
| **Information** | Seven instruments, publicly documented, named and sourced |
| **Register** | S · Schematic |

**Carrying visual:** the craft opens; payloads light in sequence. The geometry is
deliberately crude — a box, two planes, seven markers. **Crudeness is the message:** this is
a diagram, and a diagram does not pretend to know the internals.

**Carrying interaction:** hover any payload → outline, name, one-line description, source
citation. The only free exploration in the piece, placed exactly where curiosity peaks.

| Effect | Justification |
|---|---|
| **Grid** | "You are reading a diagram now." Converts register in one visual gesture, statically, for ~nothing |
| **LUT (cool)** | Structure is cool. The palette is now doing the epistemic work |
| **Outline (on hover)** | Answers the curiosity the scene created, on demand |
| **drei `<Text>` / `<Line>`** | Labels and leaders. Naming is the information; nothing else here conveys it |
| **Slow orbit** | Parallax proves the object is volumetric before it opens. One sustained move, not a flourish |

**Rejected here:** bloom (a diagram does not glow), cursor-driven camera yaw (§9.11).

---

## 9.5 Scene 4 · SoLEXS · `t` 0.48–0.60

| | |
|---|---|
| **Emotion** | Focus, narrowing to intent |
| **Information** | Of seven instruments, one produced this site's data |
| **Register** | S |

**Carrying visual:** six payloads fade; SoLEXS remains, outlined and named. The camera
dollies in and the lens lengthens (40°→28°) — a longer lens is the visual grammar of
scrutiny.

**Carrying interaction:** none. Attention is being *given*, not solicited. Adding an
interaction here would divide the attention the scene exists to concentrate.

| Effect | Justification |
|---|---|
| **Outline** | Selection is the entire content of this scene |
| **Isolation fade** | Removal, not addition. Six things leave; the survivor gains meaning by subtraction |
| **The 400 ms hold at `t=0.46`** | Stillness is a shot. The pause converts a transition into a statement |

---

## 9.6 Scene 5 · The Crossing · `t` 0.60–0.72

| | |
|---|---|
| **Emotion** | Inevitability. Not excitement — *this was always going to happen* |
| **Information** | Light from that Sun struck that detector. This is the physical event behind every number on the site |
| **Register** | S, tipping to B |

**Carrying visual:** one photon travels to the detector. **The camera is locked off and
stays locked off.** Exactly one thing moves in the entire frame.

**Carrying interaction:** scroll drives the photon. The visitor's own scroll delivers the
light — the strongest coupling of gesture to meaning in the piece.

| Effect | Justification |
|---|---|
| **LUT (cool→neutral)** | Certainty completing. The grade arrives at neutral as the measurement arrives |
| **Vignette** | Holds the frame while nothing else does |

**Rejected here:** Shock Wave on impact (spectacle — a single still frame carries more
authority), particle burst, camera shake. **This scene's power is entirely in what it
refuses to do.** Every effect proposed for it has been declined.

---

## 9.7 Scene 6 · The Collapse · `t` 0.72–0.82

| | |
|---|---|
| **Emotion** | Compression — *all of that, reduced to this* |
| **Information** | An observation becomes a datum. Structure is discarded; quantity survives |
| **Register** | S → B |

**Carrying visual:** all geometry contracts to a point. A single eased flash — **one ramp,
never a strobe** (no flashing above 3 Hz, anywhere).

| Effect | Justification |
|---|---|
| **Collapse to point** | The literal enactment of measurement: a complex thing becomes one value |
| **Tone-mapping swap (ACES→None)** | The image stops being *photographed* and starts being *plotted*. Free, and precisely on-message |
| **Effect stack falling to 2, then 0** | The render budget performs the argument |

**Rejected here:** pixelation (implies resolution *loss*; the collapse is a certainty *gain*).

---

## 9.8 Scene 7 · The Number · `t` 0.82–0.90

| | |
|---|---|
| **Emotion** | Recognition, and the beginning of trust — *that's real, and I can check it* |
| **Information** | `112.98` — the first observed minute of 2024-05-14 — with artefact, pointer, hash |
| **Register** | B · Measured |

**Carrying visual:** the canvas is **gone**, not faded behind. DOM only. `112.98` in tabular
figures. Watermark flips to `MEASURED · T1 solexs_lc_1min · 43fd0e22`, arriving *with* the
value, not after it.

**Carrying interaction:** one click reveals artefact name, JSON pointer, and hash.

| Effect | Justification |
|---|---|
| **Zero effects** | Post-processing a measurement is a visual lie about its provenance. The austerity *is* the credibility |
| **Number resolve, 600 ms** | Resolves; does not count up. A measured value appears — it does not perform |

> This is the frame the whole site exists to earn. If a visitor screenshots one image, it
> should be this one — and that screenshot must contain enough provenance for a stranger to
> check it.

---

## 9.9 Scene 8 · The Curve · `t` 0.90–1.00

| | |
|---|---|
| **Emotion** | Context, then respect |
| **Information** | One minute becomes a day: 1440 points, 2024-05-14, X8.7 flare, peak 29036.25. Then: **the machine learning did not help** |
| **Register** | B |

**Carrying visual:** the light curve draws in **linear** time — no easing. An eased draw
would misrepresent the time axis, and this is the clearest example of the honesty test
reaching all the way down into an easing curve.

**Carrying interaction:** hover any minute → exact value + UTC timestamp (uPlot). The payoff:
*the data is real, inspect it.*

**The Turn:** the arc ends by handing off to the negative result. The last emotional beat of
a cinematic experience is the project admitting its own method failed. That is the entire
thesis, and it must not be softened.

---

## 9.10 The emotional spine

> **awe → perspective → curiosity → focus → inevitability → compression → recognition → respect**

Each beat is a precondition for the next. Awe without care is spectacle. Curiosity without
focus is noise. Recognition without provenance is decoration. **Trust is the product; every
prior beat exists to make the visitor care enough to verify.**

---

## 9.11 Audit — what the script deleted

The script was applied to every adopted effect and interaction. Four items had no line and
are **removed from the plan**:

| Removed | Was justified as | Why it failed |
|---|---|---|
| **Chromatic aberration** | "Lens realism — an instrument recorded this" | Fails the dishonesty test on its own terms. SDO's optics do not produce it — we would be adding a **fictional optical artefact to real telescope footage**, simulating a camera that never existed. The one effect I adopted that contradicts the project's premise |
| **Star field** (drei `<Stars>`) | "Spatial context" | Conveys no information — L1 is not legible from a star field — and Doc 1 forbids ambient decoration. Empty near-black is more austere and more honest |
| **Cursor-driven camera yaw** | "Parallax of intent" | Reinforces no intended emotion, and during Scenes 3–4 it competes with the tier-1 mover. Ambient sophistication |
| **Magnetic buttons** | "Awwwards microinteraction vocabulary" | The plainest failure: borrowed prestige. Communicates nothing about the science |

**Amended, not removed:**

| Item | Amendment |
|---|---|
| **Film grain** | Demoted from "photographic authenticity" (which implies film capture that never happened) to **dither only** — banding mitigation on dark gradients. Static, ≤0.02, Scenes 1–2. Kept for a technical reason, not an aesthetic one |
| **Vignette in Scene 5** | "Opening out" was decorative motion. Now **static** — it holds the frame, it does not perform |

**Net effect stacks after audit:**

| Scene | Stack | Count |
|---|---|---|
| 1 · Universe | LUT(warm) + Bloom + Vignette | 3 |
| 2 · Observer | LUT(warm→cool) + Bloom(dying) + DoF(rack focus beat) | 3 |
| 3 · Dissection | LUT(cool) + Grid + Vignette | 3 |
| 4 · SoLEXS | LUT(cool) + Grid + Outline | 3 |
| 5 · Crossing | LUT(cool→neutral) + Vignette | 2 |
| 6 · Collapse | LUT(neutral) + tone-map swap | 2 |
| 7–8 · Measured | **none** | 0 |

Dither and SMAA sit outside the count (corrective, not expressive). The stack never exceeds
three and **falls monotonically to zero**.

---

## 9.12 The standing rule

Every future proposal — mine or anyone's — must add a row to a scene table in §9.2–9.9
before it can be built. No row, no render.

When an effect is defended with *"it would look incredible here,"* that is the signal to
apply §9.1 hardest. The four deletions above were all defensible on craft, cost, maturity
and browser support. They were removed because **beauty is not a justification; it is the
thing that has to be justified.**
