import { StrictMode, Suspense, useEffect, useRef, useState } from "react";
import { createRoot } from "react-dom/client";
import { Canvas } from "@react-three/fiber";
import { EffectComposer, Bloom } from "@react-three/postprocessing";
import * as THREE from "three";
import { RealSun } from "./RealSun.jsx";
import { Spacecraft } from "./Spacecraft.jsx";
import { Photon } from "./Photon.jsx";
import { Evidence } from "./Evidence.jsx";
import { derive, PHASES } from "./timeline.js";

/**
 * M1 — The Crossing. Isolated prototype.
 *
 * A single t ∈ [0,1] drives the whole sequence, controlled by a scrubber and a play
 * button (scroll orchestration is out of scope for M1). The 3D scene reads t from a ref
 * inside its frame loop — never React state — so scrubbing at 60 Hz costs no reconciles.
 * React state carries only the DOM overlay (number, curve, watermark), which changes at
 * human cadence.
 *
 * The camera is fixed. Every register transition happens to the image, never the
 * viewpoint — that stillness is what the Bible requires and what makes the crossing feel
 * inevitable rather than staged.
 */


const PAYLOAD_NAMES = ["SUIT", "VELC", "HEL1OS", "ASPEX", "PAPA", "MAG", "SoLEXS"];
const PAYLOAD_DESC = [
  "Solar Ultraviolet Imaging Telescope",
  "Visible Emission Line Coronagraph — the prime payload",
  "High Energy L1 Orbiting Spectrometer — hard X-rays",
  "Aditya Solarwind Particle Experiment",
  "Plasma Analyser Package for Aditya",
  "Magnetometer",
  "Solar Low Energy X-ray Spectrometer — this is the one AdityaNet studies",
];

const WATERMARKS = {
  artistic: "ILLUSTRATIVE · SDO / NASA · NOT ADITYA-L1 DATA",
  schematic: "SCHEMATIC · NOT TO SCALE · SDO / NASA",
  measured: "MEASURED · T1 solexs_lc_1min · 43fd0e22",
};

function Crossing() {
  // The authoritative animation clock. 3D reads .current; DOM reads mirrored state.
  const state = useRef(derive(0));
  const [t, setT] = useState(0);
  const [playing, setPlaying] = useState(false);
  // Which payload is currently lit during the dissection (-1 = none). Reported up from
  // the Spacecraft's frame loop; drives the DOM caption.
  const [activePayload, setActivePayload] = useState(-1);

  // Auto-play once on load. The prototype's whole point is the motion; a viewer should
  // never have to hunt for a Play button to see what the Crossing is.
  useEffect(() => {
    const id = setTimeout(() => setPlaying(true), 900);
    return () => clearTimeout(id);
  }, []);
  const [overlay, setOverlay] = useState({ number: 0, curve: 0, watermark: "artistic", fade: 0, phase: "ARTISTIC" });

  // Advance t. rAF for smoothness; the 3D and the DOM both derive from the same t.
  useEffect(() => {
    let raf;
    let last = performance.now();
    const tick = (now) => {
      const dt = (now - last) / 1000;
      last = now;
      setT((prev) => {
        // ~14 s for the full pass — slow enough that the pivot cannot be missed.
        const next = playing ? Math.min(1, prev + dt / 14) : prev;
        return next;
      });
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [playing]);

  // Recompute derived state whenever t changes. Write to the ref (for 3D) and mirror the
  // DOM-relevant parts into React state.
  useEffect(() => {
    const s = derive(t);
    state.current = s;
    setOverlay({
      number: s.number,
      curve: s.curve,
      watermark: s.watermark,
      fade: s.watermarkFade,
      phase: s.phaseLabel,
    });
    if (playing && t >= 1) setPlaying(false);
  }, [t, playing]);

  const canvasFade = 1 - Math.min(1, overlay.number * 1.1);

  return (
    <>
      {/* Canvas holds Registers A and S. It fades out as the number resolves. */}
      <div style={{ position: "absolute", inset: 0, opacity: canvasFade, transition: "none" }}>
        <Canvas
          camera={{ fov: 32, position: [0, 0, 6.2], near: 0.1, far: 100 }}
          gl={{ antialias: true, alpha: false }}
          onCreated={({ gl }) => {
            gl.toneMapping = THREE.NoToneMapping;
            gl.setClearColor(0x06080a, 1);
          }}
        >
          <Suspense fallback={null}>
            <RealSun state={state} />
            <Spacecraft state={state} onActive={setActivePayload} />
          </Suspense>
          <Photon state={state} />
          <EffectComposer enableNormalPass={false}>
            <Bloom intensity={0.5} luminanceThreshold={0.9} luminanceSmoothing={0.2} mipmapBlur radius={0.6} resolutionScale={0.5} />
          </EffectComposer>
        </Canvas>
      </div>

      {/* Register B — DOM evidence. */}
      <Evidence numberProgress={overlay.number} curveProgress={overlay.curve} />

      {/* Watermark. A/S read as burned-in (they sit over the canvas); B is DOM-native. */}
      <div
        style={{
          position: "absolute",
          left: 24,
          bottom: 24,
          fontSize: 11,
          letterSpacing: "0.14em",
          color: overlay.watermark === "measured" ? "#8fb8ff" : "#a0a8af",
          opacity: 0.5 + overlay.fade * 0.4,
          transition: "color 400ms",
        }}
      >
        {WATERMARKS[overlay.watermark]}
      </div>


      {/* Payload caption — Register S. Names the lit payload and cites the public source
          the identity comes from. SoLEXS gets emphasis: it is what the project is about. */}
      {activePayload >= 0 && overlay.phase !== "MEASURED" && overlay.phase !== "LIGHT CURVE" && (
        <div style={{ position: "absolute", left: 40, top: "42%", maxWidth: 320, pointerEvents: "none" }}>
          <div style={{ fontSize: activePayload === 6 ? 40 : 26, fontWeight: 600, letterSpacing: "0.02em", color: activePayload === 6 ? "#ffd08a" : "#cfe0ff" }}>
            {PAYLOAD_NAMES[activePayload]}
          </div>
          <div style={{ marginTop: 6, fontSize: 11, lineHeight: 1.5, color: "#6b747c" }}>
            {PAYLOAD_DESC[activePayload]}
          </div>
          <div style={{ marginTop: 8, fontSize: 9, letterSpacing: "0.1em", color: "#4a5560" }}>
            SOURCE · ISRO / eoPortal — Aditya-L1 payload set
          </div>
        </div>
      )}

      {/* Prototype controls — not part of the experience, purely for validation. */}
      <div
        style={{
          position: "absolute",
          left: "50%",
          bottom: 24,
          transform: "translateX(-50%)",
          display: "flex",
          alignItems: "center",
          gap: 14,
          padding: "10px 16px",
          background: "rgba(18,21,24,0.85)",
          border: "1px solid #2a3138",
          borderRadius: 6,
          fontSize: 12,
        }}
      >
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
          min="0"
          max="1"
          step="0.001"
          value={t}
          onChange={(e) => {
            setPlaying(false);
            setT(Number(e.target.value));
          }}
          style={{ width: 280 }}
          aria-label="Scrub the crossing"
        />
        <span style={{ color: "#6b747c", width: 130, fontVariantNumeric: "tabular-nums" }}>
          {overlay.phase}
        </span>
        <span data-numeric style={{ color: "#6b747c", width: 44, textAlign: "right", fontVariantNumeric: "tabular-nums" }}>
          {t.toFixed(2)}
        </span>
      </div>

      {/* Phase legend so a reviewer can see the register structure at a glance. */}
      <div style={{ position: "absolute", right: 24, top: 24, fontSize: 10, color: "#6b747c", textAlign: "right", lineHeight: 1.8 }}>
        {PHASES.map((p) => (
          <div key={p.key} style={{ opacity: overlay.phase === p.label ? 1 : 0.4 }}>
            {p.from.toFixed(2)}–{p.to.toFixed(2)} {p.label}
          </div>
        ))}
      </div>
    </>
  );
}

// Reuse a single root across Vite HMR updates. Without this guard, a hot reload of this
// module calls createRoot() a second time on the same #root, which React rejects and which
// cascades into misleading "Invalid hook call" errors that look like a duplicate-React bug.
const container = document.getElementById("root");
const root = (container._reactRoot ??= createRoot(container));
root.render(
  <StrictMode>
    <Crossing />
  </StrictMode>,
);
