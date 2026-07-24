/**
 * Damped-spring integration for camera and interaction motion.
 *
 * Springs rather than eased keyframes, because a spring is interruptible: a user who
 * grabs the star mid-transition gets a continuous response instead of a fight with a
 * timeline. That interruptibility is most of what separates motion that feels
 * responsive from motion that feels scripted.
 *
 * Pure and frame-rate independent, so tier 1 at 30 fps and tier 3 at 60 fps settle
 * over the same wall-clock duration rather than the same number of frames.
 */

export interface Spring {
  value: number;
  velocity: number;
}

export interface SpringConfig {
  /** Higher converges faster. */
  readonly stiffness: number;
  /**
   * 1.0 is critical damping — fastest approach with no overshoot.
   *
   * Cameras are always critically damped. Overshooting a camera reads as nausea, not
   * as liveliness, because the whole world moves past the target and back.
   */
  readonly damping: number;
}

export const CAMERA_SPRING: SpringConfig = { stiffness: 120, damping: 1.0 };

/**
 * Advance a spring toward `target` by `dt` seconds.
 *
 * `dt` is clamped to 50 ms. Without the clamp, a backgrounded tab resuming after
 * seconds would integrate one enormous step and fling the value past its target — a
 * classic and very visible bug when someone switches back to the page.
 */
export function stepSpring(
  spring: Spring,
  target: number,
  dt: number,
  config: SpringConfig = CAMERA_SPRING,
): void {
  const step = Math.min(dt, 0.05);
  const { stiffness, damping } = config;

  // c = 2ζ√k gives the requested damping ratio for a unit mass.
  const c = 2 * damping * Math.sqrt(stiffness);

  const displacement = spring.value - target;
  const acceleration = -stiffness * displacement - c * spring.velocity;

  spring.velocity += acceleration * step;
  spring.value += spring.velocity * step;
}

/**
 * Apply release inertia with frame-rate-independent friction.
 *
 * Expressed as a per-second retention rate rather than a per-frame multiplier, so a
 * flick decays over the same wall-clock time at any refresh rate. A per-frame constant
 * would make 120 Hz displays feel sluggish and 30 Hz displays feel slippery.
 */
export function applyFriction(velocity: number, dt: number, retentionPerSecond = 0.06): number {
  const decayed = velocity * Math.pow(retentionPerSecond, Math.min(dt, 0.05));
  return Math.abs(decayed) < 0.001 ? 0 : decayed;
}
