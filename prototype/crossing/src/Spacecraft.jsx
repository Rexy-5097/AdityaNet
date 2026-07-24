import { useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import * as THREE from "three";

/**
 * Aditya-L1 as a self-dissecting blueprint. Register S — schematic, not photoreal.
 *
 * Honesty: this is a symbolic engineering diagram, not a reconstruction. Geometry is
 * recognisable-not-accurate (a bus, two solar wings, a payload deck). The seven payloads
 * are the publicly-documented Aditya-L1 instrument set (ISRO / eoPortal). No internal
 * configuration is invented; SoLEXS is a labelled marker, not a modelled detector.
 *
 * Driven by the timeline: flies in (craftIn), dissects (dissect), lights the payloads in
 * sequence (payloadReveal), then all fade but SoLEXS (isolate / craftFade).
 */

// The seven payloads, in the order they light. SoLEXS last — the one the project is about.
const PAYLOADS = [
  { id: "SUIT", x: -0.55, z: 0.35 },
  { id: "VELC", x: 0.0, z: 0.55 },
  { id: "HEL1OS", x: 0.55, z: 0.35 },
  { id: "ASPEX", x: -0.55, z: -0.35 },
  { id: "PAPA", x: 0.0, z: -0.55 },
  { id: "MAG", x: 0.55, z: -0.35 },
  { id: "SoLEXS", x: 0.0, z: 0.0 },
];

const LINE = new THREE.Color(0x8fb8ff);
const HILITE = new THREE.Color(0xffd08a);

export function Spacecraft({ state, onActive }) {
  const group = useRef();
  const leftPanel = useRef();
  const rightPanel = useRef();
  const bus = useRef();
  const deck = useRef();
  const payloadRefs = useRef([]);
  const lastActive = useRef(-2); // guards the DOM caption from a per-frame setState

  const busGeo = useMemo(() => new THREE.BoxGeometry(0.7, 0.5, 0.7), []);
  const panelGeo = useMemo(() => new THREE.PlaneGeometry(1.3, 0.55, 6, 3), []);

  useFrame(() => {
    const s = state.current;
    const g = group.current;
    if (!g) return;

    // Fly-in: from small/far to placed. Scale and a gentle settle.
    const inn = s.craftIn;
    g.visible = inn > 0.001 && s.craftFade < 0.995;
    const baseScale = 0.15 + inn * 0.85;
    g.scale.setScalar(baseScale * (1 - s.craftFade * 0.4));
    g.position.set((1 - inn) * 2.4, (1 - inn) * 1.2, 0);
    g.rotation.set(-0.5 + inn * 0.15, 0.6 - inn * 0.2, 0);

    const d = s.dissect;
    // Solar wings slide out along X.
    if (leftPanel.current) leftPanel.current.position.x = -0.9 - d * 0.9;
    if (rightPanel.current) rightPanel.current.position.x = 0.9 + d * 0.9;
    // Bus drops, deck lifts — the payload deck is exposed.
    if (bus.current) bus.current.position.y = -d * 0.7;
    if (deck.current) deck.current.position.y = d * 0.6;

    // Payloads light in sequence, then all fade but SoLEXS on isolate.
    // Report the brightest payload to the DOM caption.
    let active = -1, best = 0.35;
    PAYLOADS.forEach((p, i) => {
      const mesh = payloadRefs.current[i];
      if (!mesh) return;
      const isSolexs = p.id === "SoLEXS";
      // Each payload's reveal window is a slice of payloadReveal.
      const slice = i / PAYLOADS.length;
      const lit = THREE.MathUtils.clamp((s.payloadReveal - slice) * PAYLOADS.length, 0, 1);
      const risen = d * (0.15 + i * 0.02);
      mesh.position.y = 0.32 + risen;
      if (lit > best) { best = lit; active = i; }

      // On isolate: non-SoLEXS payloads fade; SoLEXS brightens and centres.
      const keep = isSolexs ? 1 : 1 - s.isolate;
      const emphasise = isSolexs ? 1 + s.isolate * 0.8 : 1;
      mesh.scale.setScalar((0.06 + lit * 0.05) * emphasise);
      mesh.material.opacity = lit * keep;
      mesh.material.color.copy(isSolexs && s.isolate > 0.3 ? HILITE : LINE).lerp(HILITE, lit * (isSolexs ? 1 : 0.5));
    });
    const report = s.isolate > 0.4 ? 6 : active; // 6 = SoLEXS index
    if (onActive && report !== lastActive.current) {
      lastActive.current = report;
      onActive(report);
    }
  });

  return (
    <group ref={group}>
      {/* Bus — hexagon-ish box, wireframe. */}
      <mesh ref={bus} geometry={busGeo}>
        <meshBasicMaterial color={LINE} wireframe transparent opacity={0.6} depthWrite={false} />
      </mesh>

      {/* Solar wings — flat grids. */}
      <mesh ref={leftPanel} geometry={panelGeo} position={[-0.9, 0, 0]}>
        <meshBasicMaterial color={LINE} wireframe transparent opacity={0.5} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>
      <mesh ref={rightPanel} geometry={panelGeo} position={[0.9, 0, 0]}>
        <meshBasicMaterial color={LINE} wireframe transparent opacity={0.5} side={THREE.DoubleSide} depthWrite={false} />
      </mesh>

      {/* Payload deck — a thin platform that lifts to expose the payloads. */}
      <group ref={deck}>
        <mesh position={[0, 0.3, 0]}>
          <boxGeometry args={[0.75, 0.04, 0.75]} />
          <meshBasicMaterial color={LINE} wireframe transparent opacity={0.4} depthWrite={false} />
        </mesh>

        {PAYLOADS.map((p, i) => (
          <group key={p.id} position={[p.x * 0.42, 0, p.z * 0.42]}>
            <mesh ref={(m) => (payloadRefs.current[i] = m)} position={[0, 0.32, 0]}>
              <boxGeometry args={[1, 1, 1]} />
              <meshBasicMaterial color={LINE} transparent opacity={0} depthWrite={false} blending={THREE.AdditiveBlending} />
            </mesh>
          </group>
        ))}
      </group>
    </group>
  );
}
