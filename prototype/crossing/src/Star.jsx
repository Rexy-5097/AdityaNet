import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";
import vert from "./shaders/star.vert.glsl?raw";
import fragBody from "./shaders/star.frag.glsl?raw";
import noise from "./shaders/noise.glsl?raw";
import shellVert from "./shaders/corona.vert.glsl?raw";
import chromoFrag from "./shaders/chromosphere.frag.glsl?raw";
import glowVert from "./shaders/glow.vert.glsl?raw";
import glowFrag from "./shaders/glow.frag.glsl?raw";
import promFrag from "./shaders/prominence.frag.glsl?raw";

const frag = `${noise}\n${fragBody}`;
const promVert = "varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }";

/**
 * The star: photosphere + smooth limb + chromosphere rim + prominences + radial glow.
 * Realism pass 3 targets the remaining "fake tells": a faceted limb (now a 96-segment
 * sphere), no prominences (now three arcs at the limb), and no chromosphere/glow (now a
 * bright rim plus a camera-facing radial halo with no boxy edge). The group still drains,
 * collapses, and rotates for the Crossing.
 */

const PROMS = [
  { theta: 0.7, phi: 0.15, scale: 0.34, seed: 0.1 },
  { theta: 3.5, phi: -0.35, scale: 0.28, seed: 0.5 },
  { theta: 5.2, phi: 0.55, scale: 0.3, seed: 0.8 },
];

export function Star({ state }) {
  const group = useRef();
  const material = useRef();
  const wire = useRef();
  const flash = useRef();

  const uniforms = useMemo(
    () => ({
      uTime: { value: 0 },
      uDrain: { value: 0 },
      uDeepColor: { value: new THREE.Color(0.34, 0.05, 0.01) },
      uMidColor: { value: new THREE.Color(1.0, 0.52, 0.12) },
      uHotColor: { value: new THREE.Color(1.0, 0.86, 0.5) },
    }),
    [],
  );
  const glowUniforms = useMemo(
    () => ({ uOpacity: { value: 1 }, uColor: { value: new THREE.Color(1.0, 0.52, 0.24) } }),
    [],
  );
  const chromoUniforms = useMemo(
    () => ({ uOpacity: { value: 1 }, uColor: { value: new THREE.Color(1.0, 0.34, 0.14) } }),
    [],
  );

  const proms = useMemo(
    () =>
      PROMS.map((a) => {
        const n = new THREE.Vector3(
          Math.cos(a.phi) * Math.sin(a.theta),
          Math.sin(a.phi),
          Math.cos(a.phi) * Math.cos(a.theta),
        ).normalize();
        const tan = new THREE.Vector3().crossVectors(n, new THREE.Vector3(0, 1, 0)).normalize();
        const bin = new THREE.Vector3().crossVectors(n, tan).normalize();
        const quat = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(tan, n, bin));
        return {
          a,
          position: n.clone().multiplyScalar(0.96),
          quaternion: quat,
          uniforms: { uTime: { value: 0 }, uOpacity: { value: 1 }, uColor: { value: new THREE.Color(0.95, 0.3, 0.14) } },
        };
      }),
    [],
  );

  useFrame((_, delta) => {
    uniforms.uTime.value += delta;
    uniforms.uDrain.value = state.current.drain;
    if (group.current && state.current.collapse < 0.02) group.current.rotation.y += delta * 0.12;
    if (wire.current) wire.current.opacity = state.current.wireframe * 0.55;

    const artistic = state.current.coronaOpacity;
    glowUniforms.uOpacity.value = artistic;
    chromoUniforms.uOpacity.value = artistic * 0.9;
    for (const p of proms) {
      p.uniforms.uTime.value += delta;
      p.uniforms.uOpacity.value = artistic;
    }

    if (group.current) group.current.scale.setScalar(1 - state.current.collapse * 0.985);
    if (flash.current) {
      flash.current.material.opacity = state.current.flash;
      flash.current.scale.setScalar(0.15 + state.current.flash * 3.2);
    }
  });

  return (
    <group ref={group}>
      <mesh>
        <sphereGeometry args={[1, 96, 96]} />
        <shaderMaterial ref={material} vertexShader={vert} fragmentShader={frag} uniforms={uniforms} />
      </mesh>

      <mesh scale={1.015}>
        <sphereGeometry args={[1, 64, 64]} />
        <shaderMaterial vertexShader={shellVert} fragmentShader={chromoFrag} uniforms={chromoUniforms} transparent side={THREE.BackSide} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>

      <mesh scale={1.004}>
        <sphereGeometry args={[1, 40, 40]} />
        <meshBasicMaterial ref={wire} color={0x8fb8ff} wireframe transparent opacity={0} depthWrite={false} />
      </mesh>

      {proms.map((p) => (
        <mesh key={p.a.seed} position={p.position} quaternion={p.quaternion} scale={p.a.scale}>
          <torusGeometry args={[1, 0.22, 8, 40, Math.PI]} />
          <shaderMaterial vertexShader={promVert} fragmentShader={promFrag} uniforms={p.uniforms} transparent blending={THREE.AdditiveBlending} depthWrite={false} side={THREE.DoubleSide} />
        </mesh>
      ))}

      <mesh scale={5.5}>
        <planeGeometry args={[1, 1]} />
        <shaderMaterial vertexShader={glowVert} fragmentShader={glowFrag} uniforms={glowUniforms} transparent blending={THREE.AdditiveBlending} depthWrite={false} depthTest={false} />
      </mesh>

      <mesh ref={flash} scale={0.15}>
        <sphereGeometry args={[1, 24, 24]} />
        <meshBasicMaterial color={0xffffff} transparent opacity={0} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>
    </group>
  );
}
