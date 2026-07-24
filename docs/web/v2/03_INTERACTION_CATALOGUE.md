# 3 · Interaction Catalogue

> ⚠️ **Superseded in part by [Doc 9 · Experience Script](09_EXPERIENCE_SCRIPT.md).**
> The script audit removed **cursor proximity damping** and **magnetic controls** from §3.3.
> Where this document and Doc 9 disagree, Doc 9 governs.

Interaction design is one of the six permitted originality sources. The *mechanisms* below
are still imported; the *choreography* is ours.

## 3.1 Motion hierarchy — the governing rule

At any instant, motion is ranked. **Exactly one element occupies tier 1.**

| Tier | Role | Amplitude | Example |
|---|---|---|---|
| **1 · Primary** | The subject of the current beat | 100% | The spacecraft dissecting |
| **2 · Supporting** | Reacts to the primary | ≤20% | Sun receding behind it |
| **3 · Ambient** | Context only | ≤5%, or static | Star field |
| **4 · Inert** | Does not move | 0 | Watermark, chrome, evidence text |

Violating this is the most common way a cinematic site becomes noise. Review rejects any
frame with two tier-1 movers.

## 3.2 Scroll — the spine

| Interaction | Library | Behaviour | Accessibility |
|---|---|---|---|
| Smooth scroll | **Lenis** (MIT, v1.3.25, published 2026-07-15) | Damped scroll; native scrollbar retained | **Never seizes control.** Disabled under reduced motion. Keyboard/spacebar/Page-Up-Down all work natively |
| Scroll → `t` | **GSAP ScrollTrigger** (free licence) | `scrub: 1` maps scroll offset to `t ∈ [0,1]`, feeding `derive(t)` | Section anchors let keyboard users jump without scrubbing |
| Section pinning | ScrollTrigger `pin` | Pins the canvas while a scene plays | Pin duration capped so the page never feels stuck |
| Chapter navigation | DOM `<nav>` + `scrollTo` | Named jumps: Universe / Observer / Dissection / SoLEXS / Crossing / Evidence | **Primary navigation for keyboard and reduced-motion users** |

**`derive(t)` remains the authority.** ScrollTrigger only *supplies* `t`. The pure function
stays unit-testable and reproducible — a scientific-reproducibility property, not a
stylistic one. Any instant is addressable by URL (`?t=0.54`).

## 3.3 Microinteractions

Small, earned, never ambient.

| Interaction | Where | Library | Notes |
|---|---|---|---|
| **Payload hover** | Scene 3–4 | drei `Outline` + `<Text>` | Hover a payload → outline + label + one-line description. The *only* free exploration in the piece |
| **Cursor proximity damping** | Scenes 2–4 | `maath/easing` `damp3` | Camera yaw shifts ≤1.5° toward cursor. Parallax-of-intent, not decoration. **Off** under reduced motion |
| **Magnetic controls** | Chrome | Motion | Buttons ease toward cursor within ~8 px. Standard Awwwards-vocabulary microinteraction, used sparingly |
| **Light-curve inspection** | Register B | **uPlot** cursor | Hover a minute → exact value + UTC timestamp. The payoff interaction: *the data is real, inspect it* |
| **Evidence disclosure** | Register B | Motion | Click any number → artefact name, JSON pointer, hash. **Every number is traceable in one click** |
| **Watermark persistence** | Global | DOM | Never fades below 0.5 opacity. Not decorative — a scientific-integrity control |

## 3.4 Focus, keyboard, and the sceptic's path

| Requirement | Implementation |
|---|---|
| Full keyboard traversal | Every scene reachable via chapter nav; `Tab` order matches reading order |
| Visible focus | 2 px `#8fb8ff` outline, never suppressed |
| Skip link | "Skip to evidence" as the **first** focusable element — a sceptic must be able to bypass all cinematics in one keystroke |
| Reduced-motion path | Cross-fades between scene states; no scrub, no travel |
| No-WebGL path | Static SDO still + full DOM narrative + all evidence |
| Screen reader | In-scene labels mirrored in visually-hidden DOM; canvas `aria-hidden` |

> **The sceptic's path is a first-class feature, not a fallback.** A scientist who distrusts
> the cinematics must reach the light curve, the artefact hash, and the negative ML result
> without watching a single frame of animation. If the story is honest, skipping it costs
> nothing.

## 3.5 Timing and easing

| Beat | Duration | Easing |
|---|---|---|
| Register change (A→S, S→B) | 800–1200 ms | `power2.inOut` |
| Held beat before each change | ~400 ms stillness | — |
| Micro (hover, focus) | 120–180 ms | `power2.out` |
| Camera moves | 1.5–3 s | `power2.inOut`, or damped follow |
| Number resolve | 600 ms | `power3.out`, tabular figures |
| Light curve draw | 1200 ms | `none` — **linear, because it is time-series data**; an eased draw would misrepresent the time axis |

That last row is the pattern for the whole project: even easing is subject to the honesty
test.

## 3.6 Forbidden interactions

- Scroll-jacking that blocks or hijacks native scroll
- Cursor trails, custom cursor replacement, magnetic effects on non-interactive elements
- Autoplaying audio
- Hover-only affordances (fails touch and keyboard)
- Any "loading" theatre that fakes work that isn't happening
- Counters that spin up to a value — a measured number appears; it does not perform
