import { useMemo, useRef } from "react";
import { useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import vertexShader from "../shaders/shell.vert.glsl?raw";
import photosphereFragment from "../shaders/photosphere.frag.glsl?raw";
import atmosphereFragment from "../shaders/atmosphere.frag.glsl?raw";
import { assembleFragment } from "./shaderSource";
import { Prominences } from "./Prominences";
import { applyFriction, stepSpring, CAMERA_SPRING, type Spring } from "./spring";
import type { OrbitInput } from "./useOrbitInput";
import type { QualityTier } from "../quality/tier";

/**
 * The star. Domain A: artistic rendering, measured input.
 *
 * FOUR LAYERS, outermost last so additive blending accumulates correctly:
 *
 *   1. photosphere    opaque    granulation, active regions, limb darkening
 *   2. chromosphere   additive  thin red shell; stops the limb ending like a decal
 *   3. corona         additive  2-3 nested shells, turbulent and directional
 *   4. prominences    additive  a few magnetic loops on the limb
 *
 * Shell count scales with quality tier. Each shell is one extra draw call over a
 * sphere that covers a modest part of the viewport, so the cost is fill-rate bound
 * and degrades predictably.
 */

/** Geometry detail per tier. Surface detail lives in the shader, so this only needs
 *  enough tessellation to keep the silhouette smooth. */
const SUBDIVISIONS: Record<QualityTier, number> = { 0: 3, 1: 4, 2: 5, 3: 6 };

/** Cellular-noise scales evaluated per tier. Worley dominates fragment cost at 27
 *  hash evaluations per scale, so this is the knob that actually moves frame time. */
const GRANULATION_SCALES: Record<QualityTier, number> = { 0: 1, 1: 2, 2: 2, 3: 3 };

interface ShellSpec {
  readonly radius: number;
  readonly color: readonly [number, number, number];
  readonly intensity: number;
  readonly rimPower: number;
  readonly turbulence: number;
  readonly streaks: number;
  readonly phaseOffset: number;
}

/**
 * Chromosphere first, then corona shells outward.
 *
 * The chromosphere is deliberately tight (1.4% above the surface) and red: it is the
 * H-alpha layer, and its only job is to stop the photosphere terminating at a hard
 * edge. Corona shells step outward with falling intensity and rising streakiness, so
 * structure becomes more directional the further out you look.
 */
const SHELLS: readonly ShellSpec[] = [
  { radius: 1.028, color: [1.0, 0.26, 0.12], intensity: 3.40, rimPower: 2.8, turbulence: 9.0, streaks: 0.15, phaseOffset: 0.0 },
  { radius: 1.12, color: [1.0, 0.46, 0.20], intensity: 2.10, rimPower: 2.1, turbulence: 5.0, streaks: 0.55, phaseOffset: 1.7 },
  { radius: 1.42, color: [1.0, 0.58, 0.30], intensity: 1.15, rimPower: 1.7, turbulence: 3.2, streaks: 0.85, phaseOffset: 3.1 },
  { radius: 1.92, color: [1.0, 0.66, 0.40], intensity: 0.55, rimPower: 1.4, turbulence: 2.1, streaks: 1.0, phaseOffset: 4.6 },
];

/** How many shells each tier renders. Tier 1 keeps the chromosphere and one corona
 *  layer — losing the chromosphere entirely would restore the hard limb, which is the
 *  most damaging single artefact. */
// MEASURED (Sprint 3.8). Shell count dominates frame-pacing stability: 4 shells dropped
// 10/45 frames, 3 dropped 4/45, 2 dropped 0/42. The outermost shell covers ~3.7x the
// star's area in blended pixels for the faintest contribution in the stack, so it is the
// first thing cut. Trimming shells measured better than trimming DPR.
const SHELL_COUNT: Record<QualityTier, number> = { 0: 0, 1: 1, 2: 2, 3: 3 };

/** Radians per second of idle rotation. ~5 min per revolution. */
const IDLE_DRIFT_RAD_PER_SEC = 0.021;

interface StarProps {
  /** Normalised log peak count rate, 0..1. MEASURED — see scripts/web/derive.py. */
  activity: number;
  tier: QualityTier;
  input: OrbitInput;
}

export function Star({ activity, tier, input }: StarProps) {
  const { camera } = useThree();
  const photosphere = useRef<THREE.ShaderMaterial>(null);
  const shellMaterials = useRef<THREE.ShaderMaterial[]>([]);

  // Springs live in refs, never React state. A drag updates them every frame;
  // reconciling the tree at that rate is the most common way a WebGL React page ends
  // up feeling a frame behind the cursor.
  const azimuth = useRef<Spring>({ value: 0.6, velocity: 0 });
  const elevation = useRef<Spring>({ value: 0.22, velocity: 0 });

  const photosphereUniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uDataActivity: { value: activity },
      // Deep red lanes, gold interiors, white-hot cores. The narrow white band is what
      // signals temperature; widening it reads as a lightbulb rather than a star.
      uArtDeepColor: { value: new THREE.Color(0.26, 0.028, 0.006) },
      uArtMidColor: { value: new THREE.Color(0.94, 0.30, 0.045) },
      uArtHotColor: { value: new THREE.Color(1.0, 0.66, 0.20) },
    }),
    // Built once. Activity is written imperatively below so changing the selected day
    // never rebuilds the material, which would recompile the shader and stall a frame.
    [],
  );

  const photosphereShader = useMemo(
    () => assembleFragment(photosphereFragment, { GRANULATION_SCALES: GRANULATION_SCALES[tier] }),
    [tier],
  );
  const atmosphereShader = useMemo(() => assembleFragment(atmosphereFragment), []);

  const shells = useMemo(() => {
    const count = SHELL_COUNT[tier];
    return SHELLS.slice(0, count).map((spec) => ({
      spec,
      uniforms: {
        uTime: { value: 0 },
        uDataActivity: { value: activity },
        uArtColor: { value: new THREE.Color(...spec.color) },
        uArtIntensity: { value: spec.intensity },
        uArtRimPower: { value: spec.rimPower },
        uArtTurbulence: { value: spec.turbulence },
        uArtStreaks: { value: spec.streaks },
        uArtPhaseOffset: { value: spec.phaseOffset },
      },
    }));
  }, [tier]);

  useFrame((_, delta) => {
    const target = input.current;

    if (target.dragging) {
      azimuth.current.value += target.deltaAzimuth;
      elevation.current.value += target.deltaElevation;
      azimuth.current.velocity = target.deltaAzimuth / Math.max(delta, 1 / 240);
      elevation.current.velocity = target.deltaElevation / Math.max(delta, 1 / 240);
      target.deltaAzimuth = 0;
      target.deltaElevation = 0;
    } else {
      azimuth.current.velocity = applyFriction(azimuth.current.velocity, delta);
      elevation.current.velocity = applyFriction(elevation.current.velocity, delta);
      azimuth.current.value += azimuth.current.velocity * delta;
      elevation.current.value += elevation.current.velocity * delta;

      // Idle drift. ~5 minutes per revolution: slow enough that it never reads as
      // animation, fast enough that the eye registers the object as alive rather than
      // as a still image. Applied only at rest, so it never fights a drag or its
      // release inertia.
      if (Math.abs(azimuth.current.velocity) < 0.02) {
        azimuth.current.value += IDLE_DRIFT_RAD_PER_SEC * delta;
      }

      const limit = 1.15;
      if (Math.abs(elevation.current.value) > limit) {
        stepSpring(elevation.current, Math.sign(elevation.current.value) * limit, delta, CAMERA_SPRING);
      }
    }

    const radius = 5.4;
    const a = azimuth.current.value;
    const e = Math.max(-1.3, Math.min(1.3, elevation.current.value));

    camera.position.set(
      radius * Math.cos(e) * Math.sin(a),
      radius * Math.sin(e),
      radius * Math.cos(e) * Math.cos(a),
    );
    camera.lookAt(0, 0, 0);

    if (photosphere.current !== null) {
      photosphere.current.uniforms["uTime"]!.value += delta;
      photosphere.current.uniforms["uDataActivity"]!.value = activity;
    }
    for (const material of shellMaterials.current) {
      if (material === undefined || material === null) continue;
      material.uniforms["uTime"]!.value += delta;
      material.uniforms["uDataActivity"]!.value = activity;
    }
  });

  return (
    <group>
      <mesh>
        <icosahedronGeometry args={[1, SUBDIVISIONS[tier]]} />
        <shaderMaterial
          ref={photosphere}
          vertexShader={vertexShader}
          fragmentShader={photosphereShader}
          uniforms={photosphereUniforms}
        />
      </mesh>

      {shells.map(({ spec, uniforms }, index) => (
        <mesh key={spec.radius} scale={spec.radius}>
          <icosahedronGeometry args={[1, Math.max(3, SUBDIVISIONS[tier] - 2)]} />
          <shaderMaterial
            ref={(material) => {
              if (material !== null) shellMaterials.current[index] = material;
            }}
            vertexShader={vertexShader}
            fragmentShader={atmosphereShader}
            uniforms={uniforms}
            transparent
            // Additive so overlapping shells accumulate into brightness rather than
            // occluding one another, which is what produces the layered depth cue.
            blending={THREE.AdditiveBlending}
            // Back faces only: seeing the far wall of each shell through the near one
            // is what makes it read as a volume instead of a bubble.
            side={THREE.BackSide}
            depthWrite={false}
          />
        </mesh>
      ))}

      {/* Prominences last: drawn after the corona so they composite ON TOP of it
          rather than being buried underneath, which is why they were illegible. */}
      {tier >= 2 && <Prominences activity={activity} />}
    </group>
  );
}
