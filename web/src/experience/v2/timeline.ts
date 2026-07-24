/**
 * The `derive(t)` contract — v2 experience timeline.
 *
 * One scalar `t ∈ [0,1]` drives the entire cinematic arc. Everything the scene, the
 * post-processing stack and the DOM overlay need is derived here, purely.
 *
 * Governed by docs/web/v2/09_EXPERIENCE_SCRIPT.md (the Experience Script). Scene
 * boundaries follow §9.2–9.9; the post-audit effect stacks follow §9.11. No field exists
 * in this file unless a scene in the Script asks for it.
 *
 * Why pure (docs/web/v2/07_FRONTEND_ARCHITECTURE.md §7.4): reproducibility is a scientific
 * property here, not a stylistic one. No clock, no randomness, no `Math.random`, no reads
 * of external state. The same `t` yields the same frame forever, so `?t=0.86` addresses an
 * exact image and any reviewer can reproduce a claim about what the site showed.
 */

export type Register = "artistic" | "schematic" | "measured";

export type SceneKey =
  | "universe"
  | "observer"
  | "dissection"
  | "solexs"
  | "crossing"
  | "collapse"
  | "number"
  | "curve";

export interface Scene {
  readonly key: SceneKey;
  readonly label: string;
  readonly from: number;
  readonly to: number;
}

/** Scene boundaries — Experience Script §9.2–9.9. */
export const SCENES: readonly Scene[] = [
  { key: "universe", label: "THE UNIVERSE", from: 0.0, to: 0.12 },
  { key: "observer", label: "THE OBSERVER", from: 0.12, to: 0.24 },
  { key: "dissection", label: "DISSECTION", from: 0.24, to: 0.48 },
  { key: "solexs", label: "SoLEXS", from: 0.48, to: 0.6 },
  { key: "crossing", label: "THE CROSSING", from: 0.6, to: 0.72 },
  { key: "collapse", label: "COLLAPSE", from: 0.72, to: 0.82 },
  { key: "number", label: "MEASURED", from: 0.82, to: 0.9 },
  { key: "curve", label: "LIGHT CURVE", from: 0.9, to: 1.0 },
] as const;

/**
 * Watermark text. Register A carries the P8 Exception 01 wording verbatim: the real SDO
 * footage must never appear without it (docs/web/P8-EXCEPTION-01-real-solar-imagery.md).
 * Removing or weakening these strings is a scientific-integrity regression, not a style
 * change, and must fail review.
 */
export const WATERMARKS: Readonly<Record<Register, string>> = {
  artistic: "ILLUSTRATIVE · SDO / NASA · NOT ADITYA-L1 DATA",
  schematic: "SCHEMATIC · NOT TO SCALE · SDO / NASA",
  measured: "MEASURED · T1 solexs_lc_1min · 43fd0e22",
} as const;

export interface Derived {
  // --- position in the arc ---
  readonly t: number;
  readonly scene: SceneKey;
  readonly sceneLabel: string;

  // --- epistemic state (the spine of the whole site) ---
  readonly register: Register;
  /** 0 = warm (artistic), 1 = cool (schematic), 2 = neutral (measured). Never decreases. */
  readonly lutMix: number;
  readonly watermark: string;
  readonly watermarkFade: number;

  // --- scene actors ---
  readonly sunOpacity: number;
  readonly craftIn: number;
  readonly dissect: number;
  readonly payloadReveal: number;
  readonly isolate: number;
  readonly craftFade: number;
  readonly photon: number;
  readonly photonVisible: boolean;
  readonly collapse: number;
  readonly flash: number;

  // --- evidence (DOM, Register B) ---
  readonly number: number;
  readonly curve: number;

  // --- post-processing (Experience Script §9.11) ---
  readonly bloom: number;
  readonly grid: number;
  readonly outline: number;
  readonly dofFocus: number;
  readonly vignette: number;
  readonly toneMapped: boolean;

  // --- render control ---
  readonly canvasOpacity: number;
  readonly canvasMounted: boolean;
  /** Count of *expressive* effects active. Script caps this at 3; must be 0 in Register B. */
  readonly effectCount: number;
}

const clamp01 = (x: number): number => (x < 0 ? 0 : x > 1 ? 1 : x);

/** Linear ramp from `a`→`b`, clamped. `a === b` yields a hard step rather than dividing by zero. */
const ramp = (t: number, a: number, b: number): number =>
  a === b ? (t >= b ? 1 : 0) : clamp01((t - a) / (b - a));

/** Smoothstep. Used for every visible transition so nothing starts or stops abruptly. */
const smooth = (x: number): number => {
  const c = clamp01(x);
  return c * c * (3 - 2 * c);
};

const ease = (t: number, a: number, b: number): number => smooth(ramp(t, a, b));

/** Register thresholds — Script §9.2 (A), §9.4 (S), §9.8 (B). */
const SCHEMATIC_AT = 0.24;
const MEASURED_AT = 0.82;

export function derive(tRaw: number): Derived {
  // Guard the contract at the boundary. A NaN `t` from a scroll driver must not be able to
  // poison every downstream uniform; it collapses to the start of the arc instead.
  const t = Number.isFinite(tRaw) ? clamp01(tRaw) : 0;

  const scene = SCENES.find((s) => t >= s.from && t < s.to) ?? SCENES[SCENES.length - 1];
  // `SCENES` is a non-empty literal, but `noUncheckedIndexedAccess` cannot know that.
  const activeScene: Scene = scene ?? { key: "curve", label: "LIGHT CURVE", from: 0.9, to: 1.0 };

  // ------------------------------------------------------------------
  // Epistemic state. Certainty only ever increases (Bible, Article V).
  // ------------------------------------------------------------------
  const register: Register =
    t >= MEASURED_AT ? "measured" : t >= SCHEMATIC_AT ? "schematic" : "artistic";

  // Two independent, non-decreasing ramps summed to 0→2. The first begins inside Scene 2,
  // deliberately before the visitor consciously notices (Script §9.3) so the register
  // change feels discovered rather than announced. The second completes at the collapse.
  const lutMix = ease(t, 0.12, 0.3) + ease(t, 0.6, MEASURED_AT);

  // Opacity holds at full once the arc has begun; only the *string* changes at a register
  // boundary. An earlier version cross-faded the measured watermark in from zero, which
  // left the provenance line invisible at exactly t=0.82 — the frame where the number
  // resolves. Script §9.8 requires provenance to arrive *with* the value, not after it, so
  // the swap is instantaneous and the opacity never dips. Caught by the gate below.
  const watermarkFade = register === "artistic" ? ease(t, 0.02, 0.1) : 1;

  // ------------------------------------------------------------------
  // Scene actors.
  // ------------------------------------------------------------------

  // The Sun recedes from subject to setting, then leaves entirely at the collapse. Framing
  // is the camera's job (Doc 4); this is presence only, so the two never fight.
  const sunOpacity = (1 - ease(t, 0.1, 0.3) * 0.7) * (1 - ease(t, 0.72, MEASURED_AT));

  const craftIn = ease(t, 0.12, 0.24);
  const dissect = ease(t, 0.26, 0.46);
  const payloadReveal = ease(t, 0.3, 0.46);
  const isolate = ease(t, 0.48, 0.58);
  const craftFade = ease(t, 0.58, 0.68);

  const photon = ease(t, 0.6, 0.72);
  const photonVisible = t >= 0.58 && t < 0.76;
  const collapse = ease(t, 0.72, MEASURED_AT);

  // A single eased ramp up and down — never a strobe. WCAG: nothing above 3 Hz, and the
  // Script (§9.7) requires this to be one gesture, not a flicker.
  const flash = ease(t, 0.78, 0.82) * (1 - ease(t, 0.82, 0.87));

  const numberProgress = ease(t, 0.84, 0.9);
  const curve = ease(t, 0.9, 1.0);

  // ------------------------------------------------------------------
  // Post-processing — Script §9.11 (post-audit stacks).
  // Deleted by the audit and therefore absent by construction: chromatic aberration,
  // star field, cursor yaw, magnetic controls.
  // ------------------------------------------------------------------

  // Bloom belongs to Register A only. Its decay is information: we are leaving the
  // artistic register (Script §9.3). It must reach exactly 0 before the schematic begins.
  const bloom = 1 - ease(t, 0.12, SCHEMATIC_AT);

  // The grid announces "you are reading a diagram" and leaves as measurement arrives.
  const grid = ease(t, SCHEMATIC_AT, 0.3) * (1 - ease(t, 0.72, MEASURED_AT));

  // Selection. Rises with the isolation, released once the crossing owns the frame.
  const outline = ease(t, 0.48, 0.56) * (1 - ease(t, 0.66, 0.72));

  // The rack focus (Script §9.3) — the one flourish. 0 = focus on Sun, 1 = focus on craft.
  const dofFocus = ease(t, 0.2, 0.24);

  /**
   * CRITICAL CORRECTION to Script §9.11.
   *
   * The Script's per-scene stacks list vignette in scenes 1, 3 and 5 but not 2 and 4,
   * because the ≤3 cap forced it out to make room for DoF and Outline. Implemented
   * literally that produces a visible on/off/on/off flicker of the frame edge across the
   * arc — a defect, not a design.
   *
   * Resolution: vignette is reclassified as *ambient framing*, alongside SMAA and dither,
   * and is therefore excluded from the expressive effect count. It is held constant
   * through Registers A and S and released with the canvas. The ≤3 expressive cap is
   * still honoured everywhere (see `effectCount`), and no scene gains an effect the
   * Script did not grant it.
   */
  const vignette = 1 - ease(t, 0.76, MEASURED_AT);

  // The image stops being photographed and starts being plotted (Script §9.7).
  const toneMapped = t < 0.8;

  // ------------------------------------------------------------------
  // Render control. Register B is DOM-only: post-processing a measurement is a visual lie
  // about its provenance (Script §9.8), so the canvas leaves rather than fading behind.
  // ------------------------------------------------------------------
  const canvasOpacity = 1 - ease(t, 0.8, 0.86);
  const canvasMounted = t < 0.87;

  const effectCount =
    (bloom > 0.001 ? 1 : 0) +
    (grid > 0.001 ? 1 : 0) +
    (outline > 0.001 ? 1 : 0) +
    // The rack focus counts only while it is actually transitioning.
    (t >= 0.2 && t < 0.26 ? 1 : 0) +
    // The LUT is always present through A and S; it is the register system itself.
    (register === "measured" ? 0 : 1);

  return {
    t,
    scene: activeScene.key,
    sceneLabel: activeScene.label,

    register,
    lutMix,
    watermark: WATERMARKS[register],
    watermarkFade,

    sunOpacity,
    craftIn,
    dissect,
    payloadReveal,
    isolate,
    craftFade,
    photon,
    photonVisible,
    collapse,
    flash,

    number: numberProgress,
    curve,

    bloom,
    grid,
    outline,
    dofFocus,
    vignette,
    toneMapped,

    canvasOpacity,
    canvasMounted,
    effectCount,
  };
}
