import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import vertexShader from "../shaders/prominence.vert.glsl?raw";
import fragmentShader from "../shaders/prominence.frag.glsl?raw";

/**
 * Magnetic loops on the limb. Domain A.
 *
 * Four, not forty. Prominences are the element most likely to tip from "rewarding
 * observation" into "demanding attention", and the brief is explicit that they should
 * be noticed on the second look.
 *
 * GEOMETRY, NOT BILLBOARDS. Each loop is a partial torus oriented tangent to the
 * surface, so orbiting genuinely reveals its three-dimensionality — the loop passes in
 * front of and behind the disc as the camera moves. A camera-facing sprite would
 * collapse the instant the user drags, which is exactly the moment the illusion most
 * needs to hold, and reinforcing that the star is a solid body is the stated purpose
 * of keeping ORBIT.
 */

/**
 * Deterministic anchor points, chosen rather than randomised.
 *
 * Spread across latitudes and longitudes so at least one is visible from any starting
 * orientation, but none sits at the pole (where a tangent basis degenerates) or dead
 * centre (where a loop would be seen end-on and read as a smudge).
 *
 * Fixed values rather than a hash, because four positions that were art-directed for
 * silhouette are better than four that happen to fall out of a noise function.
 */
const ANCHORS: readonly { theta: number; phi: number; scale: number; seed: number }[] = [
  { theta: 0.62, phi: 0.35, scale: 0.30, seed: 0.11 },
  { theta: 2.35, phi: -0.28, scale: 0.23, seed: 0.47 },
  { theta: 4.10, phi: 0.62, scale: 0.27, seed: 0.73 },
  { theta: 5.30, phi: -0.55, scale: 0.20, seed: 0.29 },
];

interface ProminencesProps {
  activity: number;
}

export function Prominences({ activity }: ProminencesProps) {
  const materials = useRef<THREE.ShaderMaterial[]>([]);

  const loops = useMemo(
    () =>
      ANCHORS.map((anchor) => {
        // Surface point and an orthonormal basis around it.
        const normal = new THREE.Vector3(
          Math.cos(anchor.phi) * Math.sin(anchor.theta),
          Math.sin(anchor.phi),
          Math.cos(anchor.phi) * Math.cos(anchor.theta),
        ).normalize();

        // Any vector not parallel to the normal yields a stable tangent. World up is
        // safe here because no anchor sits near a pole.
        const tangent = new THREE.Vector3().crossVectors(normal, new THREE.Vector3(0, 1, 0)).normalize();
        const binormal = new THREE.Vector3().crossVectors(normal, tangent).normalize();

        // TorusGeometry arcs through +Y of its own space, with footpoints on ±X. Map
        // local Y to the surface normal so the loop arches outward, and local X to a
        // tangent so both feet rest on the surface.
        const basis = new THREE.Matrix4().makeBasis(tangent, normal, binormal);
        const quaternion = new THREE.Quaternion().setFromRotationMatrix(basis);

        // Seat the loop slightly below the surface so its footpoints are occluded by
        // the photosphere rather than floating.
        const position = normal.clone().multiplyScalar(0.94);

        return {
          anchor,
          position,
          quaternion,
          uniforms: {
            uTime: { value: 0 },
            uDataActivity: { value: activity },
            uArtColor: { value: new THREE.Color(1.0, 0.34, 0.20) },
            uArtSeed: { value: anchor.seed },
          },
        };
      }),
    [],
  );

  useFrame((_, delta) => {
    for (const material of materials.current) {
      if (material === undefined || material === null) continue;
      material.uniforms["uTime"]!.value += delta;
      material.uniforms["uDataActivity"]!.value = activity;
    }
  });

  return (
    <group>
      {loops.map((loop, index) => (
        <mesh
          key={loop.anchor.seed}
          position={loop.position}
          quaternion={loop.quaternion}
          scale={loop.anchor.scale}
        >
          {/* Half torus: ring radius 1, tube 0.24, arc PI. Low segment counts because
              the shape is soft-edged by the fragment shader, not by tessellation. */}
          <torusGeometry args={[1, 0.24, 8, 48, Math.PI]} />
          <shaderMaterial
            ref={(material) => {
              if (material !== null) materials.current[index] = material;
            }}
            vertexShader={vertexShader}
            fragmentShader={fragmentShader}
            uniforms={loop.uniforms}
            transparent
            blending={THREE.AdditiveBlending}
            depthWrite={false}
            side={THREE.DoubleSide}
          />
        </mesh>
      ))}
    </group>
  );
}
