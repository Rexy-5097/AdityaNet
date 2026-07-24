/**
 * The camera subsystem — narrative infrastructure, not animation.
 *
 * Governed by docs/web/v2/04_CAMERA_CHOREOGRAPHY.md (the shot list) and the Experience
 * Script (docs/web/v2/09_EXPERIENCE_SCRIPT.md). Every keyframe below carries a `shot`
 * number and a `scriptRef` back to the moment it serves. A keyframe with no documented
 * moment is not permitted — the traceability test enforces this.
 *
 * Design choices that turn the choreography's rules into structural guarantees rather than
 * things we merely try to honour:
 *
 *   - The camera is parameterised in SPHERICAL coordinates (azimuth, elevation, radius)
 *     around a look target. An orbit is "interpolate azimuth"; a dolly is "interpolate
 *     radius". Each documented move maps to exactly one scalar.
 *
 *   - World-up is fixed at +Y and orientation is always derived by looking at the target.
 *     The camera's right vector is therefore (-forward.z, 0, forward.x) — its Y component
 *     is identically zero. NO ROLL IS POSSIBLE (Doc 4 §4.1 rule 5). The test documents
 *     this; the maths guarantees it.
 *
 *   - A static shot is encoded as two adjacent keyframes with identical pose. Interpolation
 *     between identical endpoints is constant regardless of easing, so "provably static"
 *     (Doc 4 §4.2, six of twelve shots) is exact, not approximate.
 *
 *   - Every non-static segment eases with smoothstep, whose derivative is zero at both
 *     ends. Camera velocity is therefore zero at every keyframe — including the register
 *     boundaries at t=0.24 and t=0.82, satisfying "the camera never moves during a
 *     register change" (Doc 4 §4.1 rule 4), the single most important rule here.
 *
 * This module is pure and three.js-free so it runs in the node test environment. Slice 3
 * applies its output to an actual PerspectiveCamera.
 */

export interface Vec3 {
  readonly x: number;
  readonly y: number;
  readonly z: number;
}

export interface CameraPose {
  readonly position: Vec3;
  readonly target: Vec3;
  /** Vertical field of view, degrees. Doc 4: wide = scale, long = scrutiny. */
  readonly fov: number;
  /** Rack-focus scalar. 0 = focus on the Sun, 1 = focus on the craft (Script §9.3). */
  readonly focus: number;
  /** Always world-up. Present so the render adapter never has to guess. */
  readonly up: Vec3;
}

type Ease = "hold" | "smooth";

interface Keyframe {
  readonly t: number;
  readonly shot: number;
  readonly scriptRef: string;
  /** Degrees, measured from +Z toward +X. */
  readonly azimuth: number;
  /** Degrees above the equatorial plane. Kept well inside ±90° to avoid gimbal/roll. */
  readonly elevation: number;
  readonly radius: number;
  readonly target: Vec3;
  readonly fov: number;
  readonly focus: number;
  /** How to ease *into* this keyframe from the previous one. */
  readonly ease: Ease;
}

const ORIGIN: Vec3 = { x: 0, y: 0, z: 0 };

/**
 * The shot list, as data. This table IS the choreography — the one piece Doc 6 §6.4 lists
 * as legitimately custom, because the brief names camera choreography as an originality
 * source. Positions are authored; the interpolation and vector maths are imported.
 */
export const CAMERA_KEYFRAMES: readonly Keyframe[] = [
  // Shot 1 — Sun fills frame. Static. Only the footage moves. (Script §9.2)
  { t: 0.0, shot: 1, scriptRef: "§9.2 Universe — arrival", azimuth: 0, elevation: 0, radius: 4.2, target: ORIGIN, fov: 32, focus: 0, ease: "hold" },
  { t: 0.08, shot: 1, scriptRef: "§9.2 Universe — arrival (hold)", azimuth: 0, elevation: 0, radius: 4.2, target: ORIGIN, fov: 32, focus: 0, ease: "hold" },
  // Shot 2 — slow pull-back. Reveals we were close; makes room for the observer. (Script §9.2)
  { t: 0.12, shot: 2, scriptRef: "§9.2 Universe — pull-back", azimuth: 0, elevation: 0, radius: 6.2, target: ORIGIN, fov: 32, focus: 0, ease: "smooth" },
  // Shot 3 — craft enters, camera static. Scale reads honestly. (Script §9.3)
  { t: 0.2, shot: 3, scriptRef: "§9.3 Observer — craft enters", azimuth: 0, elevation: 0, radius: 6.2, target: ORIGIN, fov: 32, focus: 0, ease: "hold" },
  // Shot 4 — rack focus ONLY. Nothing translates; attention transfers Sun→craft. (Script §9.3)
  { t: 0.24, shot: 4, scriptRef: "§9.3 Observer — rack focus", azimuth: 0, elevation: 0, radius: 6.2, target: ORIGIN, fov: 32, focus: 1, ease: "smooth" },
  // Shot 5 — HOLD while the schematic register establishes (grid rises, LUT cools). The
  // camera is calm precisely during the A→S register change. CORRECTION C3: the original
  // §4.2 began the orbit at t=0.24, which collided with the register boundary and broke
  // §4.1 rule 4 ("no motion during a register change") — the rule §4.1 names as most
  // important. When §4.2's timing conflicts with rule 4, rule 4 wins. (Script §9.4)
  { t: 0.3, shot: 5, scriptRef: "§9.4 Dissection — schematic establishes (hold)", azimuth: 0, elevation: 0, radius: 6.2, target: ORIGIN, fov: 32, focus: 1, ease: "hold" },
  // Shot 6 — the opening: a single sustained arc + dolly-in + FOV widen as the craft opens.
  // Merging the former shots 5 and 6 into one move honours "one primary mover" (Doc 1 §1.2).
  { t: 0.46, shot: 6, scriptRef: "§9.4 Dissection — the opening", azimuth: 40, elevation: 10, radius: 4.8, target: ORIGIN, fov: 40, focus: 1, ease: "smooth" },
  // Shot 7 — HOLD. Seven payloads lit, nothing moving. (Script §9.4/§9.5 the 400 ms hold)
  { t: 0.48, shot: 7, scriptRef: "§9.5 SoLEXS — the hold", azimuth: 40, elevation: 10, radius: 4.8, target: ORIGIN, fov: 40, focus: 1, ease: "hold" },
  // Shot 8 — isolation push. Longer lens = scrutiny; physically approaching SoLEXS. (Script §9.5)
  { t: 0.58, shot: 8, scriptRef: "§9.5 SoLEXS — isolation push", azimuth: 40, elevation: 6, radius: 3.4, target: ORIGIN, fov: 28, focus: 1, ease: "smooth" },
  // Shot 9 — lock off. The camera stops for good. (Script §9.6)
  { t: 0.6, shot: 9, scriptRef: "§9.6 Crossing — lock off", azimuth: 40, elevation: 6, radius: 3.4, target: ORIGIN, fov: 28, focus: 1, ease: "hold" },
  // Shots 10–11 — everything now happens TO the image. Camera static to the collapse. (Script §9.6/§9.7)
  { t: 0.82, shot: 11, scriptRef: "§9.7 Collapse — camera still", azimuth: 40, elevation: 6, radius: 3.4, target: ORIGIN, fov: 28, focus: 1, ease: "hold" },
] as const;

/**
 * The documented shot-boundary times from Doc 4 §4.2. Every keyframe time must be one of
 * these — a keyframe cannot land at an undocumented instant. Exported so the test can
 * assert the correspondence rather than trusting the table above.
 */
export const DOCUMENTED_SHOT_BOUNDARIES: readonly number[] = [
  0.0, 0.08, 0.12, 0.2, 0.24, 0.3, 0.46, 0.48, 0.58, 0.6, 0.82,
] as const;

/** Register-change instants (Doc 4 §4.1 rule 4). The camera must be at rest at each. */
export const REGISTER_BOUNDARIES: readonly number[] = [0.24, 0.82] as const;

const DEG = Math.PI / 180;
const clamp01 = (x: number): number => (x < 0 ? 0 : x > 1 ? 1 : x);
const lerp = (a: number, b: number, u: number): number => a + (b - a) * u;
const smoothstep = (u: number): number => {
  const c = clamp01(u);
  return c * c * (3 - 2 * c);
};
const lerpVec = (a: Vec3, b: Vec3, u: number): Vec3 => ({
  x: lerp(a.x, b.x, u),
  y: lerp(a.y, b.y, u),
  z: lerp(a.z, b.z, u),
});

/** Spherical (deg, deg, r) around `target` → world position. az=0,el=0 places +Z. */
function sphericalToCartesian(azimuthDeg: number, elevationDeg: number, radius: number, target: Vec3): Vec3 {
  const az = azimuthDeg * DEG;
  const el = elevationDeg * DEG;
  const cosEl = Math.cos(el);
  return {
    x: target.x + radius * cosEl * Math.sin(az),
    y: target.y + radius * Math.sin(el),
    z: target.z + radius * cosEl * Math.cos(az),
  };
}

const WORLD_UP: Vec3 = { x: 0, y: 1, z: 0 };

function poseOf(kf: Keyframe): CameraPose {
  return {
    position: sphericalToCartesian(kf.azimuth, kf.elevation, kf.radius, kf.target),
    target: kf.target,
    fov: kf.fov,
    focus: kf.focus,
    up: WORLD_UP,
  };
}

export interface CameraOptions {
  /**
   * Doc 4 §4.5: under prefers-reduced-motion the camera CUTS to each shot's end pose —
   * no travel, which is the documented vestibular trigger. Every shot's framing is
   * preserved; only the movement between frames is removed.
   */
  readonly reducedMotion?: boolean;
}

/**
 * The camera pose at position `t` in the arc. Pure: same `t` (and options) → same pose,
 * always. No clock, no state — the reproducibility contract extends to the camera.
 */
export function cameraAt(t: number, options: CameraOptions = {}): CameraPose {
  const kfs = CAMERA_KEYFRAMES;
  const first = kfs[0]!;
  const last = kfs[kfs.length - 1]!;

  const clamped = Number.isFinite(t) ? t : 0;
  if (clamped <= first.t) return poseOf(first);
  if (clamped >= last.t) return poseOf(last);

  // Locate the active segment [a, b].
  let a = first;
  let b = last;
  for (let i = 1; i < kfs.length; i += 1) {
    const prev = kfs[i - 1]!;
    const next = kfs[i]!;
    if (clamped >= prev.t && clamped < next.t) {
      a = prev;
      b = next;
      break;
    }
  }

  // Reduced motion: cut to the segment's destination pose. No interpolation, no travel.
  if (options.reducedMotion) return poseOf(b);

  // A hold segment is constant by construction. Returning early keeps static shots exact.
  if (b.ease === "hold" || b.t === a.t) return poseOf(a);

  const raw = (clamped - a.t) / (b.t - a.t);
  const u = smoothstep(raw);

  return {
    position: sphericalToCartesian(
      lerp(a.azimuth, b.azimuth, u),
      lerp(a.elevation, b.elevation, u),
      lerp(a.radius, b.radius, u),
      lerpVec(a.target, b.target, u),
    ),
    target: lerpVec(a.target, b.target, u),
    fov: lerp(a.fov, b.fov, u),
    focus: lerp(a.focus, b.focus, u),
    up: WORLD_UP,
  };
}

// --- small vector helpers, exported for the invariant tests ---

export function sub(a: Vec3, b: Vec3): Vec3 {
  return { x: a.x - b.x, y: a.y - b.y, z: a.z - b.z };
}
export function length(a: Vec3): number {
  return Math.hypot(a.x, a.y, a.z);
}
export function normalize(a: Vec3): Vec3 {
  const l = length(a) || 1;
  return { x: a.x / l, y: a.y / l, z: a.z / l };
}
export function cross(a: Vec3, b: Vec3): Vec3 {
  return {
    x: a.y * b.z - a.z * b.y,
    y: a.z * b.x - a.x * b.z,
    z: a.x * b.y - a.y * b.x,
  };
}

/**
 * The camera's right vector — the horizon line. Its Y component is the roll indicator:
 * a level horizon has right.y === 0. See the module header for why this is structural.
 */
export function rightVector(pose: CameraPose): Vec3 {
  const forward = normalize(sub(pose.target, pose.position));
  return normalize(cross(forward, pose.up));
}
