import { useMemo } from "react";
import day from "./data/lightcurve.json";

/**
 * The Measured register — DOM, not canvas.
 *
 * The medium change is itself part of the honesty transition. Registers A and S live in
 * the WebGL canvas: rendered, lit-or-flat, artistic or symbolic. Register B is HTML and
 * SVG — flat, selectable, inspectable, the same substance as the evidence pages. When the
 * canvas contracts to a point and the number resolves in DOM, the viewer crosses from
 * "something rendered for me" to "something I can select and check".
 *
 * Every value here is real: this is 2024-05-14, the X8.7 flare day, straight from the
 * archive light curve. The first resolved number is the first observed minute.
 */

const WIDTH = 900;
const HEIGHT = 220;

export function Evidence({ numberProgress, curveProgress }) {
  const firstValue = useMemo(() => {
    const v = day.rate.find((x) => x !== null);
    return v ?? 0;
  }, []);

  // Build the light-curve path once; reveal is done by clipping width, not by rebuilding.
  const path = useMemo(() => {
    const rate = day.rate;
    const finite = rate.filter((v) => v !== null && v > 0);
    const logMin = Math.log10(Math.max(Math.min(...finite), 0.1));
    const logMax = Math.log10(Math.max(...finite));
    const span = Math.max(logMax - logMin, 0.5);

    const pad = { l: 8, r: 8, t: 12, b: 12 };
    const pw = WIDTH - pad.l - pad.r;
    const ph = HEIGHT - pad.t - pad.b;
    const x = (i) => pad.l + (i / (rate.length - 1)) * pw;
    const y = (v) => pad.t + ph - ((Math.log10(Math.max(v, 0.1)) - logMin) / span) * ph;

    const segs = [];
    let cur = [];
    rate.forEach((v, i) => {
      if (v === null || v <= 0) {
        if (cur.length > 1) segs.push(cur.join(" "));
        cur = [];
        return;
      }
      cur.push(`${cur.length === 0 ? "M" : "L"}${x(i).toFixed(1)},${y(v).toFixed(1)}`);
    });
    if (cur.length > 1) segs.push(cur.join(" "));
    return segs.join(" ");
  }, []);

  const numberOpacity = Math.min(1, numberProgress * 1.4);
  const numberScale = 0.85 + Math.min(numberProgress, 1) * 0.15;

  return (
    <div
      style={{
        position: "absolute",
        inset: 0,
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        justifyContent: "center",
        pointerEvents: "none",
      }}
    >
      {/* The one number. Monospace, tabular, enormous. */}
      <div
        data-numeric
        style={{
          opacity: numberOpacity,
          transform: `scale(${numberScale})`,
          fontSize: "clamp(64px, 12vw, 160px)",
          fontWeight: 500,
          fontVariantNumeric: "tabular-nums slashed-zero",
          letterSpacing: "-0.02em",
          lineHeight: 1,
          color: "#e8ebed",
          transition: "none",
        }}
      >
        {firstValue.toFixed(2)}
      </div>

      {/* The light curve, revealed left→right by clipping. */}
      <svg
        viewBox={`0 0 ${WIDTH} ${HEIGHT}`}
        style={{
          width: "min(900px, 82vw)",
          height: "auto",
          marginTop: 18,
          opacity: Math.min(1, curveProgress * 1.6),
        }}
        role="img"
        aria-label="SoLEXS total count rate, 2024-05-14, the most energetic day in the archive."
      >
        <defs>
          <clipPath id="reveal">
            <rect x="0" y="0" width={WIDTH * curveProgress} height={HEIGHT} />
          </clipPath>
        </defs>
        <path d={path} fill="none" stroke="#e69f00" strokeWidth="1.1" clipPath="url(#reveal)" />
      </svg>

      <p
        style={{
          marginTop: 14,
          fontSize: 11,
          color: "#6b747c",
          opacity: Math.min(1, curveProgress * 2),
          letterSpacing: "0.04em",
        }}
      >
        counts/s · minute resolution · {day.observed} of {day.minutes} minutes observed
      </p>
    </div>
  );
}
