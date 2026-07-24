import { useEffect, useRef, useState } from "react";
import { Canvas, useFrame, useThree } from "@react-three/fiber";
import * as THREE from "three";
import { cameraAt } from "./camera";
import { derive, SCENES, type Derived } from "./timeline";

/**
 * PREVIZ HARNESS — dev-only. Not a product surface.
 *
 * This exists so Slices 1 and 2 (the `derive(t)` contract and the camera subsystem) can be
 * reviewed for MOTION and PACING in a browser before any real scene is built. It drives
 * PLACEHOLDER geometry — a sphere for the Sun, a wireframe box for the craft — with the
 * actual `cameraAt(t)` and `derive(t)`. What you are judging here is the choreography and
 * the timing, not the visuals.
 *
 * Because the geometry is grey placeholder blocking, this harness introduces NO product
 * visual, animation or effect, and therefore needs no Experience Script justification —
 * exactly like the leva tuning panel. It must never be linked from a product route and is
 * excluded from the production build.
 */

const PLAY_SECONDS = 14; // the real arc's intended full-pass duration

/** Applies the pure camera pose to the actual R3F camera each frame. */
function CameraRig({ tRef, reducedRef }: { tRef: React.RefObject<number>; reducedRef: React.RefObject<boolean> }) {
  const { camera } = useThree();
  useFrame(() => {
    const pose = cameraAt(tRef.current ?? 0, { reducedMotion: reducedRef.current ?? false });
    camera.position.set(pose.position.x, pose.position.y, pose.position.z);
    camera.up.set(pose.up.x, pose.up.y, pose.up.z);
    camera.lookAt(pose.target.x, pose.target.y, pose.target.z);
    if (camera instanceof THREE.PerspectiveCamera && Math.abs(camera.fov - pose.fov) > 1e-4) {
      camera.fov = pose.fov;
      camera.updateProjectionMatrix();
    }
  });
  return null;
}

/**
 * Placeholder actors. Deliberately crude: a warm sphere (Sun) that recedes, and a
 * wireframe box (craft) that fades in and nudges apart on `dissect`. Just enough parallax
 * and state change to read the pacing. NOT the real Scene — that is Slices 3–5.
 */
function Placeholders({ stateRef }: { stateRef: React.RefObject<Derived> }) {
  const sun = useRef<THREE.Mesh>(null);
  const sunMat = useRef<THREE.MeshBasicMaterial>(null);
  const craft = useRef<THREE.Group>(null);
  const leftWing = useRef<THREE.Mesh>(null);
  const rightWing = useRef<THREE.Mesh>(null);
  const photon = useRef<THREE.Mesh>(null);

  useFrame(() => {
    const s = stateRef.current ?? derive(0);

    if (sun.current && sunMat.current) {
      sun.current.visible = s.sunOpacity > 0.001;
      sunMat.current.opacity = s.sunOpacity;
    }
    if (craft.current) {
      craft.current.visible = s.craftIn > 0.001 && s.craftFade < 0.999;
      const scale = 0.2 + s.craftIn * 0.8;
      craft.current.scale.setScalar(scale);
    }
    // A minimal hint of the dissection so its pacing is legible — wings slide on X.
    if (leftWing.current) leftWing.current.position.x = -0.7 - s.dissect * 0.6;
    if (rightWing.current) rightWing.current.position.x = 0.7 + s.dissect * 0.6;
    if (photon.current) {
      photon.current.visible = s.photonVisible;
      photon.current.position.set(-2.4 + s.photon * 2.4, 1.2 - s.photon * 1.2, 0.8 - s.photon * 0.8);
    }
  });

  return (
    <group>
      {/* Sun — placeholder warm sphere at the look target. */}
      <mesh ref={sun}>
        <sphereGeometry args={[1, 32, 32]} />
        <meshBasicMaterial ref={sunMat} color={0xff8a3c} transparent opacity={1} />
      </mesh>

      {/* Craft — placeholder wireframe blocking. */}
      <group ref={craft}>
        <mesh>
          <boxGeometry args={[0.6, 0.4, 0.6]} />
          <meshBasicMaterial color={0x8fb8ff} wireframe />
        </mesh>
        <mesh ref={leftWing} position={[-0.7, 0, 0]}>
          <boxGeometry args={[0.5, 0.02, 0.35]} />
          <meshBasicMaterial color={0x8fb8ff} wireframe />
        </mesh>
        <mesh ref={rightWing} position={[0.7, 0, 0]}>
          <boxGeometry args={[0.5, 0.02, 0.35]} />
          <meshBasicMaterial color={0x8fb8ff} wireframe />
        </mesh>
      </group>

      {/* Photon — a small marker so the crossing's pacing reads. */}
      <mesh ref={photon} visible={false}>
        <sphereGeometry args={[0.06, 12, 12]} />
        <meshBasicMaterial color={0xfff2d8} />
      </mesh>

      {/* Spatial reference so camera parallax is visible. Dev aid only. */}
      <gridHelper args={[12, 12, 0x223, 0x152]} position={[0, -1.6, 0]} />
    </group>
  );
}

export default function PrevizHarness() {
  const [t, setT] = useState(0);
  const [playing, setPlaying] = useState(false);
  const [reduced, setReduced] = useState(false);
  const [readout, setReadout] = useState<Derived>(() => derive(0));

  const tRef = useRef(0);
  const reducedRef = useRef(false);
  const stateRef = useRef<Derived>(derive(0));

  // Keep refs (read by the frame loop) in sync with React state.
  useEffect(() => {
    tRef.current = t;
    stateRef.current = derive(t);
  }, [t]);
  useEffect(() => {
    reducedRef.current = reduced;
  }, [reduced]);

  // Playback. Mirror a low-frequency readout into React state for the overlay.
  useEffect(() => {
    let raf = 0;
    let last = performance.now();
    const tick = (now: number) => {
      const dt = (now - last) / 1000;
      last = now;
      setT((prev) => {
        const next = playing ? Math.min(1, prev + dt / PLAY_SECONDS) : prev;
        return next;
      });
      setReadout(derive(tRef.current));
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing]);

  useEffect(() => {
    if (playing && t >= 1) setPlaying(false);
  }, [playing, t]);

  const mono = "'IBM Plex Mono', ui-monospace, monospace";

  return (
    <div style={{ position: "fixed", inset: 0, background: "#06080a" }}>
      <Canvas
        camera={{ fov: 32, position: [0, 0, 4.2], near: 0.1, far: 100 }}
        gl={{ antialias: true }}
        onCreated={({ gl }) => gl.setClearColor(0x06080a, 1)}
      >
        <CameraRig tRef={tRef} reducedRef={reducedRef} />
        <Placeholders stateRef={stateRef} />
      </Canvas>

      {/* Readout — the live derive(t) state, so pacing can be judged against the numbers. */}
      <div style={{ position: "absolute", top: 16, left: 16, fontFamily: mono, fontSize: 12, color: "#cfe0ff", lineHeight: 1.7, pointerEvents: "none" }}>
        <div style={{ fontSize: 11, letterSpacing: "0.15em", color: "#6b747c" }}>PREVIZ · SLICES 1–2 · PLACEHOLDER GEOMETRY</div>
        <div>t &nbsp;{t.toFixed(3)}</div>
        <div>scene &nbsp;{readout.sceneLabel}</div>
        <div>register &nbsp;<span style={{ color: readout.register === "measured" ? "#8fb8ff" : readout.register === "schematic" ? "#a9c4ff" : "#ffb27a" }}>{readout.register}</span></div>
        <div>lutMix &nbsp;{readout.lutMix.toFixed(2)}</div>
        <div>effects &nbsp;{readout.effectCount}{readout.effectCount > 3 ? " ⚠ OVER CAP" : ""}</div>
        <div>bloom {readout.bloom.toFixed(2)} · grid {readout.grid.toFixed(2)} · outline {readout.outline.toFixed(2)}</div>
        <div>canvas &nbsp;{readout.canvasMounted ? "mounted" : "UNMOUNTED"}</div>
      </div>

      {/* Watermark — present exactly as the product will show it. */}
      <div style={{ position: "absolute", bottom: 16, left: 16, fontFamily: mono, fontSize: 11, letterSpacing: "0.14em", color: readout.register === "measured" ? "#8fb8ff" : "#a0a8af", opacity: 0.5 + readout.watermarkFade * 0.4 }}>
        {readout.watermark}
      </div>

      {/* Phase ruler — shows scene boundaries so pacing is legible at a glance. */}
      <div style={{ position: "absolute", top: 16, right: 16, fontFamily: mono, fontSize: 10, color: "#6b747c", textAlign: "right", lineHeight: 1.8, pointerEvents: "none" }}>
        {SCENES.map((sc) => (
          <div key={sc.key} style={{ opacity: readout.sceneLabel === sc.label ? 1 : 0.4 }}>
            {sc.from.toFixed(2)}–{sc.to.toFixed(2)} {sc.label}
          </div>
        ))}
      </div>

      {/* Controls. */}
      <div style={{ position: "absolute", bottom: 16, left: "50%", transform: "translateX(-50%)", display: "flex", alignItems: "center", gap: 14, padding: "10px 16px", background: "rgba(18,21,24,0.85)", border: "1px solid #2a3138", borderRadius: 6, fontFamily: mono, fontSize: 12 }}>
        <button
          onClick={() => {
            if (t >= 1) setT(0);
            setPlaying((p) => !p);
          }}
          style={{ background: "#e8ebed", color: "#0a0c0e", border: 0, borderRadius: 4, padding: "4px 12px", cursor: "pointer", fontWeight: 600 }}
        >
          {playing ? "Pause" : t >= 1 ? "Replay" : "Play"}
        </button>
        <input
          type="range"
          min={0}
          max={1}
          step={0.001}
          value={t}
          onChange={(e) => {
            setPlaying(false);
            setT(Number(e.target.value));
          }}
          style={{ width: 340 }}
          aria-label="Scrub the arc"
        />
        <label style={{ color: "#cfe0ff", display: "flex", alignItems: "center", gap: 6, cursor: "pointer" }}>
          <input type="checkbox" checked={reduced} onChange={(e) => setReduced(e.target.checked)} />
          reduced-motion
        </label>
      </div>
    </div>
  );
}
