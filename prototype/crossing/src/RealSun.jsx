import { useMemo, useRef } from "react";
import { useFrame, useLoader } from "@react-three/fiber";
import * as THREE from "three";

/**
 * Real SDO/NASA solar imagery as the artistic register.
 *
 * P8 EXCEPTION (owner-approved): this is genuine imagery from NASA's Solar Dynamics
 * Observatory — a DIFFERENT mission with imaging instruments. Aditya-L1's SoLEXS records
 * no image at all. It is used here as ILLUSTRATIVE context, never as Aditya-L1 data, and
 * the frame watermark says so. That attribution is the entire difference between an
 * honest use of another mission's imagery (a documentary crediting stock footage) and a
 * dishonest one (passing it off as ours). See docs P8-EXCEPTION note.
 *
 * Shown as a flat camera-facing disk because that is what the photograph is — a disk. It
 * still drains (desaturates), collapses to a point, and yields the measured number, so
 * the Crossing is intact. It does not rotate: a single photograph has only one face, and
 * faking rotation would be the dishonesty this whole project avoids.
 */

const TEXTURE = "/latest_1024_0171.jpg"; // SDO AIA 171 — coronal loops. Public domain, NASA.

const vertexShader = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
  }
`;

const fragmentShader = /* glsl */ `
  precision highp float;
  uniform sampler2D uMap;
  uniform float uDrain;
  uniform float uDim;
  varying vec2 vUv;
  void main() {
    // Circular mask — the sun's disk, not a square photo.
    float d = length(vUv - 0.5) * 2.0;
    float disk = smoothstep(1.0, 0.985, d);
    if (disk < 0.01) discard;

    vec3 img = texture2D(uMap, vUv).rgb;

    // Grade the gold SDO 171 toward orange (illustrative only). Luminance-preserving:
    // keep the image's brightness structure, shift the hue warmer.
    float glum = dot(img, vec3(0.299, 0.587, 0.114));
    vec3 orange = vec3(1.0, 0.40, 0.09);
    img = mix(img, glum * orange * 1.75, 0.74);

    // Drain: desaturate toward luminance and darken, so the real image visibly stops
    // claiming to be a photograph as the register changes to schematic.
    float lum = dot(img, vec3(0.2126, 0.7152, 0.0722));
    vec3 drained = mix(img, vec3(lum), uDrain * 0.9) * mix(1.0, 0.18, uDrain);

    gl_FragColor = vec4(drained * uDim, disk * mix(0.35, 1.0, uDim));
  }
`;

export function RealSun({ state }) {
  const group = useRef();
  const material = useRef();
  const map = useLoader(THREE.TextureLoader, TEXTURE);

  const uniforms = useMemo(
    () => ({ uMap: { value: map }, uDrain: { value: 0 }, uDim: { value: 1 } }),
    [map],
  );

  useFrame(() => {
    const s = state.current;
    uniforms.uDrain.value = s.sunDrain ?? 0;
    uniforms.uDim.value = s.sunDim ?? 1;
    // The Sun is the setting: it scales down as the spacecraft enters, and collapses at
    // the crossing like everything else.
    const scale = (s.sunScale ?? 1) * (1 - (s.collapse ?? 0) * 0.985);
    if (group.current) group.current.scale.setScalar(scale);
  });

  return (
    <group ref={group}>
      <mesh>
        <planeGeometry args={[2.4, 2.4]} />
        <shaderMaterial
          ref={material}
          vertexShader={vertexShader}
          fragmentShader={fragmentShader}
          uniforms={uniforms}
          transparent
        />
      </mesh>
    </group>
  );
}
