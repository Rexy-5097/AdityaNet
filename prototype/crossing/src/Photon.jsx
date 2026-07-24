import { useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

/**
 * Schematic sensor plane and the inbound photon.
 *
 * Both belong to Register S: flat, unlit, symbolic. The plane is a wireframe grid, not a
 * rendered detector — SoLEXS's internal configuration is not publicly specified, and a
 * detailed detector here would be invention. The plane says "a sensor faces this way",
 * which is all the schematic register is entitled to claim.
 *
 * The photon travels a straight path to the plane's centre. The camera never moves, so
 * the photon's approach is the only motion in frame — the eye has one thing to watch,
 * and it is the thing that is about to become a measurement.
 */

const START = new THREE.Vector3(-3.4, 1.6, 1.2);
const TARGET = new THREE.Vector3(0, 0, 0);

export function Photon({ state }) {
  const photon = useRef();
  const trail = useRef();
  const plane = useRef();

  useFrame(() => {
    const s = state.current;
    const visible = s.photonVisible && s.collapse < 0.02;

    if (photon.current) {
      photon.current.visible = visible;
      photon.current.position.lerpVectors(START, TARGET, s.photon);
      photon.current.material.opacity = visible ? 1 : 0;
    }
    if (trail.current) {
      trail.current.visible = visible;
      // Trail stretches from start toward the photon's current position.
      const mid = new THREE.Vector3().lerpVectors(START, TARGET, s.photon * 0.5);
      trail.current.position.copy(mid);
      trail.current.scale.set(1, s.photon * START.distanceTo(TARGET) * 0.5, 1);
      trail.current.lookAt(TARGET);
      trail.current.material.opacity = visible ? 0.35 : 0;
    }
    if (plane.current) {
      // Plane fades in as the craft resolves into the SoLEXS detector, recedes into
      // the collapse. (craftFade rises through Scene 4, exactly when the sensor context
      // is what the viewer should be reading.)
      plane.current.material.opacity = Math.min(s.craftFade, 1 - s.collapse) * 0.5;
    }
  });

  return (
    <group>
      {/* Symbolic sensor plane: a wireframe grid, tilted to face the incoming photon. */}
      <mesh ref={plane} position={[0, 0, -0.05]} rotation={[0, 0, 0]}>
        <planeGeometry args={[2.6, 2.6, 8, 8]} />
        <meshBasicMaterial
          color={0x8fb8ff}
          wireframe
          transparent
          opacity={0}
          side={THREE.DoubleSide}
          depthWrite={false}
        />
      </mesh>

      {/* The photon: a warm-white glowing point. */}
      <mesh ref={photon} visible={false}>
        <sphereGeometry args={[0.055, 20, 20]} />
        <meshBasicMaterial color={0xfff2d8} transparent blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>

      {/* A thin warm streak behind it — additive, so it reads as a ray of light
          rather than the cold grey stick it was before. */}
      <mesh ref={trail} visible={false}>
        <cylinderGeometry args={[0.008, 0.008, 1, 6]} />
        <meshBasicMaterial color={0xffcf9a} transparent opacity={0} blending={THREE.AdditiveBlending} depthWrite={false} />
      </mesh>
    </group>
  );
}
