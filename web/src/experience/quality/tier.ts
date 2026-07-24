/**
 * Quality tier selection for the experience layer.
 *
 * Pure functions, no browser globals captured at module scope, so the whole policy is
 * unit-testable without a DOM. That matters more than it sounds: tier selection decides
 * whether a visitor sees a GPU scene or a static poster, and getting it wrong on a
 * class of device is invisible during development on a workstation.
 */

/** Capabilities sampled from the environment, passed in rather than read directly. */
export interface DeviceCapabilities {
  readonly hasWebgl2: boolean;
  readonly prefersReducedMotion: boolean;
  /** User's explicit opt-out, persisted. Overrides everything except capability. */
  readonly reduceEffects: boolean;
  /** navigator.deviceMemory, in GiB. Undefined on browsers that do not expose it. */
  readonly deviceMemory: number | undefined;
  readonly hardwareConcurrency: number;
  /** Coarse pointer implies touch, which correlates with mobile GPU budgets. */
  readonly coarsePointer: boolean;
}

/**
 * Tier 0 is not a failure state — it is a complete, honest rendering of the same
 * information as a static composition. Tiers 1-3 differ only in atmosphere.
 */
export type QualityTier = 0 | 1 | 2 | 3;

export const TIER_SETTINGS: Readonly<Record<QualityTier, TierSettings>> = {
  0: { maxPixelRatio: 1, coronaShells: 0, animate: false },
  1: { maxPixelRatio: 1, coronaShells: 2, animate: true },
  2: { maxPixelRatio: 1.5, coronaShells: 3, animate: true },
  3: { maxPixelRatio: 2, coronaShells: 4, animate: true },
};

export interface TierSettings {
  readonly maxPixelRatio: number;
  readonly coronaShells: number;
  readonly animate: boolean;
}

/**
 * Choose a tier from capabilities.
 *
 * Order matters. Capability and consent are absolute gates; performance heuristics
 * only choose *how much* atmosphere among the tiers that remain.
 */
export function selectTier(capabilities: DeviceCapabilities): QualityTier {
  const { hasWebgl2, prefersReducedMotion, reduceEffects } = capabilities;

  // No renderer, or the user asked not to be animated. Reduced motion resolves to a
  // composed still rather than a paused scene: a frozen frame of an animation is not
  // the same as a picture designed to be looked at.
  if (!hasWebgl2 || prefersReducedMotion || reduceEffects) return 0;

  const { deviceMemory, hardwareConcurrency, coarsePointer } = capabilities;

  // Treat unknown memory as unconstrained: penalising Safari, which does not expose
  // deviceMemory, would drop a large share of desktop users to the mobile tier.
  const constrainedMemory = deviceMemory !== undefined && deviceMemory <= 4;
  if (coarsePointer || constrainedMemory || hardwareConcurrency <= 4) return 1;

  return hardwareConcurrency >= 8 ? 3 : 2;
}

/** Sample the live environment. The only function here that touches browser globals. */
export function readCapabilities(reduceEffects: boolean): DeviceCapabilities {
  const canvas = document.createElement("canvas");
  const hasWebgl2 = canvas.getContext("webgl2") !== null;

  const memory = (navigator as Navigator & { deviceMemory?: number }).deviceMemory;

  return {
    hasWebgl2,
    prefersReducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
    reduceEffects,
    deviceMemory: memory,
    hardwareConcurrency: navigator.hardwareConcurrency ?? 4,
    coarsePointer: window.matchMedia("(pointer: coarse)").matches,
  };
}

/**
 * Downgrade policy for sustained poor frame times.
 *
 * Never upgrades. An oscillating tier is more distracting than a consistently lower
 * one, and a device that struggled once will struggle again.
 */
export function downgrade(tier: QualityTier): QualityTier {
  return tier <= 1 ? tier : ((tier - 1) as QualityTier);
}
