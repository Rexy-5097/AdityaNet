import { describe, expect, it } from "vitest";
import { derive, SCENES, WATERMARKS, type Register } from "./timeline";

/**
 * Gates for the `derive(t)` contract (docs/web/v2/07_FRONTEND_ARCHITECTURE.md §7.7).
 *
 * These are not incidental unit tests. Three of them — purity, monotonic certainty and
 * watermark sequence — encode scientific-integrity claims the site makes about itself. If
 * certainty can regress, the Artistic→Schematic→Measured thesis is false at runtime.
 */

/** Dense sweep. 2001 samples is well beyond any transition width used in the timeline. */
const SAMPLES = 2001;
const sweep = (): number[] => Array.from({ length: SAMPLES }, (_, i) => i / (SAMPLES - 1));

const RANK: Readonly<Record<Register, number>> = { artistic: 0, schematic: 1, measured: 2 };

describe("purity", () => {
  it("returns identical output for identical input", () => {
    for (const t of [0, 0.137, 0.42, 0.618, 0.86, 1]) {
      expect(derive(t)).toEqual(derive(t));
    }
  });

  it("does not depend on call order or history", () => {
    const forward = sweep().map((t) => derive(t).lutMix);
    const backward = sweep().reverse().map((t) => derive(t).lutMix).reverse();
    expect(forward).toEqual(backward);
  });
});

describe("input hardening", () => {
  it("clamps out-of-range t", () => {
    expect(derive(-5)).toEqual(derive(0));
    expect(derive(99)).toEqual(derive(1));
  });

  it("collapses non-finite t to the start of the arc rather than propagating NaN", () => {
    for (const bad of [Number.NaN, Number.POSITIVE_INFINITY, Number.NEGATIVE_INFINITY]) {
      const d = derive(bad);
      expect(Number.isFinite(d.lutMix)).toBe(true);
      expect(d.register).toBe("artistic");
    }
  });

  it("produces only finite numbers across the whole sweep", () => {
    for (const t of sweep()) {
      for (const [key, value] of Object.entries(derive(t))) {
        if (typeof value === "number") {
          expect(Number.isFinite(value), `${key} at t=${t}`).toBe(true);
        }
      }
    }
  });
});

describe("certainty is monotonic (Bible, Article V)", () => {
  it("register never regresses", () => {
    let seen = 0;
    for (const t of sweep()) {
      const rank = RANK[derive(t).register];
      expect(rank, `register regressed at t=${t}`).toBeGreaterThanOrEqual(seen);
      seen = rank;
    }
  });

  it("visits all three registers in order, skipping none", () => {
    const order: Register[] = [];
    for (const t of sweep()) {
      const r = derive(t).register;
      if (order[order.length - 1] !== r) order.push(r);
    }
    expect(order).toEqual(["artistic", "schematic", "measured"]);
  });

  it("lutMix is non-decreasing and spans 0 → 2", () => {
    let prev = -Infinity;
    for (const t of sweep()) {
      const { lutMix } = derive(t);
      expect(lutMix, `lutMix regressed at t=${t}`).toBeGreaterThanOrEqual(prev - 1e-9);
      prev = lutMix;
    }
    expect(derive(0).lutMix).toBeCloseTo(0, 6);
    expect(derive(1).lutMix).toBeCloseTo(2, 6);
  });

  it("watermark always matches the active register", () => {
    for (const t of sweep()) {
      const d = derive(t);
      expect(d.watermark).toBe(WATERMARKS[d.register]);
    }
  });

  it("never leaves the watermark fully invisible", () => {
    // A watermark that can reach zero opacity is an integrity failure, not a style choice.
    for (const t of sweep()) {
      expect(derive(t).watermarkFade).toBeGreaterThanOrEqual(0);
    }
    // It is only allowed to be low during the opening fade-in, before any imagery reads.
    for (const t of sweep().filter((x) => x > 0.12)) {
      expect(derive(t).watermarkFade, `watermark faded at t=${t}`).toBeGreaterThan(0.35);
    }
  });
});

describe("the artistic watermark carries the P8 exception wording", () => {
  it("states the imagery is not Aditya-L1 data", () => {
    expect(WATERMARKS.artistic).toContain("NOT ADITYA-L1 DATA");
    expect(WATERMARKS.artistic).toContain("SDO / NASA");
  });

  it("is present from the very first frame that shows footage", () => {
    expect(derive(0).watermark).toBe(WATERMARKS.artistic);
  });
});

describe("effect discipline (Experience Script §9.11)", () => {
  it("never exceeds three expressive effects", () => {
    for (const t of sweep()) {
      const { effectCount } = derive(t);
      expect(effectCount, `stack of ${effectCount} at t=${t}`).toBeLessThanOrEqual(3);
    }
  });

  it("runs zero effects in the measured register", () => {
    for (const t of sweep().filter((x) => x >= 0.82)) {
      const d = derive(t);
      expect(d.effectCount, `effects present at t=${t}`).toBe(0);
      expect(d.bloom).toBeLessThanOrEqual(0.001);
      expect(d.grid).toBeLessThanOrEqual(0.001);
      expect(d.outline).toBeLessThanOrEqual(0.001);
    }
  });

  it("keeps bloom exclusive to the artistic register", () => {
    // Bloom on a diagram or a measurement implies emission the data does not claim.
    for (const t of sweep().filter((x) => x >= 0.24)) {
      expect(derive(t).bloom, `bloom at t=${t}`).toBeLessThanOrEqual(0.001);
    }
    expect(derive(0).bloom).toBeCloseTo(1, 6);
  });

  it("keeps the grid out of the artistic register", () => {
    for (const t of sweep().filter((x) => x < 0.24)) {
      expect(derive(t).grid, `grid at t=${t}`).toBeLessThanOrEqual(0.001);
    }
  });
});

describe("accessibility", () => {
  it("flash is a single ramp, not a strobe", () => {
    // One rise and one fall — never a second peak, which would read as a flicker.
    const values = sweep().map((t) => derive(t).flash);
    let direction = 0;
    let changes = 0;
    for (let i = 1; i < values.length; i += 1) {
      const a = values[i - 1] ?? 0;
      const b = values[i] ?? 0;
      const d = Math.sign(Number((b - a).toFixed(9)));
      if (d !== 0 && d !== direction) {
        changes += 1;
        direction = d;
      }
    }
    expect(changes, "flash changed direction more than once").toBeLessThanOrEqual(2);
    expect(Math.max(...values)).toBeLessThanOrEqual(1);
  });

  it("keeps every normalised output within [0,1]", () => {
    const unit = [
      "sunOpacity", "craftIn", "dissect", "payloadReveal", "isolate", "craftFade",
      "photon", "collapse", "flash", "number", "curve",
      "bloom", "grid", "outline", "dofFocus", "vignette",
      "canvasOpacity", "watermarkFade",
    ] as const;
    for (const t of sweep()) {
      const d = derive(t) as unknown as Record<string, number>;
      for (const key of unit) {
        const v = d[key] ?? 0;
        expect(v, `${key}=${v} at t=${t}`).toBeGreaterThanOrEqual(0);
        expect(v, `${key}=${v} at t=${t}`).toBeLessThanOrEqual(1);
      }
    }
  });
});

describe("scene table", () => {
  it("is contiguous and covers [0,1] with no gap or overlap", () => {
    expect(SCENES[0]?.from).toBe(0);
    expect(SCENES[SCENES.length - 1]?.to).toBe(1);
    for (let i = 1; i < SCENES.length; i += 1) {
      expect(SCENES[i]?.from).toBe(SCENES[i - 1]?.to);
    }
  });

  it("resolves a scene for every t including the endpoint", () => {
    for (const t of sweep()) {
      expect(derive(t).scene, `no scene at t=${t}`).toBeTruthy();
    }
    expect(derive(1).scene).toBe("curve");
  });
});

describe("narrative ordering", () => {
  it("the canvas is gone before the light curve draws", () => {
    // Register B is DOM-only; a canvas behind the evidence would undercut its provenance.
    expect(derive(0.9).canvasMounted).toBe(false);
    expect(derive(0.95).curve).toBeGreaterThan(0);
  });

  it("the photon crosses before the collapse begins", () => {
    expect(derive(0.71).photon).toBeGreaterThan(0.9);
    expect(derive(0.71).collapse).toBeCloseTo(0, 6);
  });

  it("payloads are revealed before SoLEXS is isolated", () => {
    expect(derive(0.46).payloadReveal).toBeCloseTo(1, 4);
    expect(derive(0.46).isolate).toBeCloseTo(0, 6);
  });

  it("the number resolves before the curve draws", () => {
    expect(derive(0.9).number).toBeCloseTo(1, 4);
    expect(derive(0.9).curve).toBeCloseTo(0, 6);
  });
});
