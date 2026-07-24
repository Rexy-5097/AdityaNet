import { describe, expect, it } from "vitest";
import { stepSpring, applyFriction, CAMERA_SPRING, type Spring } from "./spring";

const settle = (target: number, dt = 1 / 60, steps = 600): Spring => {
  const spring: Spring = { value: 0, velocity: 0 };
  for (let i = 0; i < steps; i += 1) stepSpring(spring, target, dt);
  return spring;
};

describe("stepSpring", () => {
  it("converges to the target and comes to rest", () => {
    const spring = settle(1);
    expect(spring.value).toBeCloseTo(1, 3);
    expect(spring.velocity).toBeCloseTo(0, 3);
  });

  it("never overshoots under critical damping", () => {
    // The camera contract: overshoot reads as nausea because the whole world travels
    // past the target and back. If this ever fails, camera motion is wrong.
    const spring: Spring = { value: 0, velocity: 0 };
    let maximum = 0;
    for (let i = 0; i < 600; i += 1) {
      stepSpring(spring, 1, 1 / 60, CAMERA_SPRING);
      maximum = Math.max(maximum, spring.value);
    }
    expect(maximum).toBeLessThanOrEqual(1.0001);
  });

  it("settles to the same place regardless of frame rate", () => {
    const at30 = settle(1, 1 / 30, 300);
    const at120 = settle(1, 1 / 120, 1200);
    expect(at30.value).toBeCloseTo(at120.value, 2);
  });

  it("clamps a long delta so a resumed tab does not fling the value", () => {
    // A backgrounded tab can resume with dt measured in seconds. Without clamping, one
    // integration step overshoots massively — a very visible bug on tab switch.
    const spring: Spring = { value: 0, velocity: 0 };
    stepSpring(spring, 1, 5.0);
    expect(Number.isFinite(spring.value)).toBe(true);
    expect(Math.abs(spring.value)).toBeLessThan(2);
  });

  it("is stable when already at rest on target", () => {
    const spring: Spring = { value: 1, velocity: 0 };
    stepSpring(spring, 1, 1 / 60);
    expect(spring.value).toBeCloseTo(1, 6);
    expect(spring.velocity).toBeCloseTo(0, 6);
  });
});

describe("applyFriction", () => {
  it("decays velocity toward zero", () => {
    expect(Math.abs(applyFriction(1, 1 / 60))).toBeLessThan(1);
  });

  it("snaps to exactly zero below the threshold, so no frame is scheduled forever", () => {
    expect(applyFriction(0.0005, 1 / 60)).toBe(0);
  });

  it("decays by the same factor per unit time at any frame rate", () => {
    let atHigh = 1;
    for (let i = 0; i < 120; i += 1) atHigh = applyFriction(atHigh, 1 / 120);

    let atLow = 1;
    for (let i = 0; i < 30; i += 1) atLow = applyFriction(atLow, 1 / 30);

    expect(atHigh).toBeCloseTo(atLow, 3);
  });

  it("preserves direction", () => {
    expect(applyFriction(-1, 1 / 60)).toBeLessThan(0);
  });
});
