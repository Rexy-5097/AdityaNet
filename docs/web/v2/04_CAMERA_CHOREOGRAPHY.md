# 4 · Camera Choreography

Explicitly one of the six permitted originality sources. This is the shot list.

## 4.1 Principles

1. **The camera is a witness, not a participant.** It observes; it never swoops for thrill.
2. **Every move has a reason** expressible in one sentence. No move survives review without one.
3. **Stillness is a shot.** The most important beats — the crossing, the number — are static.
4. **The camera never moves during a register change.** Register changes happen *to the
   image*. If the camera also moved, the viewer could not tell what changed. This is the
   single most important rule here, inherited from the Bible.
5. **No roll, ever.** Roll is the fastest route to nausea and has no narrative referent.
6. **Focal length carries meaning** — wide for scale, long for scrutiny.

## 4.2 The shot list

| # | Scene | `t` | Shot | Camera move | FOV | Why it exists |
|---|---|---|---|---|---|---|
| 1 | Universe | 0.00–0.08 | Sun fills frame | **Static.** Only the footage moves | 32° | Establish the subject as overwhelming and *real*. Cutting on arrival would waste it |
| 2 | Universe | 0.08–0.12 | Slow pull-back | Dolly out z 4.2→6.2 | 32° | Reveals we were close. Creates room for the observer |
| 3 | Observer | 0.12–0.20 | Craft enters | **Static.** Craft moves into frame | 32° | Motion belongs to the subject, not the lens. Scale reads honestly |
| 4 | Observer | 0.20–0.24 | Rack focus | **Focus only** — DoF plane Sun→craft | 32° | The one cinematic flourish. Transfers attention without moving anything |
| 5 | Dissection | 0.24–0.30 | Orbit begins | Slow arc, ~25° azimuth | 32→40° | Parallax reveals the craft is *volumetric* before it opens |
| 6 | Dissection | 0.30–0.46 | The opening | Continue arc, slight dolly-in | 40° | Sustained single move. Parts separate; the camera stays calm so the geometry reads |
| 7 | Dissection | 0.46–0.48 | **Hold** | **Static, 400 ms** | 40° | The held beat. Seven payloads lit, nothing moving |
| 8 | SoLEXS | 0.48–0.58 | Isolation push | Dolly in, six payloads fade | 40→28° | Longer lens = scrutiny. Physically approaching the subject of the whole project |
| 9 | SoLEXS | 0.58–0.60 | **Lock off** | **Static — and stays static to t=0.82** | 28° | The camera stops for good. Everything after this happens *to the image* |
| 10 | Crossing | 0.60–0.72 | Photon travels | **Static** | 28° | Only the photon moves. Tier-1 motion, alone, uncontested |
| 11 | Crossing | 0.72–0.82 | Collapse | **Static** | 28° | Geometry contracts to a point. A camera move here would destroy the effect |
| 12 | Measured | 0.82–1.00 | — | **Canvas hidden.** DOM only | — | There is no camera in a measurement |

**Six of twelve shots are static.** The stillness ratio *is* the restraint.

## 4.3 The one flourish, and why it's allowed

Shot 4 (rack focus) is the only overtly cinematic gesture. It earns its place because it is
the only technique that transfers attention **without moving anything** — no vestibular
cost, no scale distortion, and it says "look at the small thing now" in a way a cut cannot.
It is also the moment the Sun stops being the subject and becomes the setting, which is the
hinge of the whole storyboard.

## 4.4 Implementation — how this is driven

**Theatre.js is rejected as a runtime dependency.** It is the best camera-authoring tool
available and the [Codrops fly-through technique](https://tympanus.net/codrops/2023/02/14/animate-a-camera-fly-through-on-scroll-using-theatre-js-and-react-three-fiber/)
is the canonical reference — but `@theatre/core` and `@theatre/r3f` last published
**2024-05-19**, ~26 months stale, while every peer shipped within months. Adopting it would
put an unmaintained package on the critical path of the site's signature feature.

**Adopted instead — camera path as data:**

```
CAMERA_KEYFRAMES = [ { t, position, target, fov, focusDistance }, … ]   ← ours (the choreography)
      ↓
THREE.CatmullRomCurve3        ← three core, for position interpolation
THREE.Quaternion.slerp        ← three core, for orientation
maath/easing damp3            ← MIT, for damped follow
      ↓
camera, driven by derive(t)
```

**This is the second and final custom item in the plan, and it is ~40 lines of glue.** The
interpolation, the curve maths, the quaternion slerp and the damping are all imported from
three core and `maath`. What is ours is the **keyframe table** — which is the choreography
itself, i.e. exactly the thing the brief says must be original.

Optional, **design-time only**: use the Theatre.js editor locally to author keyframe values,
then export them as a plain array and delete the dependency. Tool, not runtime.

**Rejected alternative:** drei `<ScrollControls>` + `useScroll` `range/curve` helpers. Clean
and well-maintained, but it owns the scroll container, which conflicts with Lenis + ScrollTrigger
and with Astro's multi-surface routing. Chosen only if the GSAP path proves troublesome.

## 4.5 Reduced-motion camera

Camera *travel* is the primary vestibular risk — large-scale panning and zooming are the
documented triggers. Under `prefers-reduced-motion: reduce`:

| Normal | Reduced |
|---|---|
| Dolly / orbit / push-in | **No travel.** Camera cuts to each shot's end pose |
| Rack focus | Instant, no blur ramp |
| Scroll scrub | Discrete section-to-section cross-fades (300 ms opacity) |
| FOV changes | Applied instantly at the cut |

**Every shot's framing is preserved; only the travel between them is removed.** The story
loses nothing — which is the test of whether the choreography was carrying meaning or just
motion.

## 4.6 Responsive framing

| Viewport | Adaptation |
|---|---|
| Desktop ≥1280 | Full choreography as specified |
| Tablet 768–1279 | FOV +6° throughout; orbit reduced to ~15° |
| Mobile <768 | **Static camera for all shots.** Scenes become cross-fades. Video → still frame. Portrait framing recomposed so the craft is centred, not offset |

Mobile is not a degraded desktop — it is the reduced-motion path, which is already
designed and already honest.
