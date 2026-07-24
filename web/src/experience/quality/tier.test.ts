import { describe, expect, it } from "vitest";
import { selectTier, downgrade, TIER_SETTINGS, type DeviceCapabilities } from "./tier";

const CAPABLE: DeviceCapabilities = {
  hasWebgl2: true,
  prefersReducedMotion: false,
  reduceEffects: false,
  deviceMemory: 16,
  hardwareConcurrency: 10,
  coarsePointer: false,
};

const capabilities = (overrides: Partial<DeviceCapabilities>): DeviceCapabilities => ({
  ...CAPABLE,
  ...overrides,
});

describe("selectTier — absolute gates", () => {
  it("returns tier 0 without WebGL2, however capable the device otherwise is", () => {
    expect(selectTier(capabilities({ hasWebgl2: false }))).toBe(0);
  });

  it("returns tier 0 under prefers-reduced-motion", () => {
    // Reduced motion is a hard gate, not a degradation: the result must be a composed
    // still, which is what tier 0 is. A paused scene would not satisfy the preference.
    expect(selectTier(capabilities({ prefersReducedMotion: true }))).toBe(0);
  });

  it("returns tier 0 when the user has opted out of effects", () => {
    expect(selectTier(capabilities({ reduceEffects: true }))).toBe(0);
  });

  it("honours the gates even on the most capable hardware", () => {
    const powerful = capabilities({ deviceMemory: 64, hardwareConcurrency: 32 });
    expect(selectTier({ ...powerful, prefersReducedMotion: true })).toBe(0);
    expect(selectTier({ ...powerful, reduceEffects: true })).toBe(0);
  });
});

describe("selectTier — performance heuristics", () => {
  it("puts touch devices on the mobile tier", () => {
    expect(selectTier(capabilities({ coarsePointer: true }))).toBe(1);
  });

  it("puts memory-constrained devices on the mobile tier", () => {
    expect(selectTier(capabilities({ deviceMemory: 4 }))).toBe(1);
    expect(selectTier(capabilities({ deviceMemory: 2 }))).toBe(1);
  });

  it("does not penalise browsers that withhold deviceMemory", () => {
    // Safari does not expose deviceMemory. Treating undefined as constrained would
    // drop a large share of desktop users to the mobile tier for no reason.
    expect(selectTier(capabilities({ deviceMemory: undefined }))).toBe(3);
  });

  it("separates mid and high tiers on core count", () => {
    expect(selectTier(capabilities({ hardwareConcurrency: 6 }))).toBe(2);
    expect(selectTier(capabilities({ hardwareConcurrency: 8 }))).toBe(3);
  });

  it("puts low core counts on the mobile tier", () => {
    expect(selectTier(capabilities({ hardwareConcurrency: 4 }))).toBe(1);
  });
});

describe("downgrade", () => {
  it("steps down one tier at a time", () => {
    expect(downgrade(3)).toBe(2);
    expect(downgrade(2)).toBe(1);
  });

  it("never drops an animated tier to the static poster", () => {
    // Tier 0 is a deliberate choice, not a performance outcome. Falling into it from
    // a frame-time dip would silently discard the scene a capable device can render.
    expect(downgrade(1)).toBe(1);
    expect(downgrade(0)).toBe(0);
  });
});

describe("TIER_SETTINGS", () => {
  it("never animates tier 0", () => {
    expect(TIER_SETTINGS[0].animate).toBe(false);
  });

  it("increases fidelity monotonically with tier", () => {
    const tiers = [0, 1, 2, 3] as const;
    for (let i = 1; i < tiers.length; i += 1) {
      const previous = TIER_SETTINGS[tiers[i - 1]!];
      const current = TIER_SETTINGS[tiers[i]!];
      expect(current.maxPixelRatio).toBeGreaterThanOrEqual(previous.maxPixelRatio);
      expect(current.coronaShells).toBeGreaterThanOrEqual(previous.coronaShells);
    }
  });
});
