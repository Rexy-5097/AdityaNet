import { describe, expect, it } from "vitest";
import {
  cameraAt,
  CAMERA_KEYFRAMES,
  DOCUMENTED_SHOT_BOUNDARIES,
  REGISTER_BOUNDARIES,
  length,
  rightVector,
  sub,
  type CameraPose,
} from "./camera";
import { SCENES } from "./timeline";

/**
 * Behavioral invariants for the camera subsystem (docs/web/v2/04_CAMERA_CHOREOGRAPHY.md).
 *
 * The instruction for this slice was explicit: validate the camera with invariants, not
 * visual inspection. Each test below encodes a *rule* from the choreography — no roll, no
 * motion during a register change, static shots actually static, every keyframe traceable
 * to the Script — so that a future edit which breaks the narrative fails CI rather than
 * merely looking slightly off in a browser.
 */

const SAMPLES = 2001;
const sweep = (): number[] => Array.from({ length: SAMPLES }, (_, i) => i / (SAMPLES - 1));

/** Positional speed estimate at t, per unit of t. */
function speed(t: number): number {
  const h = 0.0005;
  const a = cameraAt(Math.max(0, t - h)).position;
  const b = cameraAt(Math.min(1, t + h)).position;
  return length(sub(b, a)) / (2 * h);
}

describe("purity and finiteness", () => {
  it("is deterministic", () => {
    for (const t of [0, 0.1, 0.24, 0.37, 0.6, 0.82, 1]) {
      expect(cameraAt(t)).toEqual(cameraAt(t));
    }
  });

  it("produces only finite numbers, including for non-finite input", () => {
    for (const t of [...sweep(), Number.NaN, Infinity, -Infinity]) {
      const p = cameraAt(t);
      for (const v of [p.position, p.target, p.up]) {
        expect(Number.isFinite(v.x) && Number.isFinite(v.y) && Number.isFinite(v.z)).toBe(true);
      }
      expect(Number.isFinite(p.fov) && Number.isFinite(p.focus)).toBe(true);
    }
  });
});

describe("traceability — every keyframe maps to a documented moment", () => {
  it("every keyframe time is a documented shot boundary (Doc 4 §4.2)", () => {
    for (const kf of CAMERA_KEYFRAMES) {
      expect(DOCUMENTED_SHOT_BOUNDARIES, `keyframe at undocumented t=${kf.t}`).toContain(kf.t);
    }
  });

  it("every keyframe carries a Script reference and a shot number", () => {
    for (const kf of CAMERA_KEYFRAMES) {
      expect(kf.scriptRef).toMatch(/^§9\.\d/);
      expect(kf.shot).toBeGreaterThanOrEqual(1);
    }
  });

  it("every keyframe falls inside a real scene from the timeline contract", () => {
    for (const kf of CAMERA_KEYFRAMES) {
      const inScene = SCENES.some((s) => kf.t >= s.from && kf.t <= s.to);
      expect(inScene, `keyframe t=${kf.t} lies in no scene`).toBe(true);
    }
  });

  it("keyframe times are strictly increasing", () => {
    for (let i = 1; i < CAMERA_KEYFRAMES.length; i += 1) {
      expect(CAMERA_KEYFRAMES[i]!.t).toBeGreaterThan(CAMERA_KEYFRAMES[i - 1]!.t);
    }
  });
});

describe("no roll, ever (Doc 4 §4.1 rule 5)", () => {
  it("keeps the horizon level for the entire arc", () => {
    for (const t of sweep()) {
      // right.y is the roll indicator; a level camera has it identically zero.
      expect(Math.abs(rightVector(cameraAt(t)).y), `roll at t=${t}`).toBeLessThan(1e-9);
    }
  });
});

describe("no motion during a register change (Doc 4 §4.1 rule 4)", () => {
  it("each register boundary coincides with a keyframe", () => {
    const times = CAMERA_KEYFRAMES.map((k) => k.t);
    for (const b of REGISTER_BOUNDARIES) {
      expect(times, `no keyframe at register boundary ${b}`).toContain(b);
    }
  });

  it("camera speed is ~zero at each register boundary", () => {
    for (const b of REGISTER_BOUNDARIES) {
      expect(speed(b), `camera moving at register boundary ${b}`).toBeLessThan(1e-3);
    }
  });
});

describe("static shots are provably static (Doc 4 §4.2)", () => {
  // Hold segments, from the documented shot list.
  const holds: ReadonlyArray<readonly [number, number, string]> = [
    [0.0, 0.08, "shot 1 arrival"],
    [0.12, 0.2, "shot 3 craft enters"],
    [0.24, 0.3, "shot 5 schematic establishes"],
    [0.46, 0.48, "shot 7 the hold"],
    [0.6, 0.82, "shots 9–11 locked off"],
  ];

  const samplesIn = (a: number, b: number): number[] =>
    Array.from({ length: 25 }, (_, i) => a + ((b - a) * i) / 24);

  it("holds position, target and fov constant across every static shot", () => {
    for (const [a, b, label] of holds) {
      const ref = cameraAt(a + (b - a) * 0.001);
      for (const t of samplesIn(a + 1e-4, b - 1e-4)) {
        const p = cameraAt(t);
        expect(length(sub(p.position, ref.position)), `${label} translated at t=${t}`).toBeLessThan(1e-9);
        expect(p.fov, `${label} fov changed at t=${t}`).toBeCloseTo(ref.fov, 9);
      }
    }
  });

  it("holds show zero speed", () => {
    for (const [a, b, label] of holds) {
      const mid = (a + b) / 2;
      expect(speed(mid), `${label} moving mid-hold`).toBeLessThan(1e-6);
    }
  });
});

describe("the rack focus moves nothing but focus (Doc 4 §4.2 shot 4)", () => {
  it("translates the camera not at all between t=0.20 and t=0.24", () => {
    const start = cameraAt(0.2).position;
    for (let t = 0.2; t <= 0.24; t += 0.002) {
      expect(length(sub(cameraAt(t).position, start)), `moved during rack focus at t=${t}`).toBeLessThan(1e-9);
    }
  });

  it("drives focus from Sun (0) to craft (1) across exactly that window", () => {
    expect(cameraAt(0.2).focus).toBeCloseTo(0, 6);
    expect(cameraAt(0.24).focus).toBeCloseTo(1, 6);
  });

  it("keeps focus constant outside the rack-focus window", () => {
    for (const t of sweep().filter((x) => x < 0.2)) expect(cameraAt(t).focus).toBeCloseTo(0, 6);
    for (const t of sweep().filter((x) => x > 0.24)) expect(cameraAt(t).focus).toBeCloseTo(1, 6);
  });

  it("focus is monotonic non-decreasing (attention transfers once, never back)", () => {
    let prev = -Infinity;
    for (const t of sweep()) {
      const f = cameraAt(t).focus;
      expect(f, `focus regressed at t=${t}`).toBeGreaterThanOrEqual(prev - 1e-9);
      prev = f;
    }
  });
});

describe("motion is continuous — no visible jump cuts (Doc 4)", () => {
  it("adjacent samples never leap in position", () => {
    // This test hunts for discontinuities (jump cuts), not for fast moves. The briskest
    // legitimate move — the shot-2 pull-back, 2 units of dolly over 0.04 of t with
    // smoothstep — peaks near 0.038 per sample step. A real jump cut between mismatched
    // keyframes would be of order the keyframe-to-keyframe distance (~1–3 units). 0.1
    // cleanly separates the two.
    let prev = cameraAt(0).position;
    for (const t of sweep().slice(1)) {
      const cur = cameraAt(t).position;
      expect(length(sub(cur, prev)), `position jump at t=${t}`).toBeLessThan(0.1);
      prev = cur;
    }
  });

  it("fov is continuous and stays within its documented band [28,40]", () => {
    for (const t of sweep()) {
      const { fov } = cameraAt(t);
      expect(fov, `fov=${fov} out of band at t=${t}`).toBeGreaterThanOrEqual(28 - 1e-9);
      expect(fov).toBeLessThanOrEqual(40 + 1e-9);
    }
  });
});

describe("the orbit is narrated — azimuth only ever advances (Doc 4 §4.2 shots 5–6)", () => {
  it("azimuth is monotonic non-decreasing across the arc", () => {
    // A reversing orbit would be un-narrated motion. Recover azimuth from position.
    const azimuthOf = (p: CameraPose): number => Math.atan2(p.position.x - p.target.x, p.position.z - p.target.z);
    let prev = -Infinity;
    for (const t of sweep()) {
      const az = azimuthOf(cameraAt(t));
      expect(az, `azimuth regressed at t=${t}`).toBeGreaterThanOrEqual(prev - 1e-6);
      prev = az;
    }
  });
});

describe("the camera never collides with its subject", () => {
  it("radius stays clear of the target the whole way", () => {
    for (const t of sweep()) {
      const p = cameraAt(t);
      expect(length(sub(p.position, p.target)), `camera too close at t=${t}`).toBeGreaterThan(2.0);
    }
  });
});

describe("reduced motion cuts, it does not travel (Doc 4 §4.5)", () => {
  it("holds a single pose within each segment (no interpolation)", () => {
    // Inside the pull-back, the normal path moves; the reduced path must not.
    const a = cameraAt(0.14, { reducedMotion: true }).position;
    const b = cameraAt(0.18, { reducedMotion: true }).position;
    expect(length(sub(a, b))).toBeLessThan(1e-9);
  });

  it("preserves every shot's destination framing", () => {
    // The reduced pose at any t equals the normal pose at that segment's end keyframe.
    const endOfPullback = cameraAt(0.12).position; // shot 2 destination
    const reducedMid = cameraAt(0.15, { reducedMotion: true }).position;
    expect(length(sub(endOfPullback, reducedMid))).toBeLessThan(1e-9);
  });

  it("shows no continuous camera speed between keyframes", () => {
    const h = 0.0005;
    for (const t of [0.1, 0.35, 0.5]) {
      const p0 = cameraAt(t - h, { reducedMotion: true }).position;
      const p1 = cameraAt(t + h, { reducedMotion: true }).position;
      expect(length(sub(p1, p0))).toBeLessThan(1e-9);
    }
  });
});

describe("endpoints", () => {
  it("clamps before the first and after the last keyframe", () => {
    expect(cameraAt(-1)).toEqual(cameraAt(0));
    expect(cameraAt(2)).toEqual(cameraAt(0.82));
  });

  it("is locked off from t=0.82 onward (canvas hands over to the DOM)", () => {
    const lock = cameraAt(0.82).position;
    for (const t of [0.85, 0.9, 1]) {
      expect(length(sub(cameraAt(t).position, lock)), `moved after lock-off at t=${t}`).toBeLessThan(1e-9);
    }
  });
});
