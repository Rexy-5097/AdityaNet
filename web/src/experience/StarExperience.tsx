import { useEffect, useMemo, useRef, useState } from "react";
import { Canvas } from "@react-three/fiber";
import { EffectComposer, Bloom, ToneMapping } from "@react-three/postprocessing";
import { ToneMappingMode } from "postprocessing";
import * as THREE from "three";
import { Star } from "./scene/Star";
import { Watermark } from "./scene/Watermark";
import { useOrbitInput } from "./scene/useOrbitInput";
import {
  readCapabilities,
  selectTier,
  downgrade,
  TIER_SETTINGS,
  type QualityTier,
} from "./quality/tier";
import timeline from "@/generated/data/star-timeline.json";

/**
 * The experience island. Domain A.
 *
 * Mounts over a server-rendered poster and fades in. The poster is the LCP element and
 * always remains beneath: if this island never mounts — no WebGL2, reduced motion,
 * an opt-out, or a thrown error — the page is complete without it.
 */

interface TimelineDay {
  0: string;
  1: number;
  2: number;
}

const DAYS = timeline.data.days as unknown as readonly TimelineDay[];
const PEAK_RANGE = timeline.data.range;

/**
 * Normalise a peak count rate to 0..1 on a log scale.
 *
 * Log, because the measured range spans roughly four decades (5.8 to 76,088 counts/s).
 * Linear normalisation would render every day below about 8,000 counts/s as visually
 * identical black, discarding most of the archive.
 *
 * Exported so the transform is testable and so nothing has to guess at it.
 */
export function normaliseActivity(peakRate: number): number {
  const low = Math.log10(Math.max(PEAK_RANGE.peak_min, 1e-3));
  const high = Math.log10(PEAK_RANGE.peak_max);
  const value = Math.log10(Math.max(peakRate, 1e-3));
  return Math.min(1, Math.max(0, (value - low) / (high - low)));
}

/** The day the scene opens on: the archive's most energetic, which is 2024-05-14. */
function mostEnergeticDay(): TimelineDay {
  let best = DAYS[0]!;
  for (const day of DAYS) if (day[1] > best[1]) best = day;
  return best;
}

export default function StarExperience() {
  const container = useRef<HTMLElement | null>(null);
  const orbit = useOrbitInput();
  const [tier, setTier] = useState<QualityTier | null>(null);
  const [visible, setVisible] = useState(false);
  const [running, setRunning] = useState(true);

  const day = useMemo(mostEnergeticDay, []);
  const activity = useMemo(() => normaliseActivity(day[1]), [day]);

  useEffect(() => {
    const stored = window.localStorage.getItem("adityanet:reduce-effects") === "true";
    const selected = selectTier(readCapabilities(stored));
    setTier(selected);

    // Fade in only once the renderer has had a frame to compile shaders. Appearing
    // mid-compile would show a black rectangle over the poster.
    if (selected > 0) {
      const timer = window.setTimeout(() => setVisible(true), 120);
      return () => window.clearTimeout(timer);
    }
    return undefined;
  }, []);

  /**
   * Stop rendering when off-screen or backgrounded.
   *
   * A GPU scene left running in a hidden tab is pure waste — battery on laptops,
   * thermal budget on phones. `frameloop="never"` halts the loop entirely rather than
   * throttling it, so the cost genuinely goes to zero.
   */
  useEffect(() => {
    const element = container.current;
    if (element === null) return undefined;

    // Debug escape hatch (ISSUE-023). Automated browser panes report document.hidden,
    // so the GPU pause correctly halts rendering and the static poster shows through
    // unchanged — which silently invalidated several verification cycles in Sprint 3.6.
    // `?forcerender=1` keeps the loop running so a screenshot photographs the canvas.
    const forced = new URLSearchParams(window.location.search).has("forcerender");

    let onScreen = true;
    const update = () => setRunning(forced || (onScreen && !document.hidden));

    const observer = new IntersectionObserver(
      ([entry]) => {
        onScreen = entry?.isIntersecting ?? true;
        update();
      },
      { threshold: 0 },
    );
    observer.observe(element);
    document.addEventListener("visibilitychange", update);

    return () => {
      observer.disconnect();
      document.removeEventListener("visibilitychange", update);
    };
  }, [tier, visible]);

  // Tier 0 renders nothing: the server-rendered poster underneath is the whole
  // experience, and it is a complete one.
  if (tier === null || tier === 0) return null;

  const settings = TIER_SETTINGS[tier];

  return (
    <div
      ref={(element) => {
        container.current = element;
        orbit.attach(element);
      }}
      className="absolute inset-0 transition-opacity duration-700"
      style={{ opacity: visible ? 1 : 0 }}
      // The canvas is a picture, not a control surface, for assistive technology: the
      // same information is available as text on this page and on /data. It is
      // deliberately outside the tab order so keyboard users are not trapped in a
      // drag-only widget with no keyboard equivalent until Sprint 6 adds one.
      role="img"
      aria-label={
        `Artistic rendering of a star, driven by measured Aditya-L1 archive activity ` +
        `for ${day[0]}, the most energetic day in the archive. Drag to rotate. ` +
        `This is an illustration, not an observational image.`
      }
    >
      <Canvas
        dpr={[1, settings.maxPixelRatio]}
        gl={{ antialias: tier >= 2, alpha: true, powerPreference: "high-performance" }}
        camera={{ fov: 32, position: [0, 0, 5.4], near: 0.1, far: 100 }}
        onCreated={({ gl }) => {
          // Tone mapping belongs to the composer's ToneMapping effect. Leaving ACES on
          // the renderer as well maps the image twice, which desaturates saturated
          // oranges toward cream — the exact failure this sprint set out to fix.
          gl.toneMapping = THREE.NoToneMapping;
        }}
        frameloop={running ? "always" : "never"}
      >
        <Star activity={activity} tier={tier} input={orbit.state} />

        {/*
          Selective bloom. `luminanceThreshold` is set high on purpose: only active
          regions and prominences exceed it, so bloom REVEALS where the energy is
          rather than washing the whole disc. A low threshold is what makes procedural
          stars look like a lamp behind frosted glass — it hides the granulation that
          the photosphere pass exists to produce.

          Tier 1 skips the chain entirely; on a mobile GPU the mip chain costs more
          than the effect returns.
        */}
        {tier >= 2 ? (
          <EffectComposer enableNormalPass={false}>
            <Bloom
              intensity={0.80}
              luminanceThreshold={0.95}
              luminanceSmoothing={0.22}
              mipmapBlur
              radius={0.62}
            />
            <ToneMapping mode={ToneMappingMode.ACES_FILMIC} />
          </EffectComposer>
        ) : (
          <></>
        )}

        <Watermark />
      </Canvas>
    </div>
  );
}

/** Exported for the frame-time watchdog wiring in a later sprint. */
export { downgrade };
