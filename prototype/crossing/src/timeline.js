/**
 * The Cinematic Cut — five scenes, one scalar t ∈ [0,1].
 *
 * Scene 1 Universe   — the Sun fills the frame (real SDO, attributed). Setting.
 * Scene 2 Observer   — Aditya-L1 enters, tiny against the Sun. Scale.
 * Scene 3 Dissection — the spacecraft dissects; seven payloads light; all fade but SoLEXS.
 * Scene 4 SoLEXS     — aperture, detector plane, photon direction.
 * Scene 5 Crossing   — photon → detector → point → number → measured → light curve.
 *
 * Pure function of t (no clock, no randomness) so any instant is reproducible and
 * scrubbable. In production t maps to scroll offset.
 */

export const PHASES = [
  { key: "universe", label: "THE UNIVERSE", from: 0.0, to: 0.12 },
  { key: "observer", label: "THE OBSERVER", from: 0.12, to: 0.24 },
  { key: "dissect", label: "DISSECTION", from: 0.24, to: 0.48 },
  { key: "solexs", label: "SoLEXS", from: 0.48, to: 0.6 },
  { key: "photon", label: "PHOTON", from: 0.6, to: 0.72 },
  { key: "collapse", label: "COLLAPSE", from: 0.72, to: 0.82 },
  { key: "number", label: "MEASURED", from: 0.82, to: 0.9 },
  { key: "curve", label: "LIGHT CURVE", from: 0.9, to: 1.0 },
];

const clamp01 = (x) => Math.min(1, Math.max(0, x));
const ramp = (t, a, b) => clamp01((t - a) / (b - a));
const smooth = (x) => { const c = clamp01(x); return c * c * (3 - 2 * c); };

export function derive(t) {
  const phase = PHASES.find((p) => t >= p.from && t < p.to) ?? PHASES[PHASES.length - 1];

  // The Sun is the setting. Full frame at the start; recedes as the spacecraft arrives,
  // and freezes/dims when the dissection begins so the spacecraft owns the screen.
  const sunScale = 1.0 - smooth(ramp(t, 0.1, 0.26)) * 0.55;   // 1.0 → 0.45
  const sunDim = 1.0 - smooth(ramp(t, 0.22, 0.34)) * 0.72;    // recede behind the craft
  const sunDrain = smooth(ramp(t, 0.5, 0.62));                // desaturates near the crossing

  // The spacecraft enters (Scene 2), dissects (Scene 3), isolates SoLEXS (Scene 4).
  const craftIn = smooth(ramp(t, 0.12, 0.24));               // fly-in + grow
  const dissect = smooth(ramp(t, 0.26, 0.46));               // parts separate
  // Seven payloads light in sequence across the dissection.
  const payloadReveal = smooth(ramp(t, 0.30, 0.48));         // 0→1 sweeps the 7
  const isolate = smooth(ramp(t, 0.48, 0.58));               // all fade but SoLEXS
  const craftFade = smooth(ramp(t, 0.56, 0.64));             // craft → SoLEXS symbol only

  // Scene 5 — the Crossing (unchanged in spirit, shifted in t).
  const photon = smooth(ramp(t, 0.6, 0.72));
  const photonVisible = t >= 0.58 && t < 0.76;
  const collapse = smooth(ramp(t, 0.72, 0.82));
  const flashUp = smooth(ramp(t, 0.78, 0.82));
  const flashDown = smooth(ramp(t, 0.82, 0.87));
  const flash = flashUp * (1 - flashDown);
  const number = smooth(ramp(t, 0.84, 0.9));
  const curve = smooth(ramp(t, 0.9, 1.0));

  const watermark = t >= 0.8 ? "measured" : t >= 0.24 ? "schematic" : "artistic";
  const watermarkFade = t >= 0.8 ? smooth(ramp(t, 0.8, 0.86)) : t >= 0.24 ? 1 : smooth(ramp(t, 0.02, 0.1));

  return {
    phase: phase.key, phaseLabel: phase.label,
    sunScale, sunDim, sunDrain,
    craftIn, dissect, payloadReveal, isolate, craftFade,
    photon, photonVisible, collapse, flash, number, curve,
    watermark, watermarkFade,
    // legacy alias so the Crossing's Sun drain shader still reads something
    drain: sunDrain,
  };
}
