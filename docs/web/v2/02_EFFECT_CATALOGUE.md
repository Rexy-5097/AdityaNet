# 2 · Effect Catalogue

> ⚠️ **Superseded in part by [Doc 9 · Experience Script](09_EXPERIENCE_SCRIPT.md).**
> The script audit removed **chromatic aberration** and the **star field** from §2.1/§2.3,
> and demoted **film grain** to dither-only. Where this document and Doc 9 disagree, Doc 9
> governs. Authoritative post-audit effect stacks: [Doc 9 §9.11](09_EXPERIENCE_SCRIPT.md).

Every effect below ships in [`pmndrs/postprocessing`](https://github.com/pmndrs/postprocessing)
(Zlib) via `@react-three/postprocessing` (MIT), or in `drei` (MIT), unless stated. **No
custom shader is proposed in this document.**

**Why composition is cheap here:** `EffectPass` "automatically organizes and merges any given
combination of effects," and the library renders through a single screen-filling triangle
rather than a quad. Effects that merge into one pass cost roughly one pass — the naive
"each effect = one full-screen pass" mental model does not apply. **Depth-sampling effects
(DoF, SSAO, God Rays) are the exception and do not merge.**

**Cost legend:** ▁ negligible · ▃ low · ▅ moderate · ▇ heavy (measure before shipping)

---

## 2.1 Adopted — Register A (Artistic)

| Effect | Communicates | Where in AdityaNet | Perf | Browser support | Accessibility | Composable? |
|---|---|---|---|---|---|---|
| **Bloom** (`BloomEffect`, mipmap blur) | "This light is physically overwhelming" — the Sun exceeds the sensor | Scene 1 only. Dies completely by the drain | ▃ at `resolutionScale 0.5` | WebGL2 universal | Can raise luminance; must respect reduced-motion by holding static, and cap intensity | **Yes** — merges in `EffectPass` |
| **Depth of Field** (`DepthOfFieldEffect`) | Attention. A shallow plane says *look here, not there* | Scene 1→2: Sun sharp, craft soft; rack focus as the craft arrives | ▅ — depth pass, **does not merge** | WebGL2 universal | Blur can disorient; disable under reduced motion, keep everything sharp | Partial — separate pass |
| **Vignette** (`VignetteEffect`) | Framing. Turns a viewport into a *shot* | Scenes 1–4, subtle (offset ~0.3) | ▁ | Universal | None | **Yes** |
| **Noise / film grain** (`NoiseEffect`) | Photographic authenticity; hides gradient banding on dark backgrounds | Scenes 1–2 at very low opacity (~0.02–0.04) | ▁ | Universal | Static grain is safe; **must not animate** under reduced motion (flicker risk) | **Yes** |
| **Chromatic aberration** (`ChromaticAberrationEffect`) | Lens realism — an *instrument* recorded this | Scene 1 only, near-imperceptible (≤0.0005) | ▁ | Universal | Colour fringing can affect low vision; keep below perceptual threshold | **Yes** |
| **SMAA** (`SMAAEffect`) | Nothing — it removes an artefact | Global | ▃ | Universal | Improves legibility of wireframe edges | **Yes** |

## 2.2 Adopted — the register pivot (the most important row in this document)

| Effect | Communicates | Where in AdityaNet | Perf | Browser support | Accessibility | Composable? |
|---|---|---|---|---|---|---|
| **LUT colour grading** (`LUTEffect`, 3D texture) | **Certainty.** Warm=interpretation, cool=structure, neutral=measurement | The whole A→S→B spine. Three LUTs, cross-faded by `t` | ▁ — a 3D texture lookup | WebGL2 (3D textures) universal in target browsers | Must not be the *only* channel carrying meaning — watermark text carries it too | **Yes** |

**This replaces the entire "drain" shader.** v1 hand-wrote desaturation and flattening in
GLSL. A LUT does it better, is authored in any grading tool, is swappable without a
recompile, and costs one texture fetch. The project's central visual idea — *certainty has a
colour temperature* — is a stock effect.

## 2.3 Adopted — Register S (Schematic)

| Effect | Communicates | Where in AdityaNet | Perf | Browser support | Accessibility | Composable? |
|---|---|---|---|---|---|---|
| **Grid** (`GridEffect`) | "You are now reading a diagram, not a photograph" | Rises during the drain; present through Scenes 3–4 | ▁ | Universal | Fine repeating patterns can trigger discomfort — keep scale coarse, opacity low, **never animate the pattern** | **Yes** |
| **Outline** (`OutlineEffect`) | Selection. "*This* object is the subject" | Payload isolation — SoLEXS outlined while six siblings fade. Also hover states | ▃ | WebGL2 universal | **Must pair with a text label** — outline alone fails colour-blind users and screen readers | Partial |
| **drei `<Text>`** (SDF via troika) | Labels that stay crisp at any camera distance | All payload//axis labels in-scene | ▃ | Universal | **Not screen-reader accessible** — every in-scene label must be mirrored in the DOM layer | Yes |
| **drei `<Line>`** (fat lines) | Precise schematic linework at consistent width | Payload leaders, aperture, photon path | ▁ | Universal | Decorative — mark `aria-hidden` | Yes |

## 2.4 Adopted — transition moments

| Effect | Communicates | Where in AdityaNet | Perf | Browser support | Accessibility | Composable? |
|---|---|---|---|---|---|---|
| **Tone mapping swap** (ACES → None) | The image stops being *photographed* and starts being *plotted* | At the S→B boundary | ▁ | Universal | None | Yes |
| **`VideoTexture`** (three core) | The Sun, imported not invented | Scene 1 | ▃ decode; ▁ GPU | Universal; **iOS needs `playsinline` + `muted`** | Must honour reduced-motion → swap to still frame; must not autoplay with sound | Yes |

## 2.5 Rejected — and why

Rejection reasoning matters as much as adoption. Each of these is technically excellent and
wrong *here*.

| Effect | Why rejected |
|---|---|
| **God Rays** | Beautiful, and the single most tempting effect for a solar site. Rejected: it is a **volumetric interpretation** of light we did not measure, drawn over footage of a real Sun. It would be the exact class of "looks like data, isn't" the project exists to repudiate. Also ▇ and non-merging |
| **Glitch** | Fails the dishonesty test outright — implies signal corruption that never occurred |
| **Scanline / Dot-screen** | Sci-fi UI cosplay. Implies a CRT/instrument readout that does not exist |
| **Pixelation** | Considered for the collapse; rejected — implies resolution loss, when the collapse is a *gain* in certainty |
| **Shock Wave** | Considered for photon impact; rejected as spectacle. A single frame of stillness communicates the same thing with more authority |
| **SSAO** | Ambient occlusion needs lit geometry. Register S is deliberately unlit. Zero benefit, ▅ cost |
| **Bloom in Register S or B** | Explicitly forbidden. Bloom on a measurement implies emission the data does not claim |
| **`MeshTransmissionMaterial`** (drei) | Superb glass/crystal material, genuinely mature. Nothing in AdityaNet is made of glass. Rejected for having no referent |
| **Particle systems / GPGPU** | No physical process in our story is particulate at the scale shown. Decoration only |
| **`MeshReflectorMaterial`** | Implies a floor/stage. There is no ground in space |
| **Parallax on multiple layers** | Vestibular risk (background moving at a different rate is a documented trigger) for negligible gain |

---

## 2.6 Effect stack per scene

Enforcing the **≤3 simultaneous effects** cap from Doc 1 §1.4:

| Scene | `t` | Effect stack | Count |
|---|---|---|---|
| 1 · Universe | 0.00–0.12 | LUT(warm) + Bloom + Vignette · *(+ DoF at the rack-focus beat only)* | 3–4 |
| 2 · Observer | 0.12–0.24 | LUT(warm→cool) + Bloom(dying) + Vignette | 3 |
| 3 · Dissection | 0.24–0.48 | LUT(cool) + Grid + Vignette | 3 |
| 4 · SoLEXS | 0.48–0.60 | LUT(cool) + Grid + Outline | 3 |
| 5 · Crossing | 0.60–0.82 | LUT(cool→neutral) + Vignette(opening out) | 2 |
| 6 · Measured | 0.82–1.00 | **none — canvas hidden, DOM only** | 0 |

Grain and SMAA sit outside this count (SMAA is corrective; grain is ▁ and constant through
1–2). The stack **monotonically simplifies** as certainty rises — visual restraint tracks
epistemic confidence. That is the whole argument of the site, expressed as a render budget.

## 2.7 Global accessibility contract

1. **`prefers-reduced-motion: reduce`** → camera choreography becomes cross-fades; video
   becomes a still; DoF disabled; grain frozen; scroll-scrub becomes discrete section jumps.
   Guidance is explicit that large-scale movement (parallax, zoom, panning) is the vestibular
   trigger, while opacity fades are the safe substitute — so the reduced path keeps every
   *state change* and removes only the *travel between* them.
2. **An on-page motion toggle**, independent of the OS setting, persisted to `localStorage`.
   Recommended practice where parallax/scroll effects are core.
3. **The story must be fully readable without WebGL.** Canvas is enhancement; every claim
   exists in DOM text. WebGL failure or a blocked context degrades to the static path — no
   error state, no missing content.
4. **In-scene text is not accessible.** Every drei `<Text>` label is mirrored in a visually
   hidden DOM element in reading order.
5. **No effect is the sole carrier of meaning.** Outline pairs with a label; LUT register
   shift pairs with the watermark string.
6. **No flashing** above 3 Hz anywhere — this includes the collapse flash, which must be a
   single eased ramp, not a strobe.
