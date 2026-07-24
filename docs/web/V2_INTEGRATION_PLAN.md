# AdityaNet v2 — Dependency & Asset Plan

**Role:** Systems Integrator. **Date:** 2026-07-24. **Status:** plan only — no code written.

**Governing rule:** every component below was tested against *"Can this be imported?"* first.
Custom engineering is proposed in exactly **one** place, and that case is argued explicitly
in §7 rather than assumed.

**Originality budget.** AdityaNet's originality is spent on storytelling, sequencing,
transitions, scientific honesty, and evidence presentation. It is spent nowhere else. Every
pixel-producing technology below is someone else's, already hardened.

**Licence verification method.** JS licences were read from the npm registry metadata
(`npm view <pkg> license`) rather than recalled. Asset licences were read from the
publisher's own policy pages, cited inline. Nothing here is asserted from memory.

---

## 1. Verified licence ground truth

Checked this session, against primary sources:

| Item | Verified finding | Source |
|---|---|---|
| NASA images/video/3D | "Generally not subject to copyright" — free to reuse. Conditions: acknowledge NASA, no implied endorsement, care with identifiable people, third-party material marked separately | [NASA Brand Center — Images and Media](https://www.nasa.gov/nasa-brand-center/images-and-media/) |
| NASA SVS (solar footage) | "All of our content is in the public domain (unless otherwise noted)… free to download, use, and redistribute for whatever purposes you see fit." **Caveat: some videos carry licensed music that is NOT public domain — use video without audio** | [SVS Help](https://svs.gsfc.nasa.gov/help/) |
| NASA 3D Resources | Free, copyright-free, glTF `.glb`/`.usdz`, Draco-compressed — already web-optimised | [NASA 3D Resources](https://www.nasa.gov/3d-resources/), [GitHub](https://github.com/nasa/NASA-3D-Resources) |
| GSAP (incl. ScrollTrigger, SplitText) | Now free under the standard "no charge" licence. Commercial use explicitly covered, no payment, no attribution requirement. Prohibited only for building competing no-code animation tools | [GSAP Standard License](https://gsap.com/standard-license/) |
| three, R3F, drei, r3f-postprocessing, lenis, motion, uplot, recharts, zustand, astro, leva, maath | **MIT** | npm registry |
| postprocessing | **Zlib** (permissive, MIT-compatible) | npm registry |
| d3, @observablehq/plot | **ISC** (permissive, MIT-compatible) | npm registry |
| @theatre/core | **Apache-2.0** | npm registry |

All proposed licences are permissive and mutually compatible. **No copyleft, no GPL, no
"non-commercial", no paid tier anywhere in the runtime dependency tree.**

---

## 2. Scene 1 — The Sun (the setting)

The Sun must never be procedurally rendered again. It is imported footage.

| Purpose | Existing library / asset | Licence | Community maturity | Performance | Integration difficulty | Reason for choosing it |
|---|---|---|---|---|---|---|
| Cinematic solar footage (hero) | **NASA SVS SDO 4K galleries** — [SDO 4k Content](https://svs.gsfc.nasa.gov/gallery/sdo4k-content/), [4k slow-rotation Sun](https://svs.gsfc.nasa.gov/12613/) | Public domain (verified) | NASA Goddard, continuously published since 2010 | Ship a transcoded 1080p/720p H.264+WebM, ~2–5 MB, `poster` + `preload="none"`. **Never ship the 4.9 GB master** | **Low** — `<video>` + `THREE.VideoTexture` (built into three, no dep) | The single highest-leverage import in the project. Real Sun, real flares, zero shader work, zero licence cost. Replaces ~600 lines of GLSL |
| Still solar disc (fallback / poster / low-power) | **SDO latest images** `latest_1024_0171.jpg`, `latest_1024_HMIIC.jpg` — already vendored | Public domain (verified) | Operational since 2010 | ~190 KB each, cached | **None** — already in `public/` | Already working in the M1 prototype. Doubles as the `<video poster>` and the `prefers-reduced-motion` path |
| Star field backdrop | **drei `<Stars>`** or **ESA/Gaia sky survey** | MIT / ESA credit-required | drei is the standard R3F helper set | Points geometry, negligible | **Low** | Do not hand-roll a particle field. `<Stars>` is four lines |

**Honesty constraint (P8 Exception 01, unchanged):** every frame of real solar imagery
carries `ILLUSTRATIVE · SDO / NASA · NOT ADITYA-L1 DATA`. Removing that watermark is a
regression that must fail review. NASA attribution is *also* required by NASA's own
guidelines, so the watermark satisfies both scientific honesty and licence compliance
simultaneously.

**Audio warning:** SVS videos may embed licensed music. Strip audio on transcode
(`-an` in ffmpeg). This is the one way NASA content can carry a non-public-domain
encumbrance.

---

## 3. 3D runtime

| Purpose | Existing library / asset | Licence | Community maturity | Performance | Integration difficulty | Reason for choosing it |
|---|---|---|---|---|---|---|
| WebGL engine | **three.js** | MIT | The de facto WebGL standard; enormous ecosystem | Baseline | Already integrated | No alternative worth considering |
| React renderer | **@react-three/fiber** | MIT | The standard React↔three binding | Zero overhead vs raw three; reconciles outside React for frame loops | Already integrated | Lets the frame loop read a ref, never React state |
| 3D helpers | **@react-three/drei** | MIT | The standard R3F helper library | Per-helper; import granularly | **Low** | `<Text>`, `<useTexture>`, `<Html>`, `<ScrollControls>`, `<Stars>`, `<Billboard>`, `<Line>` — all previously hand-built. **See note below** |
| Bloom / post FX | **@react-three/postprocessing** + **postprocessing** | MIT / Zlib | pmndrs-maintained, widely deployed | Already tuned: intensity 0.5, threshold 0.9, `resolutionScale 0.5` | Already integrated | Keep existing tuning |
| glTF loading | **three `GLTFLoader` + `DRACOLoader`** | MIT | Bundled with three | Draco decode in worker | **Low** | No extra dependency; NASA models already ship Draco-compressed |

> **drei is cleared for reintroduction.** drei was previously blamed for an
> `Invalid hook call` that blanked the prototype. That diagnosis was wrong and is now
> disproven: the crash was a plain `ReferenceError` (an undeclared `useState`), compounded
> by a Vite HMR double-`createRoot`. `npm ls react` confirmed a single deduped React 19.2.8
> throughout. See ISSUE-027. **drei carries no known defect here** — its `<Text>` (SDF text
> via troika) removes the DOM-caption workaround entirely.

---

## 4. Sequencing, scroll & transitions — *the originality layer*

This is where AdityaNet is allowed to be distinctive. Even here, the **mechanism** is
imported; only the **choreography** is ours.

| Purpose | Existing library / asset | Licence | Community maturity | Performance | Integration difficulty | Reason for choosing it |
|---|---|---|---|---|---|---|
| Timeline / sequencing | **GSAP core + ScrollTrigger** | Free "no charge" (verified) | ~15+ years, the industry standard for exactly this genre of site | Highly optimised; `scrub` drives our pure `derive(t)` | **Medium** — one integration point | The single best fit for a scroll-driven cinematic. Now free *including* ScrollTrigger, which historically was the paid blocker. Keeps our existing pure-function timeline: ScrollTrigger supplies `t`, `derive(t)` stays untouched and unit-testable |
| Smooth scroll | **Lenis** | MIT | The current standard (darkroom.engineering) | RAF-driven, lightweight | **Low** | Native scroll feels wrong for a cinematic; Lenis is the accepted fix and integrates with ScrollTrigger in ~10 lines |
| DOM transitions | **Motion** (`motion`) | MIT | Successor to Framer Motion, very widely used | Compositor-friendly transforms | **Low** | For evidence panels/captions. Do **not** animate these with GSAP too — one tool per layer |
| Cross-surface transitions | **Astro native View Transitions** | MIT | Browser-native (with polyfill) | Free — no JS animation | Already integrated | Already working; keep |
| Debug/tuning UI | **Leva** | MIT | Standard pmndrs tuning panel | Dev-only, tree-shaken from prod | **Low** | Tune choreography without recompiles. Must be dev-only |

**Deliberate rejection — Theatre.js** (Apache-2.0): a genuinely excellent visual sequencer,
but it wants to *own* the animation state and persist keyframes to JSON. That conflicts
with our pure, reproducible, scrubbable `derive(t)` — which is a scientific-reproducibility
property, not a stylistic one. Rejected on architectural grounds, not quality.

---

## 5. Evidence presentation (Register B)

Hard constraint: evidence surfaces ship **~0 KB JS**. Charts must render server-side or as
static SVG wherever possible.

| Purpose | Existing library / asset | Licence | Community maturity | Performance | Integration difficulty | Reason for choosing it |
|---|---|---|---|---|---|---|
| Light curves (1440 pts/day) | **uPlot** | MIT | Mature; the recognised performance leader for dense time series | ~45 KB min; renders 1440 pts in low single-digit ms; canvas-based | **Low–Medium** | Purpose-built for exactly this shape of data. Only for *interactive* curves |
| Static/SSR charts | **@observablehq/plot** + **d3** | ISC | Observable-maintained; d3 is the lineage standard | Run at **build time → inline SVG → 0 KB client JS** | **Medium** | Preserves the 0 KB budget. This is the default for evidence surfaces |
| Viridis / perceptual colour | **d3-scale-chromatic** | ISC | Canonical implementation | Trivial | **Low** | The Bible mandates viridis for Register B. Import it; do not transcribe colour ramps by hand |
| Tabular/numeric type | **IBM Plex Mono** or **JetBrains Mono** | SIL OFL 1.1 | Both widely deployed | Subset + `woff2`, self-hosted | **Low** | True tabular figures for measured values. OFL permits self-hosting |
| UI type | **Inter** | SIL OFL 1.1 | Ubiquitous | Subset + `woff2` | **Low** | Self-host — **never** Google Fonts CDN (GDPR + a third-party request on every load) |
| Icons | **Lucide** | ISC | Very widely adopted | Tree-shaken per-icon SVG | **Low** | No icon should ever be drawn by hand |

---

## 6. Application shell

| Purpose | Existing library / asset | Licence | Community maturity | Performance | Integration difficulty | Reason for choosing it |
|---|---|---|---|---|---|---|
| Framework | **Astro** | MIT | Mature; islands architecture is its core competence | 0 KB JS by default — exactly our evidence constraint | Already integrated | Already delivering six surfaces. Keep |
| 3D state | **zustand** | MIT | Standard in the R3F ecosystem (already a transitive dep of fiber) | Minimal; subscribe outside React | **Low** | Already present transitively — promoting it to direct costs **zero** additional bytes |

---

## 7. The spacecraft — the one genuine exception

**This is the only place I recommend against importing, and the reasoning is not
"we can do it better."**

What I verified:

- **NASA 3D Resources has no Aditya-L1.** It is an ISRO mission; NASA's public-domain
  library does not cover it.
- Every Aditya-L1 model located is **third-party stock**: [CGTrader (~$4)](https://www.cgtrader.com/3d-models/space/spaceship/isro-aditya-l1-3d-model-india-mission-to-sun),
  [Sketchfab Store](https://sketchfab.com/3d-models/aditya-l1-satellite-89fe9cc3359e410ba285862dec53e5dc),
  [Sketchfab Store](https://sketchfab.com/3d-models/aditya-l1-6658e75eb32240d6a485227564ad2938).
  One is described as built "using images from ISRO's website."
- I could **not** confirm a CC-BY / CC0 Aditya-L1 model. The one non-store candidate did
  not state its licence on the page.

These fail on **two independent grounds:**

1. **Licence — redistribution.** Stock-3D royalty-free licences typically forbid
   redistributing the asset in a form permitting extraction. A `.glb` served to a browser
   is *inherently* downloadable by any visitor. Web delivery of purchased stock geometry is
   therefore a genuine licence risk, not a theoretical one. This alone disqualifies it
   absent written confirmation from the seller.
2. **Scientific honesty (P8) — this is the disqualifying one.** These are *artists'
   interpretations*, not engineering data. Presenting fan-made geometry as Aditya-L1's
   structure claims a fidelity no source backs. That is precisely the failure mode
   AdityaNet exists to repudiate. **A purchased photoreal model would make the project less
   honest, not more finished.**

Rejected outright: substituting a NASA public-domain satellite (e.g. SAC-C). Showing the
wrong spacecraft is a straightforward misrepresentation.

### Recommendation

**Keep the existing primitive-based schematic** (`Spacecraft.jsx`, ~120 lines: a box bus,
two plane wings, seven labelled payload markers). Rationale:

- It is **not a "custom spacecraft model."** It is a *diagram assembled from three.js
  primitives* — the cheapest possible construction, already written, already working.
- Register S **requires** it to look like a diagram. A photoreal mesh would be the *wrong
  register* even if it were free and perfectly licensed.
- It carries **zero licence risk** and **zero new dependencies**.
- The seven payload **names** (SUIT, VELC, HEL1OS, ASPEX, PAPA, MAG, SoLEXS) are facts, not
  copyrightable expression — citing them to ISRO/eoPortal is safe. **ISRO's diagrams and
  photographs are a different matter: treat as ©ISRO / all-rights-reserved unless a
  specific open licence is confirmed. Do not vendor ISRO imagery on the current evidence.**

Improvement here is **imported, not built**: replace the DOM-caption workaround with
drei `<Text>` / `<Billboard>` for in-scene labels. Net effect — *less* custom code than today.

---

## 8. Proposed dependency manifest

```
# runtime — 3D
three                          MIT
@react-three/fiber             MIT
@react-three/drei              MIT
@react-three/postprocessing    MIT
postprocessing                 Zlib

# runtime — motion
gsap                           free "no charge" (incl. ScrollTrigger)
lenis                          MIT
motion                         MIT

# runtime — evidence
uplot                          MIT
d3-scale-chromatic             ISC

# build-time only (0 KB client)
@observablehq/plot             ISC
d3                             ISC

# shell
astro                          MIT
zustand                        MIT   (already transitive)

# dev only
leva                           MIT
```

**Self-hosted assets:** Inter + IBM Plex Mono (OFL 1.1, subset woff2); Lucide icons (ISC);
SDO stills (public domain, present); one transcoded SVS solar clip, audio stripped
(public domain).

**Net new runtime dependencies: 6** (drei, gsap, lenis, motion, uplot, d3-scale-chromatic).
Everything else is already installed or build-time only.

---

## 9. Budgets and risks

| Risk | Mitigation |
|---|---|
| Video weight on the hero | Transcode to 1080p + 720p, H.264 + WebM, `preload="none"`, `poster` = existing SDO still. Hard ceiling **5 MB**. Still-image path for `prefers-reduced-motion` and mobile |
| SVS licensed-music encumbrance | Strip audio at transcode (`-an`). Verify each clip's page for a "licensed music" note before vendoring |
| Bundle growth from drei | Import per-helper (`drei/core/Text`), never the barrel. Re-measure gz after integration |
| Evidence surfaces gaining JS | Observable Plot runs at **build time** → inline SVG. uPlot only where interaction is genuinely required. Assert 0 KB in CI |
| Two animation systems fighting | Strict split: **GSAP owns scroll→`t`**; **Motion owns DOM element transitions**. Never both on one property |
| NASA attribution | Already satisfied by the mandatory P8 watermark |
| **Frame cost still unmeasured** | Unresolved and carried forward (ISSUE-023). The automated pane throttles rAF to zero, so 60 fps remains **unverified on real hardware**. Video-texture compositing is far cheaper than the procedural shader it replaces, so the change is directionally favourable — but that is reasoning, not measurement, and must not be reported as a result |

---

## 10. What this plan deletes

Integration is a subtraction exercise. On adoption, these are removed:

- The procedural Sun shader stack — `star.frag/vert`, `corona.*`, `chromosphere.frag`,
  `glow.*`, `prominence.frag`, `noise.glsl` (~600 lines of GLSL) → **replaced by a `<video>` element**
- Hand-rolled scroll/rAF timeline driving → **GSAP ScrollTrigger**
- The DOM payload-caption workaround → **drei `<Text>`**
- Any hand-drawn chart axes/scales → **Observable Plot / uPlot**

`derive(t)` **survives unchanged** — it is the reproducibility contract, and it is ours.

---

## 11. Open questions for the owner

1. **Solar clip selection** — pick one SVS clip (flare event vs. slow rotation). Recommend a
   slow-rotation loop for the hero: it must not upstage the crossing.
2. **ISRO imagery** — confirmed treated as all-rights-reserved unless you have a licence.
   Blocks nothing; the schematic path avoids it entirely.
3. **Spacecraft** — confirm §7: keep the primitive schematic, decline stock models. If you
   want photoreal, it needs a written redistribution licence *and* a P8 exception, and I'd
   still advise against it on honesty grounds.
