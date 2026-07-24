import { useEffect, useRef } from "react";
import Lenis from "lenis";
import { gsap } from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { derive } from "./timeline";

/**
 * The flagship scroll experience — Slice 3 (revision 2).
 *
 * NO renderer. Two public-domain NASA clips are the setting; scroll scrubs their playheads
 * (the product-launch gesture). This revision addresses owner feedback:
 *   1. Spacecraft footage for the middle beats — SDO Beauty Pass cross-fades in after the Sun.
 *   2. Text comfort — a lower-third scrim + softened, warmer type instead of pure white on gold.
 *   3. Richer scroll animation — beats drift and de-blur in; videos cross-fade; a real
 *      collapse into the measured state.
 *   4. The number no longer "appears from nowhere" — a dark MEASURED STAGE forms first, with
 *      a baseline axis, giving the value a backdrop and a home.
 *
 * Honesty: every frame of footage carries the P8 watermark. Both clips are illustrative
 * NASA imagery, not Aditya-L1; the measured number is real SoLEXS archive data.
 */

const SUN = { mp4: "/video/sun-aia171.mp4", poster: "/video/sun-aia171-poster.jpg" };
const CRAFT = { mp4: "/video/spacecraft-sdo.mp4", poster: "/video/spacecraft-sdo-poster.jpg" };

interface Beat {
  readonly from: number;
  readonly to: number;
  readonly kicker: string;
  readonly line: string;
}

/**
 * Seven beats in three acts. The middle-to-end build is the fix for "not enough story to
 * establish the number": the visitor now learns the specific event, what SoLEXS actually
 * did, and only then sees the value — earned, not dropped in. Acts 3's beats play over the
 * forming measured stage, so the footage recedes exactly as the number emerges (the crossing).
 */
const BEATS: readonly Beat[] = [
  // Act 1 — the Sun (SDO AIA 171 footage)
  { from: 0.02, to: 0.13, kicker: "THE UNIVERSE", line: "Every measurement begins as light." },
  { from: 0.16, to: 0.27, kicker: "THE SOURCE", line: "The Sun in ultraviolet — Solar Dynamics Observatory, 171 ångström." },
  // Act 2 — the Observer (SDO Beauty Pass footage)
  { from: 0.33, to: 0.44, kicker: "THE OBSERVER", line: "To measure a star, you must send something to watch it." },
  { from: 0.47, to: 0.58, kicker: "THE INSTRUMENT", line: "Aboard Aditya-L1, SoLEXS reads the Sun's soft X-rays." },
  // Act 3 — the Measurement (footage recedes into the measured stage)
  { from: 0.62, to: 0.72, kicker: "THE EVENT", line: "On 14 May 2024, the Sun released an X8.7 flare — among its most violent in years." },
  { from: 0.74, to: 0.8, kicker: "THE COUNT", line: "SoLEXS counted the X-rays that reached it — one value, every minute." },
  { from: 0.82, to: 0.87, kicker: "THE CROSSING", line: "Light becomes a number." },
];

const clamp01 = (x: number): number => (x < 0 ? 0 : x > 1 ? 1 : x);
const smooth = (x: number): number => {
  const c = clamp01(x);
  return c * c * (3 - 2 * c);
};
/** Rising ramp a→b, eased. */
const inRamp = (t: number, a: number, b: number): number => smooth(clamp01((t - a) / (b - a)));
/** Falling ramp a→b, eased (1 before a, 0 after b). */
const outRamp = (t: number, a: number, b: number): number => 1 - inRamp(t, a, b);

interface BeatState {
  readonly opacity: number;
  readonly ty: number;
  readonly blur: number;
}
/** A beat rises into place (drift + de-blur), holds, then drifts up and out. */
function beatState(t: number, from: number, to: number): BeatState {
  const edge = Math.min(0.06, (to - from) * 0.4);
  const enter = smooth(clamp01((t - from) / edge));
  const exit = smooth(clamp01((to - t) / edge));
  const vis = Math.min(enter, exit);
  return {
    opacity: vis,
    ty: (1 - enter) * 22 - (1 - exit) * 22,
    blur: (1 - vis) * 6,
  };
}

export default function V2Experience() {
  const root = useRef<HTMLDivElement>(null);
  const sunVideo = useRef<HTMLVideoElement>(null);
  const craftVideo = useRef<HTMLVideoElement>(null);
  const sunWrap = useRef<HTMLDivElement>(null);
  const craftWrap = useRef<HTMLDivElement>(null);
  const stage = useRef<HTMLDivElement>(null);
  const eventEcho = useRef<HTMLDivElement>(null);
  const beatRefs = useRef<(HTMLDivElement | null)[]>([]);
  const numberWrap = useRef<HTMLDivElement>(null);
  const watermark = useRef<HTMLDivElement>(null);
  const progressBar = useRef<HTMLDivElement>(null);
  const scrollHint = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const prefersReduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    gsap.registerPlugin(ScrollTrigger);

    let lenis: Lenis | null = null;
    const onRaf = (time: number): void => {
      lenis?.raf(time * 1000);
    };
    if (!prefersReduced) {
      lenis = new Lenis({ duration: 1.15, smoothWheel: true });
      lenis.on("scroll", ScrollTrigger.update);
      gsap.ticker.add(onRaf);
      gsap.ticker.lagSmoothing(0);
    }

    const readyFlags = new WeakMap<HTMLVideoElement, boolean>();
    const prep = (v: HTMLVideoElement | null): void => {
      if (!v) return;
      v.pause();
      const mark = (): void => void readyFlags.set(v, true);
      if (v.readyState >= 2) mark();
      else v.addEventListener("loadeddata", mark, { once: true });
    };
    prep(sunVideo.current);
    prep(craftVideo.current);

    // Seek a video only across its own scrub window, and only while it is visible.
    // `endFrac` caps how far into the clip the scrub reaches — used so the spacecraft
    // (dominant only in the first ~62% of its clip, then drifting out of frame) stays the
    // subject across the whole Observer act instead of exiting early.
    const scrub = (v: HTMLVideoElement | null, t: number, from: number, to: number, visible: boolean, endFrac = 1): void => {
      if (!v || prefersReduced || !visible || !readyFlags.get(v) || !Number.isFinite(v.duration)) return;
      const local = clamp01((t - from) / (to - from));
      const target = local * (v.duration * endFrac - 0.05);
      if (Math.abs(v.currentTime - target) > 0.01) v.currentTime = target;
    };

    const applyState = (t: number): void => {
      const d = derive(t);

      // --- Video cross-fade: Sun → spacecraft → measured stage ---
      // The stage now forms during Act 3 (from t≈0.60), so the flare/count/crossing beats
      // land on a settling dark field and the number arrives on a prepared backdrop.
      const sunOp = outRamp(t, 0.28, 0.34);
      const craftOp = inRamp(t, 0.28, 0.34) * outRamp(t, 0.58, 0.64);
      const stageOp = inRamp(t, 0.6, 0.7);

      if (sunWrap.current) sunWrap.current.style.opacity = String(sunOp);
      if (craftWrap.current) craftWrap.current.style.opacity = String(craftOp);
      if (stage.current) stage.current.style.opacity = String(stageOp);

      // A faint, blurred echo of the flare warms THE EVENT beat so Act 3 does not open on
      // an empty field. Same illustrative footage, heavily defocused — an afterimage of
      // what we just watched, not a second showing of it.
      if (eventEcho.current) {
        eventEcho.current.style.opacity = String(inRamp(t, 0.58, 0.64) * outRamp(t, 0.72, 0.78) * 0.24);
      }

      scrub(sunVideo.current, t, 0.0, 0.3, sunOp > 0.02);
      scrub(craftVideo.current, t, 0.32, 0.6, craftOp > 0.02, 0.62);

      // Gentle push-in on whichever clip is live — cinematic drift, not parallax noise.
      const zoom = 1.02 + t * 0.06;
      if (sunVideo.current) sunVideo.current.style.transform = `scale(${zoom})`;
      if (craftVideo.current) craftVideo.current.style.transform = `scale(${zoom})`;

      // --- Beats ---
      BEATS.forEach((b, i) => {
        const el = beatRefs.current[i];
        if (!el) return;
        const s = beatState(t, b.from, b.to);
        el.style.opacity = String(s.opacity);
        el.style.transform = `translateY(${s.ty}px)`;
        el.style.filter = s.blur > 0.05 ? `blur(${s.blur.toFixed(2)}px)` : "none";
      });

      // --- The number, resolving onto the stage ---
      if (numberWrap.current) {
        const n = smooth(clamp01((d.number - 0.05) * 1.25));
        numberWrap.current.style.opacity = String(n);
        numberWrap.current.style.transform = `translateY(${(1 - n) * 16}px)`;
      }

      // --- Watermark (contract C2: string swaps, opacity holds) ---
      if (watermark.current) {
        watermark.current.textContent = d.watermark;
        watermark.current.style.color = d.register === "measured" ? "#9fbef0" : "#aeb6bd";
        watermark.current.style.opacity = String(0.55 + d.watermarkFade * 0.35);
      }

      if (progressBar.current) progressBar.current.style.transform = `scaleX(${t})`;
      // The scroll hint is only an invitation to begin; it retires once the visitor has.
      if (scrollHint.current) scrollHint.current.style.opacity = String(outRamp(t, 0.04, 0.12));
    };

    const st = ScrollTrigger.create({
      trigger: root.current,
      start: "top top",
      end: "bottom bottom",
      scrub: prefersReduced ? false : 1,
      onUpdate: (self) => applyState(self.progress),
    });
    applyState(0);

    return () => {
      st.kill();
      if (lenis) {
        gsap.ticker.remove(onRaf);
        lenis.destroy();
      }
    };
  }, []);

  const scrim = "linear-gradient(to top, rgba(6,8,10,0.92) 0%, rgba(6,8,10,0.72) 22%, rgba(6,8,10,0.25) 48%, transparent 72%)";

  return (
    <div ref={root} style={{ position: "relative", height: "900vh", background: "#06080a" }}>
      <div style={{ position: "sticky", top: 0, height: "100vh", width: "100%", overflow: "hidden" }}>
        {/* Sun clip */}
        <div ref={sunWrap} style={{ position: "absolute", inset: 0 }}>
          <video ref={sunVideo} src={SUN.mp4} poster={SUN.poster} muted playsInline preload="auto"
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", willChange: "transform" }} />
        </div>

        {/* Spacecraft clip */}
        <div ref={craftWrap} style={{ position: "absolute", inset: 0, opacity: 0 }}>
          <video ref={craftVideo} src={CRAFT.mp4} poster={CRAFT.poster} muted playsInline preload="auto"
            style={{ position: "absolute", inset: 0, width: "100%", height: "100%", objectFit: "cover", willChange: "transform" }} />
        </div>

        {/* Measured stage — a dark, calm backdrop that forms before the number resolves, so
            the value has a home instead of appearing over nothing. */}
        <div ref={stage} style={{ position: "absolute", inset: 0, opacity: 0, pointerEvents: "none",
          background: "radial-gradient(130% 100% at 50% 42%, #0b1016 0%, #070a0d 55%, #05070a 100%)" }}>
          {/* A baseline axis — where the real light curve will live (Slice 5). */}
          <div style={{ position: "absolute", left: "12%", right: "12%", top: "62%", height: 1, background: "rgba(159,190,240,0.22)" }} />
          <div style={{ position: "absolute", left: "12%", top: "calc(62% - 5px)", width: 1, height: 10, background: "rgba(159,190,240,0.35)" }} />
          <div style={{ position: "absolute", right: "12%", top: "calc(62% - 5px)", width: 1, height: 10, background: "rgba(159,190,240,0.35)" }} />
        </div>

        {/* Flare echo — a defocused afterimage of the footage, only under THE EVENT. */}
        <div ref={eventEcho} style={{ position: "absolute", inset: 0, opacity: 0, pointerEvents: "none",
          backgroundImage: `url(${SUN.poster})`, backgroundSize: "cover", backgroundPosition: "center",
          filter: "blur(48px) saturate(0.65) brightness(0.72)", transform: "scale(1.25)" }} />

        {/* Vignette — framing only. */}
        <div style={{ position: "absolute", inset: 0, pointerEvents: "none",
          background: "radial-gradient(125% 95% at 50% 45%, transparent 42%, rgba(6,8,10,0.42) 80%, rgba(6,8,10,0.86) 100%)" }} />

        {/* Lower-third scrim — guarantees text legibility over any footage. */}
        <div style={{ position: "absolute", inset: 0, pointerEvents: "none", background: scrim }} />

        {/* Beats. */}
        {BEATS.map((b, i) => (
          <div key={b.kicker} ref={(el) => { beatRefs.current[i] = el; }}
            style={{ position: "absolute", left: "clamp(24px, 8vw, 120px)", bottom: "16%", maxWidth: "min(680px, 82vw)", opacity: 0, pointerEvents: "none", willChange: "transform, opacity, filter" }}>
            <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.32em", color: "#93a7c9", marginBottom: 16 }}>
              {b.kicker}
            </div>
            <div style={{ fontFamily: "var(--font-sans)", fontSize: "clamp(23px, 3.1vw, 40px)", fontWeight: 300, lineHeight: 1.28, color: "#dfe3e7", letterSpacing: "-0.005em", textShadow: "0 2px 30px rgba(0,0,0,0.55)" }}>
              {b.line}
            </div>
          </div>
        ))}

        {/* The number. */}
        <div ref={numberWrap} style={{ position: "absolute", inset: 0, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center", opacity: 0, pointerEvents: "none", willChange: "transform, opacity" }}>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 11, letterSpacing: "0.3em", color: "#93a7c9", marginBottom: 22 }}>
            MEASURED
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontVariantNumeric: "tabular-nums", fontSize: "clamp(56px, 11vw, 150px)", fontWeight: 500, color: "#eef1f3", letterSpacing: "-0.02em", lineHeight: 1 }}>
            112.98
          </div>
          <div style={{ fontFamily: "var(--font-mono)", fontSize: 12, letterSpacing: "0.16em", color: "#6b747c", marginTop: 20 }}>
            counts · SoLEXS · 2024-05-14 · first observed minute
          </div>
          {/* Gives the value scale: it is the first of a full day the archive holds. */}
          <div style={{ fontFamily: "var(--font-sans)", fontSize: 14, fontWeight: 300, color: "#8a929a", marginTop: 30, letterSpacing: "0.01em" }}>
            The first of 1,440 minutes recorded that day.
          </div>
        </div>

        {/* Watermark — always present (P8). */}
        <div ref={watermark} style={{ position: "absolute", left: "clamp(24px, 8vw, 120px)", bottom: 26, fontFamily: "var(--font-mono)", fontSize: 10.5, letterSpacing: "0.16em", color: "#aeb6bd", opacity: 0.55 }}>
          ILLUSTRATIVE · SDO / NASA · NOT ADITYA-L1 DATA
        </div>

        {/* Scroll hint. */}
        <div ref={scrollHint} style={{ position: "absolute", right: "clamp(24px, 8vw, 120px)", bottom: 26, fontFamily: "var(--font-mono)", fontSize: 10.5, letterSpacing: "0.24em", color: "#6b747c" }}>
          SCROLL
        </div>

        {/* Progress line. */}
        <div style={{ position: "absolute", left: 0, right: 0, bottom: 0, height: 2, background: "rgba(255,255,255,0.06)" }}>
          <div ref={progressBar} style={{ height: "100%", background: "#7f9dd6", transform: "scaleX(0)", transformOrigin: "left" }} />
        </div>
      </div>
    </div>
  );
}
